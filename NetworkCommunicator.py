import queue
import socket
import select
import struct
import threading

from Errors import *

# TODO: test if port already in use
# TODO: make IP version agnostic

from color import *

class NetworkCommunicator(threading.Thread):
    """A class that handles the actual network stuff
    
    Attributes:
        no public attributes, queues should be the only way of communication between the threads

    """

    def __init__(self, message_in_queue: queue.LifoQueue, message_out_queue: queue.LifoQueue, port: int = 0, timeout_interval: float = 0.5, localhost: bool = False) -> None:
        """ Initialize a NetworkCommunicator
        
        Args:
            message_in_queue               (queue.LifoQueue) : a queue for thread safe queueing recieved messages to be handled
            message_out_queue              (queue.LifoQueue) : a queue for thread safe queueing messages to be sent
            port                           (int)             : port on which the NetworkCommunicator will bind itself onto
            timeout            (optional)  (float)           : an optional parameter to specify the timeout for the select()
            localhost          (optional)  (bool)            : if True the localhost will be used, for debugging purposes

        """

        super().__init__(target=self.run, args=())

        # buffer ingoing messages
        # stores Tuple[remote_address: tuple, gamekey: int, sender_identifier: int, message_type: str, byte_message: bytes]
        self.message_in_queue = message_in_queue
        # buffer outgoing messages
        # stores Tuple[remote_address: tuple, gamekey: int, sender_identifier: int, message_type: str, message_string: str]
        self.message_out_queue = message_out_queue
        self.port = port
        self.timeout_interval = timeout_interval

        self.should_close = False
        self.magic_number = 0x8b0968b3
        self.out_buffer = {}            # stores {remote_address: message, ...}

        self.host = socket.gethostbyname(socket.gethostname())
        # self.host = ""
        if localhost:
            self.host = "127.0.0.1"

        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.main_socket.setblocking(False)

        self.main_socket.bind((self.host, self.port))

        # set the port variable to the port assigned py the operating system
        self.port = self.main_socket.getsockname()[1]

        self.main_socket.listen()

        self.inputs, self.outputs, self.exc = [self.main_socket], [], []

        self.ALL_SOCKETS = [str(self.main_socket)]

    @property
    def get_port(self) -> int:
        """a getter for the port"""
        # not properly done since this is still just a wrapper around self.port
        return self.port

    @property
    def get_host(self) -> str:
        """a getter for the port"""
        return self.host

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

            for remote_address in list(self.out_buffer.keys()):
                errno = send_socket.connect_ex(remote_address)
                cprint(C, f"connecting to port: {remote_address[1]}") # DEBUG
                if errno == 0:
                    # print(f"succesfully connect_ex()ed (with {errno=!r})")
                    pass
                elif errno == 10035:
                    # [WinErr 10035]: WSAEWOULDBLOCK
                    # print(f"{errno=!r}: WSAEWOULDBLOCK (ok for non-blocking sockets)")
                    pass
                elif errno == 10054:
                    # [WinErr 10054]: WSAECONNRESET
                    self.error_message(f"[WinErr 10054]: WSAECONNRESET, connection reset by peer (remote): {remote_address}")
                    del self.out_buffer[remote_address]
                elif errno == 10061:
                    # [WinErr 10061]: WSAECONNREFUSED
                    self.error_message(f"[WinErr 10061]: WSAECONNREFUSED target activly refused connction (most likely not a port on which this programm is listening): {remote_address}")
                    del self.out_buffer[remote_address]
                else:
                    # catch remaining errors
                    raise ConnectExError(errno=errno)
                
                self.outputs.append(send_socket)
                self.ALL_SOCKETS.append(str(send_socket))

            # block until either a socket is ready or until the timeout, to register new entries in the 'self.message_out_queue'
            readable_sockets, writable_sockets, exceptional_sockets = select.select(self.inputs, self.outputs, self.exc, self.timeout_interval)

            # print([s for s in self.inputs])

            # print(f"len(inputs): {red}{len(self.inputs)}{reset} len(readable_sockets): {red}{len(readable_sockets)}{reset} writable_sockets: {red}{len(writable_sockets)}{reset}")
            # print(f"len(inputs): {red}{len(self.inputs)}{reset} len(readable_sockets): {red}{len(readable_sockets)}{reset} writable_sockets: {red}{len(writable_sockets)}{reset}")

            # cprint(G, "\n   ".join([f"sockname {i.getsockname(), i.getpeername()}" for i in self.inputs[1:]]))
            # cprint(R, "\n   ".join([f"sockname {i.getsockname(), i.getpeername()}" for i in self.outputs]))

            # cprint(M, "\n".join([str(s) for s in self.ALL_SOCKETS]))

            # handle all readable sockets
            sock: socket.socket
            for sock in readable_sockets:
                if sock == self.main_socket:
                    # accepting a new connection
                    connection, remote_address = sock.accept()
                    connection.setblocking(False)
                    # append the new connection to the inputs, to let select() put it in readable
                    self.inputs.append(connection)
                    self.ALL_SOCKETS.append(str(connection))
                else:
                    # recv data and append to message_out_queue
                    try:
                        message_data = self.recv_all(sock)
                        # print(f"hey I just put something into the in_queue")
                        self.message_in_queue.put(message_data)

                        # print(sock)    # DEBUG??? 
                        # sock.close()    # DEBUG??? 

                    except (ConnectionClosedError, MagicNumberMisMatchError, MessageTooBigError) as e:
                        cprint(R, f"ERROR: {e}")        # DEBUG
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
                    while len(byte_messages):
                        sock.sendall(byte_messages.pop(0))

                    # delete the messages list if it is empty
                    if len(byte_messages) == 0:
                        del self.out_buffer[remote_address]
                        sock.close()

                    # remove the socket, so that it won't be used again for select()
                    self.outputs.remove(sock)

            sock: socket.socket
            for sock in exceptional_sockets:
                cprint(G, "EXCEPTIONAL SOCKET CLOSED !!")       # DEBUG
                # should not happen, if it does we just close the connection
                if sock in self.inputs:
                    self.inputs.remove(sock)
                else:
                    self.outputs.remove(sock)
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()

            # closes the main socket if neccessary
            if self.should_close:
                self.close()
                return

    def error_message(self, reason:str) -> None:
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

        message = remote_address, gamekey, sender_identifier, ord(message_type), bytes(message_string, 'utf-8')

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

        cprint(G, f"recieved a message: {chr(message_type)}")

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

    def pack_message(self, remote_address: tuple, gamekey: int, sender_identifier: int, message_type: str, message_string: str) -> tuple:
        """packs the message to a bytes() object

        # TODO remove remote_address from args and returns

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

        if message_type == 'l':
            self.should_close = True

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
            ord(message_type)
        )

        byte_message = header + bytes(message_string, 'utf-8')

        return remote_address, byte_message

    def client_close(self):
        self.should_close = True
    
    def close(self) -> None:
        """closes the socket and ends the thread (by emptying self.inputs)

        """

        while len(self.inputs):
            self.inputs.pop(-1).close()

        # sys.exit()
        # thread.exit()
        # thread._Thread_stop()

        cprint(Y, f"the NetworkCommunicator is shutting down, {len(self.inputs)} sockets still waiting!") # DEBUG