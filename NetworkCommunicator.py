import socket
import select
import queue
import threading
import struct

class NetworkCommunicator(threading.Thread):

    def __init__(self, message_in_queue: queue.LifoQueue, message_out_queue: queue.LifoQueue, temp: int) -> None:
        self.message_in_queue = message_in_queue            # buffer ingoing messages
        self.message_out_queue = message_out_queue          # buffer outgoing messages

        self.timeout_interval = 0.5

        self.magic_number = 0x8b0968b3
        self.out_buffer = {}            # stores {remote_address: message, ...}

        # self.host = s.gethostbyname(s.getfqdn(s.gethostname()))
        # self.host = s.gethostbyname(s.gethostname())
        self.host = "127.0.0.1"                                             # DEBUG
        # print(f"ownport input: ", end='')
        # self.port = int(input())                                          # DEBUG

        self.port = temp

        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.main_socket.setblocking(False)

        self.main_socket.bind((self.host, self.port))
        self.main_socket.listen()

        self.inputs, self.outputs, self.exc = [self.main_socket], [], []

        super().__init__(target=self.run, args=())

    def run(self) -> None:
        
        while self.inputs:

            # create sockets for entries in 'self.message_out_queue' and add them to the 'self.out_buffer'
            while not self.message_out_queue.empty():
                remote_address, message = self.message_out_queue.get()
                if remote_address not in self.out_buffer:
                    self.out_buffer[remote_address] = [message]
                else:
                    self.out_buffer[remote_address].append(message)

                send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.main_socket.setblocking(False)

                # connect_ex should maybe get its own loop
                # handle messages which never connect()
                errno = send_socket.connect_ex(remote_address)
                if errno == 0:
                    print(f"succesfully connect_ex()ed (with {errno=!r})")
                elif errno == 10035:
                    print(f"{errno=!r}: WSAEWOULDBLOCK (ok for non-blocking sockets)")
                elif errno == 10061:
                    print(f"{errno=!r}: WSAECONNREFUSED (most likely server not listening)")
                else:
                    print(f"some weird error after trying to connect_ex(): {errno=!r}")
                
                self.outputs.append(send_socket)

            # block until either a socket is ready or until the timeout, to register new entries in the 'self.message_out_queue'
            readable_sockets, writable_sockets, exceptional_sockets = select.select(self.inputs, self.outputs, self.exc, self.timeout_interval)

            for sock in readable_sockets:
                if sock == self.main_socket:
                    # a new connection
                    connection, remote_address = sock.accept()
                    print(f"new connection from {remote_address}")
                    connection.setblocking(False)
                    # append the new connection to the inputs, to let select() put it in readable
                    self.inputs.append(connection)
                else:
                    # recv data and append to message_out_queue
                    print("recieving data ...")
                    # message = self.recv_all(sock)
                    message = sock.recv(1024)                   # DEBUG
                    if message:
                        print(f"data: {message=}")
                        self.message_in_queue.put(message)
                    else:
                        self.inputs.remove(sock)
                        sock.shutdown(socket.SHUT_RDWR)
                        sock.close()

            for sock in writable_sockets:
                # send (write) from out_buffer if raddr matches
                remote_address = sock.getpeername()
                if remote_address in self.out_buffer:
                    messages = self.out_buffer[remote_address]

                    while len(messages) > 0:
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
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()

    def recv_all(self, sock: socket.socket) -> tuple:
        # get all the data from a message
        # get the size from a package
        sock.setblocking(True)
        header = sock.recv(25)

        # should potentially timeout - ??

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

        message = sock.recv(size)
        if not message:
            return False

        sock.setblocking(False)

        return gamekey, identifier, message_type, message


class DebugInput(threading.Thread):

    def __init__(self, message_out_queue: queue.LifoQueue, temp) -> None:
        self.message_out_queue = message_out_queue          # buffer outgoing messages
        self.raddr = ('127.0.0.1', temp)
        super().__init__(target=self.get_input, args=())

    def get_input(self) -> None:
        self.message_out_queue.put((self.raddr, b"first message!"))
        print(f"start looking for input...")
        while True:
            temp = input()
            print(f"{temp=}")
            self.message_out_queue.put((self.raddr, bytes(temp, 'utf-8')))

if __name__ == "__main__":

    in_queue = queue.LifoQueue()
    out_queue = queue.LifoQueue()

    print(f"bind on port: ", end='')
    temp = int(input())

    print(f"send to port: ", end='')
    temp1 = int(input())

    nc = NetworkCommunicator(
        message_in_queue=in_queue,
        message_out_queue=out_queue,
        temp=temp)

    inp = DebugInput(out_queue, temp1)
    inp.start()

    nc.start()