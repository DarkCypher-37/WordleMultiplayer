import queue
import threading

import NetworkCommunicator


def stash(message_string, raddr):

    remote_address = raddr
    gamekey = 0xf272b57cc9fd9580
    sender_identifier = 0xAAAAAAAAAAAAAAAA
    message_type = 'a'

    message_type = 'l' if message_string == "leave()" else 'a'

    message = (
        remote_address,
        gamekey,
        sender_identifier,
        message_type,
        message_string
    )

    return message

def queue_print(in_queue):
    while True:
        while not in_queue.empty():
            remote_address, gamekey, sender_identifier, message_type, message_string = in_queue.get()
            print(f"recieved message: {message_string}")

if __name__ == "__main__":

    # stores Tuple[remote_address: tuple, gamekey: int, sender_identifier: int, message_type: str, message_string: str]
    in_queue = queue.LifoQueue()
    
    # stores as a Tuple[remote_address: tuple, gamekey: int, sender_identifier: int, message_type: str, message_string: str]
    out_queue = queue.LifoQueue()

    print(f"enter or anything: ", end='')
    temp = input()

    if temp:
        bind_port = 55555
        to_port   = 44444
    else:
        bind_port = 44444
        to_port   = 55555


    print(f"{bind_port, to_port=}")

    nc = NetworkCommunicator.NetworkCommunicator(
        message_in_queue=in_queue,
        message_out_queue=out_queue,
        port=bind_port,
        timeout_interval=0.5
    )

    q_pr = threading.Thread(target=queue_print, args=(in_queue,))

    nc.start()
    q_pr.start()
    host = "192.168.240.1"

    raddr = (host, to_port)

    while True:
        out_queue.put(stash(input(), raddr))