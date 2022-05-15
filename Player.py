import queue


class Player:

    def __init__(self, solution_word) -> None:
        self.wordlist = WordList()
        self.solution_word = solution_word
        self.valid_chars = "abcdefghijklmnopqrstuvwxyz"
        self.word_table = [[None for _ in range(5)] for _ in range(6)] # 5 by 6 table of the words
        self.match_table = [[None for _ in range(5)] for _ in range(6)] # 5 by 6 table of the words's status
        self.current_word_index = 0
        self.current_char_index = 0

    def add_word(self, word: str):
        """add a word to the word_table of a player"""
        if self.current_word_index > 5:
            raise Exception("word list too full!")

        # add word to word_table
        self.word_table[self.current_word_index] = list(word)
        self.current_word_index += 1
        self.update_match_list()

    def add_char(self, char: str):
        """add a character to the current position on the word_table"""

        char = char.casefold()

        if self.current_word_index > 5:
            raise Exception("word list too full!")
        if self.current_char_index > 4:
            raise Exception("char list too full!")
        if len(char) > 1:
            # may not be nessecary
            raise ValueError(f"too long to be a char: {char!r}")
        if char not in self.valid_chars:
            # check for letter through a .. z
            # maybe should raise ValueError ?
            d_print(f"{char} not in the alphabet!")       # DEBUG
            return False

        # add the char to the word_table
        self.word_table[self.current_word_index][self.current_char_index] = char
        self.current_char_index += 1
        self.print_table() # DEBUG

        if self.current_char_index >= 5:
            d_print("reached max char_index")         # DEBUG
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
            d_print(f"{word!r} is not a valid word")  # DEBUG
            return False
        self.match_table[self.current_word_index] = match
        return match

    def print_table(self):
        """prints out the word_table, for debug purposes"""
        print('\n'.join(''.join(list(map(str, word))) for word in self.word_table).replace("None", '_'))

    def match(self, guess:str):
        """ 
        returns an array of CharStatus corresponding to the correctness of the letters in guess
        returns False if guess is not a word in the wordlist or (by extension of the previous) not 5 chars in length
        """
        result = [CharStatus.word_doesnt_contain for _ in range(5)]
        solution_copy = self.solution_word

        if not self.wordlist.contains(guess):
            d_print(f"{guess} is not a word in wordlist!!")                               # DEBUG
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


        d_print(f"solution: {self.solution_word}")                            # DEBUG
        d_print(f"          {''.join([str(i.value) for i in result])}")       # DEBUG
        d_print(f"guess:    {guess}")                                         # DEBUG

        return result

class MultiPlayer(Player):
    
    def __init__(self, solution_word, identifier, username:str) -> None:
        # TODO:
        # add unicode-timestamp self.starttime
        self.is_ready = False
        self.starttime = None


        super().__init__(solution_word)
        self.username = username
        self.identifier = 0              # used to uniquely identify the player
        self.remote_address = None       # tuple(IP_address, Port) # TODO set the remote address during join process
        self.add_queue = queue.Queue()     # in queue for thread safe handling/storing the recieved newly added chars       # prob. unnessecary
        self.remove_queue = queue.Queue()     # in queue for thread safe handling/storing the recieved newly removed chars  # prob. unnessecary

    def add_char(self, char: str):
        # return super().add_char(char)
        pass


class BotPlayer(Player):
    # potentially ???
    def __init__(self, solution_word) -> None:
        super().__init__(solution_word)