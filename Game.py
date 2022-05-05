import random
import enum
import arcade
import queue
import select
import socket
import threading
import struct

import traceback                                               # DEBUG

def debug(obj):                                                # DEBUG
    d_print("debugging ...")                                   # DEBUG
    while True:                                                # DEBUG
        try:                                                   # DEBUG
            d_print(repr(eval(input())))                       # DEBUG
        except KeyboardInterrupt:                              # DEBUG
            d_print("... debugging over")                      # DEBUG
            break                                              # DEBUG
        except:                                                # DEBUG
            traceback.print_exc()                              # DEBUG

def d_print(text):                                             # DEBUG
    # if True:                                                 # DEBUG
    if False:                                                  # DEBUG
        print(f"DEBUG: {text}")                                # DEBUG

# __all__

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
        # self.player_count = player_count
        self.players = [] # list of players
        self.start_round()

    def start_round(self):
        self.solution_word = self.wordlist.get_random_word()
        self.players.append(Player(self.solution_word))
        # self.solution_word = "thaal"                                # DEBUG
        d_print(f"DEBUG solution: {self.solution_word}")              # DEBUG
        self.game_loop()

    def game_loop(self):
        """temporary game loop"""
        while True:
            char = input()
            d_print(f"-> {char=}")            # DEBUG
            if self.players[0].add_char(char) == [2, 2, 2, 2, 2]:
                print("player won!!!")
                break


class Player:

    def __init__(self, solution_word) -> None:
        self.wordlist = WordList()
        self.solution_word = solution_word
        self.vaild_chars = "abcdefghijklmnopqrstuvwxyz"
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

    def add_char(self, char:str):
        """add a character to the current position on the word_table"""

        char = char.casefold()

        if self.current_word_index > 5:
            raise Exception("word list too full!")
        if self.current_char_index > 4:
            raise Exception("char list too full!")
        if len(char) > 1:
            # may not be nessecary
            raise ValueError(f"{char!r} is too long to be a char")
        if char not in self.vaild_chars:
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
    # potentially ???
    def __init__(self, solution_word) -> None:
        super().__init__(solution_word)
        self.identifier = "" # used to uniquely identify the player
        self.username = ""
        # in queue for thread safe handling/storing the recieved chars 
        self.InQueue = queue.Queue()
        # in queue for thread safe handling/storing the to be sent chars 
        self.outQueue = queue.Queue()

    def add_char(self, char: str):
        # return super().add_char(char)
        pass


class BotPlayer(Player):
    # potentially ???
    def __init__(self, solution_word) -> None:
        super().__init__(solution_word)


class NetworkHandler:
    """
    potentially two threads?

    """

    def __init__(self, client_player, players) -> None:
        self.client_player = client_player
        self.players = players
        # create a ipv4 TCP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # maybe use AF_INET6 (ipv6)
        # bind the socket to '' (meaning INADDR_ANY, binding to all interfaces)
        # and port 0, which lets the os chose a port
        self.sock.bind(('', 0))
        print(f"{self.sock.getsockname()=}")                        # DEBUG
        # setting up a kind of queue for a socket, so if several connections are trying to communicate simultainiously, they will be handled sequentially
        self.sock.listen()
        # make the socket non-blocking, as select will be 'polling' the sockets
        self.sock.setblocking(False)
        # storing all sockets which could be recieving data from a remote
        self.inputs = [self.sock]
        # storing all sockets which could be sending data to a remote
        self.outputs = []
        self.handle()

        # DEBUG to send data
        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # maybe use AF_INET6 (ipv6)
        # self.sock.connect(('localhost', int(input())))
        # self.send_data(self.sock)        

    def handle(self):
        # iterate until inputs are empty, meaning (hopefully) the socket has been closed
        while self.inputs:
            # sockets will be added to readable if there is data to be read
            # sockets will be added to writable if data could be sent
            # if <data to be sent> :
            #     outputs.append(...)
            readable_sockets, writable_sockets, exceptional_sockets = select.select(self.inputs, self.outputs, self.inputs) # timeout: float = 
            for sock in readable_sockets:
                if sock == self.sock:
                    # if the socket is the 'base'socket, we have a new connection to accept
                    connection, remote_address = sock.accept()
                    connection.setblocking(False)
                    # appending the connection to the inputs
                    self.inputs.append(connection)
                    print(f"connection from {remote_address}")      # DEBUG
                else:
                    # recieve 1024 bytes
                    # player_id, data = self.recieve_data()
                    self.recieve_data(sock)
            
            for sock in writable_sockets:
                # check if there is data to send then send it
                self.send_data(sock)
            
            for sock in exceptional_sockets:
                # should not happen, if it does we just close the connection
                self.inputs.remove(sock)
                sock.close()

        # when this is reached the socket should be closed
        
    def send_data(self, sock):
        """
        send one message

        layout: 
            magic number |  size  |   identifier    | message type |       message
            4bytes    | 4bytes |     8bytes      |     1byte    | length given in {size}
                uInt     |  uInt  |   u Long Long   |     char     |        char[]
         -> !IIQb 

        magic number:
            always exactly: 0x8b0968b3

        message types:
            j (join):  request to join the game
            c (char):  transmits one char
            w (word):  transmits one word (5 chars)
        """
        magic_number = 0x8b0968b3
        format = "!IIQb"

        # TODO: get messages to be sent when needed

        message = "hello world"       # EXAMPLE
        identifier = 404              # EXAMPLE
        message_type = ord('j')       # EXAMPLE

        # uses ! for network byte order
        # consists of (unsigned Interger + unsigned Interger + unsigned Long Long + char
        print(f"struct: {hex(magic_number), len(message), identifier, message_type}")
        data = struct.pack(format, magic_number, len(message), identifier, message_type)
        sock.sendall(data + bytes(message, "utf_8"))
        print(data)

    def recieve_data(self, sock):
        """recieve one message and handle it accordingly"""
        # set socket to blocking, to recieve more than one time
        sock.setblocking(True)
        
        # uses ! for network byte order
        # consists of (unsigned Interger + unsigned Interger + unsigned Long Long + char
        magic_number, size, identifier, message_type = struct.unpack("!IIQb", sock.recv(4+4+8+1))
        message_type = chr(message_type)

        if magic_number != 0x8b0968b3:
            # if the magic number doesnt match it is likely that something went wrong
            self.inputs.remove(sock)
            sock.close() 

        # make sure all data in the message was recieved, as it is not guaranteed to be within one sock.recv()
        data = bytes()
        while len(data) < size:
            data += sock.recv(size)

        sock.setblocking(False)

        # TODO: handle the message
        if message_type in ('j', 'c', 'w'):
            print(hex(magic_number), size, identifier, message_type)
            print(data)
        else:
            print(f"{message_type!r} unkown message type")

        # close the socket
        self.inputs.remove(sock)
        sock.close()
        exit()


class GUI(arcade.Window):

    def __init__(self, width: int = 800, height: int = 600, 
                 title: str = 'Wordle Clone', fullscreen: bool = False, 
                 resizable: bool = False, update_rate = 1 / 60, 
                 antialiasing: bool = True):
        super().__init__(width, height, title, fullscreen, resizable, update_rate, antialiasing)

    def on_draw(self):
        return super().on_draw()

    def on_update(self, delta_time: float):
        return super().on_update(delta_time)

if __name__ == "__main__":
    # game = Game()
    # game.match("tadal")
    p = Player("tadal")
    nh = NetworkHandler(p, [p])
