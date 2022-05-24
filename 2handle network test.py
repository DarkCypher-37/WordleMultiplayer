from NetworkHandler import NetworkHandler
from Player import Player, MultiPlayer


if __name__ == "__main__":

    p1 = MultiPlayer(
        solution_word="apple",
        identifier=0,
        username="ha lol"
    )


    playerlist = [p1]


    nh = NetworkHandler(
        playerlist=playerlist,
        username=p1.username,
        localhost=True,
        debug_port=55555
    )

    # laddr ('192.168.178.23', )

    raddr = ("127.0.0.1", 44444)

    nh.join_network(10, raddr)
    while True:
        nh.check_for_recieved_messages()