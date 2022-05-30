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
        gamekey = self.network_handler.gen_random_bytes(8)
        gamekey = 500
        self.network_handler.create_network(gamekey, solution_word)

    def join_network(self, remote_address: tuple[str, int], gamekey: int):
        self.network_handler.join_network(
            gamekey=gamekey,
            remote_address=remote_address
        )

    def ready(self):
        self.player.is_ready = True
        self.network_handler.send_to_all(
            send_message_function = self.network_handler.send_message_ready_player
        )

    def unready(self):
        self.player.is_ready = False
        self.network_handler.send_to_all(
            send_message_function = self.network_handler.send_message_unready_player
        )

    def close(self) -> None:
        self.network_handler.close()

    def update(self):
        self.network_handler.check_for_recieved_messages()

    def add_char(self, char):
        # self.network_handler.game_has_started
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
            return True

    def remove_char(self):
        if self.player.current_char_index < 1:
            raise OutOfWordTableBounds("char list too empty!")
        if self.player.won:
            raise AlreadyWonError("the player has already won")

        char = self.player.word_table[self.player.current_word_index][self.player.current_char_index-1]

        self.player.remove_char(char)

        self.network_handler.send_to_all(self.network_handler.send_message_char_remove, char)