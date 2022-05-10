import random
import enum
import arcade
import queue
import select
import socket
import threading
import struct

# FIXME check if identifier always refers to the correct identifier
# in a message the SENDER IDENTIFIER is sent
# FIXME fix terminology for everything message-related

def d_print(text):                                             # DEBUG
    # if False:                                                # DEBUG
    if True:                                                   # DEBUG
        print(f"DEBUG: {text}")                                # DEBUG

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
        # TODO: check for new players in the player queue
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
    
    def __init__(self, solution_word, identifier, username) -> None:
        super().__init__(solution_word)
        self.username = username
        self.identifier = 0              # used to uniquely identify the player
        self.remote_address = None       # tuple(IP_address, Port) # TODO set the remote address during join process
        self.add_queue = queue.Queue()     # in queue for thread safe handling/storing the recieved newly added chars 
        self.remove_queue = queue.Queue()     # in queue for thread safe handling/storing the recieved newly removed chars 

    def add_char(self, char: str):
        # return super().add_char(char)
        pass


class BotPlayer(Player):
    # potentially ???
    def __init__(self, solution_word) -> None:
        super().__init__(solution_word)


class NetworkHandler(threading.Thread):
    """
    Handles the Network stuff in a seperate thread

    """

    def __init__(
            self, new_player_queue: queue.Queue,
            remove_player_queue: queue.Queue,
            send_add_queue: queue.Queue,
            send_remove_queue: queue.Queue,
            ready_event: threading.Event,
            unready_event: threading.Event,
            leave_event: threading.Event
        ) -> None:
        """
        initialize. the client player has to be in the queue
        then create_socket()
        then join_network() or create_network()
        then run handle() continiously with self.start()
        """
        super().__init__(target=self.handle)

        self.new_player_queue = new_player_queue
        self.remove_player_queue = remove_player_queue
        self.send_add_queue = send_add_queue
        self.send_remove_queue = send_remove_queue
        self.ready_event = ready_event
        self.unready_event = unready_event
        self.leave_event = leave_event

        self.players = {}
        self.message_queue = queue.Queue()

        # store the client player in the players list
        player = self.new_player_queue.get()
        self.players[player.identifier] = player
        # store the identifier of the clients player
        self.client_player_identifier = player.identifier

        self.has_joined_a_network = False

        self.magic_number = 0x8b0968b3
        self.message_types = ['j', 'k', 'l', 'm', 'n', 'r', 'u', 'c', 'd', 'w', 'l', 'e']

        # create a ipv4 TCP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # maybe use AF_INET6 (ipv6)
        # bind the socket to '' (meaning INADDR_ANY, binding to all interfaces)
        # and port 0, which lets the os chose a port
        self.socket.bind(('', 0))
        d_print(f"{self.socket.getsockname()=}")                        # DEBUG
        # setting up a kind of queue for a socket, so if several connections are trying to communicate simultainiously, they will be handled sequentially
        self.socket.listen()
        # make the socket non-blocking, as select will be 'polling' the sockets
        self.socket.setblocking(False)
        # storing all sockets which could be recieving data from a remote
        self.inputs = [self.socket]
        # storing all sockets which could be sending data to a remote
        self.outputs = []

        # DEBUG to send data
        # self.magic_number = 0x8b0968b3
        # self.message_types = ['j', 'k', 'l', 'm', 'r', 'u', 'c', 'w', 'l']
        # self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # maybe use AF_INET6 (ipv6)
        # self.socket.connect(('localhost', int(input())))
        # self.send_message(self.socket)  

              
    # def add_players_from_queue(self):
    #     """adding players from the queue to the self.players dict. may be redundant because adding new players is handled by another function"""
    #     while not self.new_player_queue.empty:
    #         # TODO: REDUNDANT method
    #         # maybe if this is really needed
    #         # most likely the NetworkHandler will be initialized without players in new_player_queue
    #         player = self.new_player_queue.get()
    #         self.players[player.identifier] = player

    def add_player(self, player: MultiPlayer):
        """add a player to the player dict and to the new_player_queue"""
        self.new_player_queue.put(player)
        self.players[player.identifier] = player

    def remove_player(self, player):
        """remove a player from the player dict and adds the player to the remove_player_queue"""
        self.remove_player_queue.put(player)
        self.players.pop(player.identifier)

    def handle(self):
        print("started handling ...")
        """continously handle incoming and outgoing messages"""
        # iterate until inputs are empty, meaning (hopefully) the socket has been closed
        while self.inputs:
            # sockets will be added to readable if there is data to be read
            # sockets will be added to writable if data could be sent
            # if self.data_to_be_sent(): ??
            #     outputs.append(...)    ??
            # FIXME: when something is continously in the outputs list, it kinda defeats the whole point of using select()

            # loop over message_queue
            #    make a connection to each entry(by identifier)
            #    add to self.outputs list 

            readable_sockets, writable_sockets, exceptional_sockets = select.select(self.inputs, self.outputs, self.inputs, ) # timeout: float = 
            for sock in readable_sockets:
                if sock == self.socket:
                    # if the socket is the 'base'socket, we have a new connection to accept
                    connection, remote_address = sock.accept()
                    connection.setblocking(False)
                    # appending the connection to the inputs
                    self.inputs.append(connection)
                    d_print(f"connection from {remote_address}")      # DEBUG
                else:
                    # recieve 1024 bytes
                    # player_id, data = self.recieve_data()
                    self.recieve_data(sock)
            
            for sock in writable_sockets:
                # TODO: check if there is data to send then send it
                self.handle_send_ready_unready_leave()
                self.handle_sending_add_remove_queue(sock)
                
            for sock in exceptional_sockets:
                # should not happen, if it does we just close the connection
                if sock in self.inputs:
                    self.inputs.remove(sock)
                else:
                    self.outputs.remove(sock)
                sock.close()
        print(f"lost the socket: {readable_sockets, writable_sockets, exceptional_sockets}")     # DEBUG
        # when this is reached the socket should have been closed      

    def handle_send_ready_unready_leave():
        # TODO
        pass

    def handle_sending_add_remove_queue(self, sock: socket.socket):
        """handles the sending of data"""
        # checks if there is a new char to be sent
        while len(self.send_add_queue.queue) > 0:
            # sends the last item from the send_add_queue to all players
            char = self.send_add_queue.get()
            for player in self.players:
                self.send_char_add_message(sock, char, player.identifier)

        # checks if there was a char removed (from the current word)
        while len(self.send_remove_queue.queue) > 0:
            # sends the last item from the send_remove_queue to all players
            char = self.send_remove_queue.get()
            for player in self.players:
                self.send_char_remove_message(sock, char, player.identifier)

    def send_message(self, connected_socket: socket.socket, message_type: str, message: str):
        """
        send one message to a socket

        layout: 
            magic number |  size  |     gamekey     | sender_identifier | message type |       message
               4bytes    | 4bytes |     8bytes      |      8bytes       |     1byte    | length given in {size}
                uInt     |  uInt  |   u Long Long   |    u Long Long    |     char     |        char[]
        format -> "!IIQQb"
        size <= 2**12 = 4096 bytes
        header size = exact 25 (4 + 4 + 8 + 8 + 1)
        total size <= 25 + 4096 = 4121 bytes

        magic number:
            always exactly: 0x8b0968b3

        message types:
            j (join request)      :  request to join the game
                - username
                - (gamekey)
                - (identifier = 0 (not set))

            k (join response accept):  send back an accept after a join request
                - identifier for the new player
                - list of players (IP + Port)
               
            l (join response deny) :  send back a deny after a join request
                - reason

            m (join note)         :  note to all players after
                - username

            n (join note response):  
                - username

            r (ready)             :  transmits a notice to all players that one player is ready to play or to restart
                - time as Unicode timestamp

            u (unready)           :  transmits a notice to all players that one player is not ready anymore
            c (char add)          :  transmits one char to be added
            d (char remove)       :  transmits one char to be removed
            w (word)              :  transmits one word (5 chars)
            l (leave)             :  transmits a notice of leaving the network
            e (err info)          :  note from NetworkCommunicator to Client to report an error
        all types: ['j', 'k', 'l', 'm', 'n', 'r', 'u', 'c', 'd', 'w', 'l', 'e']
        """
        sender_identifier = self.client_player_identifier
        format = "!IIQQb"
        message_type = ord(message_type)

        # message = "hello world"       # EXAMPLE
        # gamekey = 0xf272b57cc9fd9580  # EXAMPLE
        # sender_identifier = 404       # EXAMPLE
        # message_type = ord('j')       # EXAMPLE

        # pack the metadata into a C-alike struct, to get it in bytes  
        # uses ! for network byte order
        # consists of (unsigned Interger + unsigned Interger + unsigned Long Long + char
        header = struct.pack(
            format,
            self.magic_number,
            len(message),
            self.gamekey,
            sender_identifier,
            message_type
        )
        # connected_socket.sendall(header + bytes(message, "utf_8"))
        self.message_queue.append() # FIXME append what

        # d_print(f"struct: {struct.unpack(format, header)}")                                                                # DEBUG
        d_print(f"struct: {hex(self.magic_number), len(message), hex(self.gamekey), sender_identifier, chr(message_type)}")     # DEBUG
        d_print(header)                                                                                                      # DEBUG

    def recieve_data(self, sock):
        """recieve one message and handle it accordingly"""
        # TODO: !!! test for empty message !!!
        # TODO: could be done in one recieve

        # set socket to blocking, to recieve more than one time
        sock.setblocking(True)
        
        # uses ! for network byte order
        # consists of ( uInterger + uInterger + uLongLong + uLongLong + char )
        format = "!IIQQb"
        metadata_length = 4+4+8+8+1
        magic_number, size, gamekey, identifier, message_type = struct.unpack(format, sock.recv(metadata_length))
        message_type = chr(message_type)

        if magic_number != self.magic_number:
            # if the magic number doesnt match it is likely that something went wrong
            self.inputs.remove(sock)
            sock.close() 

        # make sure all data in the message was recieved, as it is not guaranteed to be within one sock.recv()
        data = bytes()
        while len(data) < size:
            data += sock.recv(size)

        sock.setblocking(False)

        # TODO: handle the message
        # TODO: check if self.has_network 
        # potentially a dict with message_type as keys and functions as their values ?? 
        if message_type in self.message_types:
            d_print(f"{hex(magic_number), size, hex(gamekey), identifier, message_type}")
            d_print(data)
        else:
            d_print(f"{message_type!r} unkown message type")

        # close the socket
        self.inputs.remove(sock)
        sock.close()
        exit()                          # DEBUG

    def connect_to_player(self, identifier: int):
        remote_address = self.players[identifier].remote_address

        try:
            self.socket.connect(remote_address)
            return True
        except ConnectionRefusedError:
            print(f"couldnt connect to {remote_address}, connection refused")
            return False

# TODO: fill out the following methods !

    def join_network(self, remote_address, gamekey: int, username: str):
        """
        join an already existing network
        
        make a socket
            - 

        send join request to socket
            - on fail -> ip or port wrong
        
        """
        if self.has_joined_a_network:
            print("Already part of a Network, leave the current network to join a new one")
            return False

        identifier = 0
        self.gamekey = gamekey

        print("join_network() executed")
        
        try:
            # connection is allowed to be blocking, because the thread has not yet started to select.select()
            connection, address = self.socket.connect(remote_address)

            self.send_message(
                sock=connection,
                identifier=identifier,
                message_type='j',
                message=username
            )

            connection.close()

        except ConnectionRefusedError:
            print(f"tried to join: {remote_address!r} but is not a vaild remote address")

    def create_network(self):
        """create a new network"""
        # TODO
        self.has_joined_a_network = True
        self.gamekey = 0xf272b57cc9fd9580 # EXAMPLE
        print("create_network() executed")
        # return local_address, gamekey
        pass


    def handle_join_request_message(self, sock: socket.socket):
        """handles the recieving of a j (join message)"""

        identifier = 0
        # generate an unique identifier for the new player
        identifier_max_val = 2**(8*8)
        # keep getting random values for the identifier if they are already in use by other players
        while identifier in self.players.keys() and identifier != 0:
            # start at 1, because identifier=0 is used for a special case (the join_request message)
            identifier = random.randint(1, identifier_max_val)

        # DENY or ACCEPT the join

        # send a join_response message
        # either a deny or accept
        self.send_message(
            sock=sock,
            identifier=identifier,
            message_type='',
            message=""
        )

    def handle_join_accept_message(self, identifier: int, playerlist):
        """handles the recieving of a k (join_response message)"""

        if len(self.players) != 1:
            print("playerlist should only contain one entry but contains: {self.players}")
            return False
        
        # switch the identifier to a value decided by another player to avoid identifier conflicts
        self.players[identifier] = self.players[self.client_player_identifier]
        del self.players[self.client_player_identifier]
        self.client_player_identifier = identifier
        
        # get all players from the playerlist to the self.players list
        for player in playerlist:
            self.add_player(player)

        self.has_joined_a_network = True

    def handle_join_deny_message(self):
        """handles the recieving of a l (join_response message)"""
        # TODO: THIS ONE NEXT
        self.has_joined_a_network = False # unnessecary since never set
        pass

    def handle_join_note_message(self):
        """handles the recieving of a m (join_note message)"""
        pass

    def handle_join_note_response_message(self):
        """handles the recieving of a n (join_note_response message)"""
        pass


    def handle_char_add_message(self, char: str, identifier: int):
        """handles the recieving of a char message"""
        pass

    def handle_char_remove_message(self, char: str, identifier: int):
        """handles the recieving of a char message"""
        pass

    def handle_word_message(self, word: str, identifier: int):
        """handles the recieving of a word message"""
        pass


    def handle_ready_message(self):
        pass

    def handle_unready_message(self):
        pass


    def handle_leave_message(self):
        pass

    def send_join_response_message(self):
        """sends a join_response message"""
        pass

    def send_join_note_message(self):
        """sends a join_note message"""
        pass

    def send_join_note_response_message(self):
        """sends a join_note_response message"""
        pass


    def send_char_add_message(self, sock: socket.socket, char: str, identifier: int):
        """sends a c (char) message"""
        if not self.connect_to_player(identifier=identifier):
            return False

        self.send_message(
            sock=sock,
            identifier=identifier,
            message_type='c',
            message=char
        )

    def send_char_remove_message(self, sock: socket.socket, char: str, identifier: int):
        """sends a b (char remove) message"""
        if not self.connect_to_player(identifier=identifier):
            return False

        self.send_message(
            sock=sock,
            identifier=identifier,
            message_type='b',
            message=char
        )

    def send_word_message(self, sock: socket.socket, word: str, identifier: int):
        """sends a word message"""
        self.send_message(
            sock=sock,
            identifier=identifier,
            message_type='w',
            message=word
        )


    def send_ready_message(self):
        pass

    def send_unready_message(self):
        pass


    def send_leave_message(self):
        pass


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
    p = MultiPlayer("tadal", 30, "hello")

    new_queue = queue.Queue()
    new_queue.put(p)

    remove_queue = queue.Queue()
    send_add_queue = queue.Queue()

    nh = NetworkHandler(new_player_queue    = new_queue,
                        remove_player_queue = remove_queue,
                        send_add_queue          = send_add_queue)
    
    nh.create_network()
    nh.join_network("raddr", 0xf272b57cc9fd9580) # EXAMPLE
    nh.start()
