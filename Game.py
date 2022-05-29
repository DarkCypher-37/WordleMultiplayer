from datetime import datetime
from Errors import AlreadyWonError, OutOfWordTableBounds
from NetworkHandler import NetworkHandler
from WordList import WordList, CharStatus
from Player import Player, MultiPlayer

from color import *

class SingleplayerGame:
    pass

class MultiplayerGame:

    def __init__(self) -> None:
        self.wordlist = WordList()

        # TODO create the client player

        self.player = MultiPlayer(
            solution_word=None, # TODO sync solution word between players
            username="teest uSername"
        )

        self.player_list: list[MultiPlayer] = [self.player] # list of players # TODO add client player to this list

        self.network_handler = NetworkHandler(
            playerlist=self.player_list,
            localhost=True
        )

    def create_network(self):
        solution_word = self.wordlist.get_random_word()
        gkey = 500
        self.network_handler.create_network(gkey, solution_word)

    def join_network(self):
        gkey = 500
        port = int(input("raddr_port: "))
        self.network_handler.join_network(gkey, remote_address=('127.0.0.1', port))


    def close(self) -> None:
        self.network_handler.close()

    def update(self):
        self.network_handler.check_for_recieved_messages()

    def add_char(self, char):
        if self.player.current_word_index >= self.player.max_word_guesses:
            raise OutOfWordTableBounds("word list too full!")
        elif self.player.current_char_index >= self.player.chars_in_a_word:
            raise OutOfWordTableBounds("char list too full!")
        elif self.player.won:
            raise AlreadyWonError("the player has already won")
        # elif self.player.endtime is not None: # already covered by OutOfWordTableBounds
        #     raise AlreadyLostError(f"the player already used up all guesses")
        
        self.network_handler.send_to_all(self.network_handler.send_message_char_add, char)
        match = self.player.add_char(char)
        if match == [CharStatus.correct_position]*5:
            self.player.won = True
            self.player.endtime = datetime.now().timestamp()
            # TODO the client player has won, there should probably happen more

    def remove_char(self):
        if self.player.current_char_index < 1:
            raise OutOfWordTableBounds("char list too empty!")
        if self.player.won:
            raise AlreadyWonError("the player has already won")

        char = self.player.word_table[self.player.current_word_index][self.player.current_char_index-1]

        self.player.remove_char(char)

        self.network_handler.send_to_all(self.network_handler.send_message_char_remove, char)