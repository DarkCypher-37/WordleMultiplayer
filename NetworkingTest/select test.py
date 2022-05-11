import socket
import select
import queue
import threading
import time

# the quick brown fox jumped over the lazy dog

class Player:
    def __init__(self, identifier, raddr) -> None:
        self.identifier = identifier
        self.raddr = raddr

class Net(threading.Thread):

    def __init__(self, target = None, args = None) -> None:
        self.timeout_interval = 0.1
        super().__init__(target=self.send, args=args)

    def send(self, message_queue: queue.Queue, players) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)

        self.identifier = players[0].identifier

        bind_port = players[0].raddr[1]
        to_port = players[1].raddr[1]

        print(f"{bind_port=}, {to_port=}")

        self.players = {}
        for p in players:
            self.players[p.identifier] = p

        self.socket.bind(('', bind_port))
        self.socket.listen()

        input, output, exc = [self.socket], [], []

        while input:

            to_be_sent = {}

            while not message_queue.empty():
                identifier, message = message_queue.get()
                print(f"message {message!r} will be sent shortly ...")
                if self.players[identifier].raddr not in to_be_sent:
                    to_be_sent[self.players[identifier].raddr] = []
                to_be_sent[self.players[identifier].raddr].append(message)

                send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                send_socket.setblocking(False)
                
                host = socket.gethostbyname(socket.gethostname())
                errno = send_socket.connect_ex((host, to_port))
                if errno == 0:
                    print(f"succesfully connect_ex()ed (with {errno=!r})")
                if errno == 10035:
                    # print(f"{errno=!r} WSAEWOULDBLOCK (ok for non-blocking sockets)")
                    pass
                else:
                    print(f"some weird error after trying to connect_ex(): {errno=!r}")

                output.append(send_socket)

            readable, writable, exc = select.select(input, output, input, self.timeout_interval)

            for sock in readable:
                if sock == self.socket:
                    connection, addr = sock.accept()
                    print(f"accepted connection from {addr}")
                    connection.setblocking(False)
                    input.append(connection)
                    # break # this may cause some connections to be discarded ?? not neces. because it appends to input not readable
                else:
                    print(f"reading data from socket ...")
                    data = sock.recv(1024) # may not get all the data
                    if data:
                        print(f"recieved: {data}")
                    else:
                        # TODO  test out whether socket can be closed from remote
                        input.remove(sock)
                        sock.close()

            for sock in writable:
                raddr = sock.getpeername()
                if raddr in to_be_sent:
                    messages = to_be_sent[raddr]
                    sock.sendall(bytes(messages.pop(0), 'utf-8'))

                    if len(messages) == 0:
                        del to_be_sent[raddr]

                    output.remove(sock)
                

class Input(threading.Thread):

    def __init__(self, target = None, args = None) -> None:
        super().__init__(target=self.get_input, args=args)

    def get_input(self, message_queue, identifier) -> None:
        message_queue.put((identifier, "first message!"))
        while True:
            message_queue.put((identifier, input()))
            

if __name__ == "__main__":
    message_queue = queue.Queue()

    print("identifier: ", end='')
    identifier = input()

    # print("start y/n: ", end='')
    # if input() != "y":
    #     print("value error")
    #     exit()

    # print("bind on port: ", end='')
    # try:
    #     bind_port = int(input())
    # except ValueError:
    #     print("value error")
    #     exit()

    # print("connect to port: ", end='')
    # try:
    #     to_port = int(input())
    # except ValueError:
    #     print("value error")
    #     exit()

    if identifier == "1":
        bind_port = 11111
        to_port = 22222
    elif identifier == "2":
        bind_port = 22222
        to_port = 11111

        # time.sleep(1)

    p1 = Player(identifier=identifier, raddr=('gibberish', bind_port))
    
    host = socket.gethostbyname(socket.gethostname())
    p2 = Player(identifier="404", raddr=(host, to_port))

    players = [p1, p2]

    n = Net(args=(message_queue, players))
    i = Input(args=(message_queue, "404"))


    n.start()
    i.start()