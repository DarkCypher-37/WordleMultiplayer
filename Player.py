from WordList import WordList, CharStatus
from Errors import *

from color import *


class Player:

    def __init__(self, solution_word) -> None:
        self.wordlist = WordList()
        self.solution_word = solution_word
        self.valid_chars = "abcdefghijklmnopqrstuvwxyz"
        self.max_word_guesses = 6
        self.chars_in_a_word = 5
        self.won = False
        self.word_table = [[None for _ in range(self.chars_in_a_word)] for _ in range(self.max_word_guesses)] # 5 by 6 table of the words
        self.match_table = [[CharStatus.undefined for _ in range(self.chars_in_a_word)] for _ in range(self.max_word_guesses)] # 5 by 6 table of the words's status
        self.current_word_index = 0
        self.current_char_index = 0

    def add_word(self, word: str):
        """add a word to the word_table of a player"""

        if self.current_char_index != 0:
            raise KeyError(f"can't use add_word when there is already a character in the current word: {self.word_table[self.current_word_index]}")

        if self.current_word_index >= self.max_word_guesses:
            # at this point the game is 'over', the player has lost
            raise KeyError("word list too full!")

        # add word to word_table
        self.word_table[self.current_word_index] = list(word)
        match = self.update_current_match()
        if not match:
            # word not in wordlist
            cprint(B, f"{word!r} is not a word in the list")  # DEBUG
            self.empty_current_word()
            return False
        self.current_word_index += 1
        return match

    def add_char(self, char: str):
        """
        add a character to the current position on the word_table
        checks if a 'row' is completed
        ! checking whether all guesses are used up must be done where this function is called 
        """

        char = char.casefold()

        if self.current_word_index >= self.max_word_guesses:
            raise KeyError("word list too full!")
        if self.current_char_index >= self.chars_in_a_word:
            raise KeyError("char list too full!")
        if len(char) > 1:
            raise CharTooLongError(f"too long to be a char: {char!r}")
        if char not in self.valid_chars:
            # check for letter through a .. z
            raise ValueError(f"char not part of the english alphabet: {char}")

        # add the char to the word_table
        self.word_table[self.current_word_index][self.current_char_index] = char
        self.current_char_index += 1

        if self.current_char_index == self.chars_in_a_word:
            # when the end of a word is reached, check for a word match
            match = self.update_current_match()
            if not match:
                # the word is not in the wordlist or not vaild
                self.empty_current_word()
                return False
            # if the match was succesful reset the char index 
            self.current_char_index = 0
            self.current_word_index += 1
            return match

    def remove_char(self, char: str) -> None:
        """remove the last character to be put in the word_table"""

        if self.current_char_index == 0:
            raise KeyError("decrementing the current_char_index would cause an out of bound error, cannot remove char")
        
        self.current_char_index -= 1 
        
        if self.word_table[self.current_word_index][self.current_char_index] != char:
            raise ValueError("the transmitted char to be removed was not identical with the one saved by the client, cannot remove char")
        
        self.word_table[self.current_word_index][self.current_char_index] = None

    def empty_current_word(self):
        """reset the current word from the word_table"""
        self.word_table[self.current_word_index] = [None for _ in range(5)]
        self.current_char_index = 0

    def update_match_list(self):
        """updates the entire match_table"""
        for index, word in enumerate(self.word_table):
            word = ''.join(map(str, word))
            match = self.match(word)
            if not match:
                raise ValueError(f"{word!r} not a valid word")
            self.match_table[index] = match

    def update_current_match(self):
        """updates the match_table for the last word_table entry"""
        # gets the last word from the word_table as  a string
        word = ''.join(map(str, self.word_table[self.current_word_index]))
        match = self.match(word)
        if not match:
            cprint(B, f"{word!r} is not a valid word")  # DEBUG
            return False
        self.match_table[self.current_word_index] = match
        return match

    def print_table(self):
        """prints out the word_table, for debug purposes"""
        print('\n'.join('|'.join(list(map(str, word))) for word in self.word_table).replace("None", '_'))

    def __str__(self):
        """returns the table as a string"""
        return '\n'.join('|'.join(list(map(str, word))) for word in self.word_table).replace("None", '_')

    def match(self, guess:str):
        """ 
        returns an array of CharStatus corresponding to the correctness of the letters in guess
        returns False if guess is not a word in the wordlist or (by extension of the previous) not 5 chars in length
        """

        if not self.wordlist.contains(guess):
            cprint(B, f"{guess} is not a word in wordlist!!")                               # DEBUG
            return False

        result = [CharStatus.word_doesnt_contain for _ in range(5)]
        solution_copy = self.solution_word

        # first filter out all letters with correct position
        for index, char in enumerate(guess):
            if solution_copy[index] == char:
                # solution_copy[index] = '_' doesn't work but this does essentially the same:
                solution_copy = solution_copy[:index] + '_' + solution_copy[index+1:]
                # add to the result
                result[index] = CharStatus.correct_position
        
        
        # then filter out remaining occouring characters, prioritising from the left
        for index, char in enumerate(guess):
            if char in solution_copy:
                # replace the first character matching char with an underscore
                solution_copy = solution_copy.replace(char, '_', 1)
                # add to the result
                result[index] = CharStatus.word_contains

        return result

class MultiPlayer(Player):
    
    def __init__(self, solution_word, username:str, identifier: int = 0, raddr = None) -> None:
        super().__init__(solution_word)
        
        self.is_ready = False
        self.starttime = None
        self.endtime = None

        self.username = username
        self.identifier = identifier              # used to uniquely identify the player
        self.remote_address: tuple[str, int] = raddr       # tuple(IP_address, Port) # TODO set the remote address during join process
    

    def add_char(self, char: str):
        return super().add_char(char)


class BotPlayer(Player):
    # potentially ???
    def __init__(self, solution_word) -> None:
        super().__init__(solution_word)