#! /usr/bin/python3

import random
import enum
import arcade

class CharStatus(enum.Enum):
    undefined = -1
    correct_position = 2                # green
    word_contains = 1                   # yellow
    word_doesnt_contain = 0             # gray


class WordList:

    def __init__(self) -> None:
        """creates an WordList object, reads in "WordList.txt", a file containing ~13K 5 letter words"""
        with open("WordList.txt", 'r') as file:
            self.words = file.read().split()

    def contains(self, word:str) -> bool:
        """returns true if the word is contained in the wordlist"""
        # return True if word in self.words else False
        return word in self.words

    def get_random_word(self) -> str:
        """returns a random word from the wordlist"""
        # There is currently only the ~13K wordlist, however the solution in wordle is chosen from a list with ~2K entries 
        return random.choice(self.words)


class Game:

    def __init__(self) -> None:
        self.wordlist = WordList()
        self.players = [] # list of players
        self.start_round()

    def start_round(self):
        self.solution_word = self.wordlist.get_random_word()
        self.players.append(Player(self.solution_word))
        # self.solution_word = "thaal"                              # DEBUG
        print(f"DEBUG solution: {self.solution_word}")              # DEBUG
        self.game_loop()

    def game_loop(self):
        """temporary game loop"""
        while True:
            char = input()
            print(f"-> {char=}")
            if self.players[0].add_char(char) == [2, 2, 2, 2, 2]:
                print("player won!!!")
                break
        # for _ in range(6):
        #     match = False
        #     while not match:
        #         # wait for valid input
        #         guess = input()
        #         match = self.match(guess)
        #     if match == [2, 2, 2, 2, 2]:
        #         print("GAME WON!!!")
        #         break
        #     print(''.join([str(i.value) for i in match]))       # DEBUG
        # print("loop over")




class Player:

    def __init__(self, solution_word) -> None:
        self.wordlist = WordList()
        self.solution_word = solution_word
        self.word_table = [[None] * 5] * 6 # 5 by 6 table of the words
        self.match_table = [[None] * 5] * 6 # 5 by 6 table of the words's status
        self.current_word_index = 0
        self.current_char_index = 0

    def add_word(self, word: str):
        """add a word to the word_table of a player"""
        if self.current_word_index > 5:
            raise Exception("word list too full!")

        self.word_table[self.current_word_index] = list(word)
        self.current_word_index += 1
        self.update_match_list()

    def add_char(self, char:str):
        """add a character to the current position on the word_table"""
        if self.current_word_index > 5:
            raise Exception("word list too full!")
        if self.current_char_index > 4:
            raise Exception("char list too full!")
        print(f"{len(char)=}")
        if len(char) > 1: # may not be nessecary
            raise ValueError(f"{char!r} is too long to be a char")

        print("executed once")
        self.word_table[self.current_word_index][self.current_char_index] = char
        self.current_char_index += 1
        self.print_table()

        if self.current_char_index >= 5:
            print("reached max char_index")
            # when the end of a word is reached, reset the char index 
            self.current_char_index = 0
            self.current_word_index += 1
            return self.update_last_match()

    def update_match_list(self):
        """updates the entire match_table"""
        for index, word in enumerate(self.word_table):
            word = ''.join(map(str, word))
            match = self.match(word)
            if not match:
                raise ValueError(f"{word!r} not a valid word")
            self.match_table[index] = match
            
    def update_last_match(self):
        """updates the match_table for the last word_table entry"""
        self.print_table()
        print(f"{self.current_word_index-1}")
        word = ''.join(map(str, self.word_table[self.current_word_index-1]))
        match = self.match(word)
        if not match:
            raise ValueError(f"{word!r} is not a valid word")
        self.match_table[self.current_word_index-1] = match
        return match

    def print_table(self):
        # print("\n".join([w for w in self.word_table]))
        print('\n'.join(''.join(list(map(str, w))) for w in self.word_table).replace("None", '_'))

    def match(self, guess:str):
        """ 
        returns an array of CharStatus corresponding to the correctness of the letters in guess
        returns False if guess is not a word in the wordlist or (by extension of the previous) not 5 chars in length
        """
        result = [CharStatus.word_doesnt_contain for _ in range(5)]
        solution_copy = self.solution_word

        if not self.wordlist.contains(guess):
            print(f"{guess} is not a word in wordlist!!")                               # DEBUG
            return False

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


        print(f"solution: {self.solution_word}")                            # DEBUG
        print(f"          {''.join([str(i.value) for i in result])}")       # DEBUG
        print(f"guess:    {guess}")                                         # DEBUG

        return result

class MultiPlayer:
    # potentially ???
    pass
class BotPlayer:
    # potentially ???
    pass
class NetworkHandler:
    pass

class GUI(arcade.Window):

    pass

if __name__ == "__main__":
    game = Game()
    # game.match("tadal")