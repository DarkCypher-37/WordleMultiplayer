import random
import enum

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