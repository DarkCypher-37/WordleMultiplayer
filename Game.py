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

    def contains(self, word):
        return True if word in self.words else False

    def get_random_word(self) -> str:
        return random.choice(self.words)

class Game:
    def __init__(self) -> None:
        self.wordlist = WordList()
        self.start_round()

    def start_round(self):
        # self.solution_word = self.wordlist.get_random_word()
        self.solution_word = "thaal" # DEBUG
        print(f"DEBUG solution: {self.solution_word}") # DEBUG
        self.game_loop()

    def game_loop(self):
        for i in range(5):
            guess = input()
            match = self.match(guess)
            if match == [2, 2, 2, 2, 2]:
                print("GAME WON!!!")
                break
            print(''.join([str(i.value) for i in match]))
        print("loop over")

    def match(self, guess):
        result = [CharStatus.word_doesnt_contain for _ in range(5)]
        solution_copy = self.solution_word

        if not self.wordlist.contains(guess):
            return -1

        # first filter out all letters with correct position
        for index, char in enumerate(guess):
            if solution_copy[index] == char:
                solution_copy = solution_copy[:index] + '_' + solution_copy[index+1:]
                # solution_copy[index] = '_'
                result[index] = CharStatus.correct_position
        
        
        # then filter out remaining occouring characters, prioritising from the left
        for index, char in enumerate(guess):
            if char in solution_copy:
                result[index] = CharStatus.word_contains
                solution_copy = solution_copy.replace(char, '_', 1)


        print(f"solution: {self.solution_word}")                            # DEBUG
        print(f"          {''.join([str(i.value) for i in result])}")       # DEBUG
        print(f"guess:    {guess}")                                         # DEBUG

        return result


game = Game()
# game.match("tadal")