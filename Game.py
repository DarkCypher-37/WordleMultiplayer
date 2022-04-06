#! /usr/bin/python3

import os
import random 
import enum
import re

class CharStatus(enum.Enum):
    undefined = -1
    correct_position = 2                # green
    word_contains = 1                   # yellow
    word_doesnt_contain = 0             # gray

# print(f"{os.getcwd()=}")

class WordList:
    def __init__(self) -> None:
        with open("WordList.txt", 'r') as file:
            self.words = file.read().split()

    def contains(self, word):
        return True if word in self.words else False

    def get_random_word(self) -> str:
        return random.choice(self.words)

# wordlist = WordList()
# for word in wordlist.words:
#     if len(re.findall('e', word)) >= 3:
#         print(word)


class Game:
    def __init__(self) -> None:
        self.wordlist = WordList()
        self.start_round()

    def start_round(self):
        # self.solution_word = self.wordlist.get_random_word()
        self.solution_word = "thaal"
        print(f"DEBUG solution: {self.solution_word}")
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



        print(f"solution: {self.solution_word}")
        print(f"          {''.join([str(i.value) for i in result])}")
        print(f"guess:    {guess}")

        return result


    def match_old(self, guess):
        # if not self.wordlist_contains(word) : return False # not sure if needed

        # loop over each char to check position and containment of the char

        result = []
        solution_copy = self.solution_word

        for index, char in enumerate(guess):
            # check for containing character in the copy of the solution word, to handle duplicate characters
            if char in solution_copy:
                # check for correct position
                if self.solution_word[index] == char:
                    result.append(CharStatus.correct_position)
                else:
                    result.append(CharStatus.word_contains)
                # replace the current char with an underscore to replace the used character
                print(f"not repl: {solution_copy}")
                solution_copy = solution_copy.replace(char, '_', 1)
                print(f"    repl: {solution_copy}")

            else:
                result.append(CharStatus.word_doesnt_contain)

            # print(''.join([str(i.value) for i in result]))
            # print(solution_copy)
        print()
        return result

        # print(f"solution: {self.solution_word}")
        # print(f"          {''.join([str(i.value) for i in result])}")
        # print(f"guess:    {guess}")


game = Game()
# game.match("tadal")