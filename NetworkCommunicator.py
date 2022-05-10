import queue
import socket
import select
import struct
import threading

# TODO: test if port already in use
# TODO: close socket if client wants to leave 

class NetworkError(Exception):
    pass

class ConnectionClosedError(NetworkError):
    def __str__(self) -> str:
        return "Remote has closed the connection"

class MagicNumberMisMatchError(NetworkError):
    def __str__(self) -> str:
        return "magic number doesnt match"

class MessageTooBigError(NetworkError):
    def __str__(self) -> str:
        return "message_string part of a message was larger than 2**12 = 4096 bytes"

class ConnectExError(NetworkError):
    def __init__(self, errno) -> None:
        self.errno = errno

    def __str__(self) -> str:
        return f"during a conect_ex() attempt an error occured (errno: {self.errno})"


class NetworkCommunicator(threading.Thread):
    """A class that handles the actual network stuff
    
    Attributes:
        no public attributes, queues should be the only way of communication between the threads

    """

    def __init__(self, message_in_queue: queue.LifoQueue, message_out_queue: queue.LifoQueue, port: int, timeout_interval: float = 0.5, localhost: bool = False) -> None:
        """ Initialize a NetworkCommunicator
        
        Args:
            message_in_queue               (queue.LifoQueue) : a queue for thread safe queueing recieved messages to be handled
            message_out_queue              (queue.LifoQueue) : a queue for thread safe queueing messages to be sent
            port                           (int)             : port on which the NetworkCommunicator will bind itself onto
            timeout            (optional)  (float)           : an optional parameter to specify the timeout for the select()
            localhost          (optional)  (bool)            : if True the localhost will be used, for debugging purposes

        """
        # buffer ingoing messages
        # stores Tuple[remote_address: tuple, gamekey: int, sender_identifier: int, message_type: str, message_string: str]
        self.message_in_queue = message_in_queue
        # buffer outgoing messages
        # stores Tuple[remote_address: tuple, gamekey: int, sender_identifier: int, message_type: str, message_string: str]
        self.message_out_queue = message_out_queue
        self.port = port
        self.timeout_interval = timeout_interval

        self.magic_number = 0x8b0968b3
        self.out_buffer = {}            # stores {remote_address: message, ...}

        self.host = socket.gethostbyname(socket.gethostname())
        if localhost:
            self.host = "127.0.0.1"

        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.main_socket.setblocking(False)

        self.main_socket.bind((self.host, self.port))

        self.main_socket.listen()

        self.inputs, self.outputs, self.exc = [self.main_socket], [], []

        super().__init__(target=self.run, args=())

    def run(self) -> None:
        """'mainloop' of the thread, constantly polling for new entries to the message_out_queue and blocking using select for incoming messages 
        
        """
        
        while self.inputs:

            # create sockets for entries in 'self.message_out_queue' and add them to the 'self.out_buffer'
            while not self.message_out_queue.empty():
                # pack the unzipped tuple to a byte_message
                remote_address, byte_message = self.pack_message(*self.message_out_queue.get())
                if remote_address not in self.out_buffer:
                    self.out_buffer[remote_address] = [byte_message]
                else:
                    self.out_buffer[remote_address].append(byte_message)

                send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.main_socket.setblocking(False)

            for remote_address in self.out_buffer.keys():
                errno = send_socket.connect_ex(remote_address)
                if errno == 0:
                    # print(f"succesfully connect_ex()ed (with {errno=!r})")
                    pass
                elif errno == 10035:
                    # [WinErr 10035]: WSAEWOULDBLOCK
                    # print(f"{errno=!r}: WSAEWOULDBLOCK (ok for non-blocking sockets)")
                    pass
                elif errno == 10054:
                    # [WinErr 10054]: WSAECONNRESET
                    self.error_message("[WinErr 10054]: WSAECONNRESET, connection reset by peer (remote)")
                elif errno == 10061:
                    # [WinErr 10061]: WSAECONNREFUSED
                    self.error_message("[WinErr 10061]: WSAECONNREFUSED target activly refused connction (most likely not a port on which this programm is listening)")
                else:
                    raise ConnectExError(errno=errno)
                
                self.outputs.append(send_socket)

            # block until either a socket is ready or until the timeout, to register new entries in the 'self.message_out_queue'
            readable_sockets, writable_sockets, exceptional_sockets = select.select(self.inputs, self.outputs, self.exc, self.timeout_interval)

            # handle all readable sockets
            sock: socket.socket
            for sock in readable_sockets:
                if sock == self.main_socket:
                    # accepting a new connection
                    connection, remote_address = sock.accept()
                    connection.setblocking(False)
                    # append the new connection to the inputs, to let select() put it in readable
                    self.inputs.append(connection)
                else:
                    # recv data and append to message_out_queue
                    try:
                        message_data = self.recv_all(sock)
                        self.message_in_queue.put(message_data)

                    except (ConnectionClosedError, MagicNumberMisMatchError, MessageTooBigError):
                        self.inputs.remove(sock)
                        sock.shutdown(socket.SHUT_RDWR)
                        sock.close()

            # handle all writable sockets
            sock: socket.socket
            for sock in writable_sockets:
                # send (write) from out_buffer if raddr matches
                remote_address = sock.getpeername()
                if remote_address in self.out_buffer:
                    byte_messages = self.out_buffer[remote_address]

                    # send all the messages in the messages list
                    while len(byte_messages) > 0:
                        sock.sendall(byte_messages.pop(0))

                    # delete the messages list if it is empty
                    if len(byte_messages) == 0:
                        del self.out_buffer[remote_address]

                    # remove the socket, so that it won't be used again for select()
                    self.outputs.remove(sock)

            sock: socket.socket
            for sock in exceptional_sockets:
                # should not happen, if it does we just close the connection
                if sock in self.inputs:
                    self.inputs.remove(sock)
                else:
                    self.outputs.remove(sock)
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()

    def error_message(self, reason:str):
        """puts an error message 'e' on the message_in_queue to notify the other thread of an error

        an example for a usecase might be a refused connection by the remote

        Args:
            reason (string) : the reason for the errror

        """

        remote_address = None
        gamekey = None
        sender_identifier = None
        message_type = 'e'
        message_string = reason

        message = remote_address, gamekey, sender_identifier, message_type, message_string

        self.message_in_queue.put(message)

    def recv_all(self, sock: socket.socket) -> tuple:
        """recieves one message

        Args:
            sock (socket.socket) : the socket from which to send
        
        Returns:
            remote_address    (tuple)  : a tuple of (Ip address, port)
            gamekey           (int)    : 8byte number used as a 'password'-like thing for networks
            sender_identifier (int)    : 8byte number, unique for each player
            message_type      (string) : a single character to indicate the message type
            byte_message      (bytes)  : utf-8 encoded bytes for a variable-length string-part of the message

        Raises:
            ConnectionClosedError       : connection closed by remote
            MagicNumberMisMatchError    : mismatch of the recieved magic number 
            MessageTooBigError          : too large message_string in the recieved message
            
        """

        # set the socket to be blocking, so that multiple recv() can be executed
        sock.setblocking(True)
        byte_header = sock.recv(25)

        # TODO: should potentially timeout - ??

        if not byte_header:
            # connection has been closed by remote
            raise ConnectionClosedError

        format = "!IIQQb"
        remote_address = sock.getpeername()

        # convert byte_header from bytes to usable format
        magic_number, size, gamekey, sender_identifier, message_type = struct.unpack(format, byte_header)

        if magic_number != self.magic_number:
            raise MagicNumberMisMatchError(f"magic number doesnt match: {magic_number} != {self.magic_number}")

        if size > 2**12:
            raise MessageTooBigError(f"package too big: {size} bytes > 4096 bytes")

        byte_message = sock.recv(size)
        if not byte_message:
            # connection has likely been closed by remote
            raise ConnectionClosedError

        sock.setblocking(False)

        return remote_address, gamekey, sender_identifier, message_type, byte_message

    def pack_message(self, remote_address: tuple, gamekey: int, sender_identifier: int, message_type: str, message_string: str):
        """packs the message to a bytes() object

        Args:
            remote_address     (tuple)  : a tuple of (Ip address, port)
            gamekey            (int)    : 8byte number used as a 'password'-like thing for networks
            sender_identifier  (int)    : 8byte number, unique for each player
            message_type       (string) : a single character to indicate the message type
            message_string     (string) : a string for a variable-length part of the message
        
        Returns:
            remote_address     (tuple)  : a tuple of (Ip address, port)
            byte_message       (bytes)  : a bytes() object of the entire message ready to be sent

        Raises:
            ValueError: too long message_string
            
        """

        # TODO: capture 'l' (leave) messages and handle them appropiatly

        size = len(message_string)

        if size > 2**12:
            raise ValueError(f"message_string too long: {size} > {2**12}")

        format = "!IIQQb"# network-byteorder, 4bytes, 4bytes, 8bytes, 8bytes, 1byte -> 25 bytes in total

        # magic number | size | gamekey | sender_identifier | message type | message_string
        header = struct.pack(
            format, 
            self.magic_number,
            size,
            gamekey,
            sender_identifier,
            message_type
        )

        byte_message = header + bytes(message_string, 'utf-8')

        return remote_address, byte_message