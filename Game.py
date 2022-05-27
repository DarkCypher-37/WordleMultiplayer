from NetworkHandler import NetworkHandler
from WordList import WordList, CharStatus
from Player import Player, MultiPlayer

class SingleplayerGame:
    pass

class MultiplayerGame:

    def __init__(self) -> None:
        self.wordlist = WordList()

        # TODO create the client player

        self.player = MultiPlayer(
            solution_word="teest", # TODO sync solution word between players
            username="teest uSername"
        )

        self.player_list: list[MultiPlayer] = [self.player] # list of players # TODO add client player to this list

        self.network_handler = NetworkHandler(
            playerlist=self.player_list,
            localhost=True
        )

        i = input(f"create or join (c/j): ")

        if i == 'c':
            self.network_handler.create_network(500)
        elif i == 'j':
            # gkey = int(input("gamekey: "))
            gkey = 500
            port = int(input("raddr_port: "))
            self.network_handler.join_network(gkey, remote_address=('127.0.0.1', port))

        # while len(self.network_handler.identifier_to_player_dict) == 1:
        #     self.network_handler.check_for_recieved_messages()

        self.solution_word = self.wordlist.get_random_word()
        # self.solution_word = "thaal"                                # DEBUG
        print(f"DEBUG solution: {self.solution_word}")              # DEBUG

    def game_loop(self):
        """temporary game loop"""
        # TODO: check for new messages
        # TODO: check for wins of client and others
        while True:
            user_input = input()
            print(f"-> {user_input=}")            # DEBUG
            # self.network_handler.send_message_word(word=user_input)
            self.network_handler.send_to_all(self.network_handler.send_message_word, user_input)

            if self.player_list[0].add_word(user_input) == [CharStatus.correct_position]*5:
            # if self.player_list[0].add_char(char) == [CharStatus.correct_position]*5:
                print("player won!!!")
                break
            self.player_list[0].print_table()
            if self.player_list[0].current_word_index == self.player_list[0].max_word_guesses:
                print("no more guesses!! you lost")
                break

    def update(self):
        self.network_handler.check_for_recieved_messages()

    def add_char(self, char):
        self.network_handler.send_to_all(self.network_handler.send_message_char_add, char)
        self.player.add_char(char)