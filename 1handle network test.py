from NetworkHandler import NetworkHandler
from Player import Player, MultiPlayer


if __name__ == "__main__":

    print(f"port: ", end='')
    port = int(input())
    print(f"dest port: ", end='')
    dest_port = int(input())
    print(f"username: ", end='')
    username = input()

    p1 = MultiPlayer(
        solution_word="apple",
        identifier=0,
        username=username
    )

    playerlist = [p1]

    nh = NetworkHandler(
        playerlist=playerlist,
        username=p1.username,
        localhost=True,
        debug_port=port
    )

    raddr = ("127.0.0.1", dest_port)

    nh.join_network(10, raddr)
    while True:
        nh.check_for_recieved_messages()