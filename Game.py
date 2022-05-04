#! /usr/bin/python3

import random, enum

class CharStatus(enum.Enum):
    undefined = -1
    correct_position = 2                # green
    word_contains = 1                   # yellow
    word_doesnt_contain = 0             # gray

class WordList:
    def __init__(self) -> None:
        with open("WordList.txt", 'r') as file:
            self.words = file.read().split()

    def contains(self, word:str) -> bool:
        # return True if word in self.words else False
        return word in self.words

    def get_random_word(self) -> str:
        return random.choice(self.words)

class Game:
    def __init__(self) -> None:
        self.wordlist = WordList()
        self.start_round()

    def start_round(self):
        self.solution_word = self.wordlist.get_random_word()
        # self.solution_word = "thaal"                            # DEBUG
        print(f"DEBUG solution: {self.solution_word}")          # DEBUG
        self.game_loop()

    def game_loop(self):
        """ temporary game loop """
        for _ in range(6):
            match = False
            while not match:
                guess = input()
                match = self.match(guess)
            if match == [2, 2, 2, 2, 2]:
                print("GAME WON!!!")
                break
            print(''.join([str(i.value) for i in match]))       # DEBUG
        print("loop over")

    def match(self, guess:str):
        """ 
        returns an array of CharStatus corresponding to the correctness of the letters in guess
        returns False if guess is not a word in the wordlist or (by extension of the previous) not 5 chars in length
        """
        result = [CharStatus.word_doesnt_contain for _ in range(5)]
        solution_copy = self.solution_word

        if not self.wordlist.contains(guess):
            print("not a word!!")                               # DEBUG
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


if __name__ == "__main__":
    game = Game()
    # game.match("tadal")