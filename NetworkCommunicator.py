import socket
import select
import queue
import threading
import struct

# FIXME ALL !!!

class NetworkCommunicator(threading.Thread):

    def __init__(self, message_in_queue: queue.LifoQueue, message_out_queue: queue.LifoQueue) -> None:
        self.message_in_queue = message_in_queue            # buffer ingoing messages
        self.message_out_queue = message_out_queue          # buffer outgoing messages

        self.timeout_interval = 0.5

        self.magic_number = 0x8b0968b3
        self.out_buffer = {}            # stores {remote_address: message, ...}

        # self.host = s.gethostbyname(s.getfqdn(s.gethostname()))
        # self.host = s.gethostbyname(s.gethostname())
        self.host = "localhost"                                             # DEBUG
        self.port = int(input())                                            # DEBUG

        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.main_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.main_socket.setblocking(False)

        self.main_socket.bind((self.host, self.port))
        self.main_socket.listen()

        self.inputs, self.outputs, self.exc = [self.main_socket], [], []

        super().__init__(target=self.run, args=())

    def run(self) -> None:

        print("aaa")
        
        while self.inputs:

            # create sockets for entries in 'self.message_out_queue' and add them to the 'self.out_buffer'
            while not self.message_out_queue.empty():
                remote_address, message = self.message_out_queue.get()
                if remote_address not in self.out_buffer:
                    self.out_buffer[remote_address] = [message]
                else:
                    self.out_buffer[remote_address].append(message)

                send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.main_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
                self.main_socket.setblocking(False)

                errno = send_socket.connect_ex(remote_address)
                if errno == 0:
                    print(f"succesfully connect_ex()ed (with {errno=!r})")
                if errno == 10035:
                    print(f"{errno=!r} WSAEWOULDBLOCK (ok for non-blocking sockets)")
                    pass
                else:
                    print(f"some weird error after trying to connect_ex(): {errno=!r}")
                
                self.outputs.append(send_socket)

            # block until either a socket is ready or until the timeout, to register new entries in the 'self.message_out_queue'
            # might raise Exception upon timeout                # DEBUG
            print("select ...")
            readable_sockets, writable_sockets, exceptional_sockets = select.select(self.inputs, self.outputs, self.exc, self.timeout_interval)

            for sock in readable_sockets:
                if sock == self.main_socket:
                    # a new connection
                    connection, remote_address = sock.accept()
                    print(f"new connection from {remote_address}")
                    connection.setblocking(False)
                    self.inputs.append(connection)
                else:
                    # recv data and append to message_out_queue
                    print("recieving data ...")
                    # message = self.recv_all(sock)
                    message = sock.recv(1024)
                    if message:
                        print(f"data: {message=}")
                        self.message_out_queue.put(message)
                    else:
                        self.inputs.remove(sock)
                        sock.close()

            for sock in writable_sockets:
                # write from out_buffer if raddr matches
                # if raddr in out_buffer: 
                #    ...
                remote_address = sock.getpeername()
                if remote_address in self.out_buffer:
                    messages = self.out_buffer[remote_address]

                    sock.sendall(messages.pop(0))

                    if len(messages) == 0:
                        del self.out_buffer[remote_address]

                    self.outputs.remove(sock)

            for sock in exceptional_sockets:
                # should not happen, if it does we just close the connection
                if sock in self.inputs:
                    self.inputs.remove(sock)
                else:
                    self.outputs.remove(sock)
                sock.close()

    def recv_all(self, sock) -> tuple:
        # get all the data from a message
        # get the size from a package
        sock.setblocking(False)
        header = sock.recv(25)

        # should potentially timeout - ??
        # could be used to 
        # buffer = sock.recv(1024)
        # header = buffer[:25]

        if not header:
            # connection has been closed by remote
            return False

        format = "!IIQQb"

        # convert header from bytes to usable format
        magic_number, size, gamekey, identifier, message_type = struct.unpack(format, header)

        if magic_number != self.magic_number:
            print(f"magic number doesnt match: {magic_number} != {self.magic_number}")
            return False

        if size > 2**12:
            print(f"package too big: {size} bytes > 4096 bytes")
            return False
        
        total_bytes_recieved = 0
        message = bytes()

        # get all the data
        # FIXME: reads into next packet
        #        could be fixed by calculating diffrence between 'total_bytes_recieved' and 'size'
        while total_bytes_recieved < size:
            data = sock.recv(1024)
                
            if not data:
                # connection most likely closed
                return False

            message += data

        self.main_socket.setblocking(False)

        return gamekey, identifier, message_type, message

if __name__ == "__main__":

    in_queue = queue.LifoQueue()
    out_queue = queue.LifoQueue()

    # out_queue.put((('localhost', 55555), b"hello world!!"))         # DEBUG

    nc = NetworkCommunicator(
        message_in_queue=in_queue,
        message_out_queue=out_queue)
        
    nc2 = NetworkCommunicator(
        message_in_queue=in_queue,
        message_out_queue=out_queue)

    nc.start()
    nc2.start()