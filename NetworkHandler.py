from datetime import datetime

import queue
import random

from Player import Player, MultiPlayer
from NetworkCommunicator import NetworkCommunicator
from WordList import CharStatus
from Errors import *

from color import *

# TODO join needs to send the right port to connect to
# TODO join_note needs to send the right port to connect to
# TODO First to send a ready message gets to decide the solution word
#       -> might cause problems when 2 player send simultaniously



class NetworkHandler:
    def __init__(self, playerlist: list, localhost: bool = False) -> None:

        if len(playerlist) != 1:
            raise ValueError("playerlist can only contain the client player upon creation of the Network Handler")

        self.message_in_queue = queue.LifoQueue()
        self.message_out_queue = queue.LifoQueue()

        self.network_communicator = NetworkCommunicator(
            message_in_queue=self.message_in_queue, 
            message_out_queue=self.message_out_queue,
            localhost=localhost
        )

        self.port = self.network_communicator.get_port # display the port to the mainloop / game
        self.host = self.network_communicator.get_host # display the host to the mainloop / game

        self.gamekey = None
        self.solution_word = None
        self.max_network_size = 5
        self.game_has_started = False
        self.has_joined_a_network = False
        self.currently_joining_a_network = False
        self.message_types = ['j', 'k', 'm', 'n', 'o', 'r', 's', 'u', 'c', 'd', 'w', 'l', 'e'] # TODO check for correctness

        self.client_identifier = 0
        self.identifier_to_raddr_dict: dict[int, tuple[str, int]] = {}
        self.identifier_to_player_dict: dict[int, MultiPlayer]  = {}
        player: MultiPlayer
        for player in playerlist:
            self.identifier_to_raddr_dict[player.identifier] = player.remote_address
            self.identifier_to_player_dict[player.identifier] = player
        
        self.username = self.identifier_to_player_dict[self.client_identifier].username

    def close(self) -> None:
        cprint(R, f"closing ...") # DEBUG
        self.send_to_all(send_message_function=self.send_message_leave, args=())
        self.network_communicator.close()

    def add_player(self, username: str, identifier: int, remote_address: tuple[str]) -> None:

        if self.solution_word is None:
            raise ValueError("maybe self.solution word cant be None on player creation, maybe it can??") # DEBUG

        player = MultiPlayer(
            solution_word=self.solution_word,      # DEBUG get the real solution word
            username=username,
            identifier=identifier,
            raddr=remote_address
        )

        self.identifier_to_raddr_dict[player.identifier] = player.remote_address
        self.identifier_to_player_dict[player.identifier] = player

        # TODO add to 

        cprint(G, f"USER ADDED: {player.username=}")     # DEBUG

    def gen_random_bytes(self, byte_count: int, start: int = 0) -> int:
        """method to get a specified amount of random bytes

        the highest number to be reuturned is 2**(byte_count*8)

        Args:
            - byte_count: number of random bytes ot be  returned
            - start: specifies the smallest possible value to be returnd
        
        Returns:
            - random integer

        """

        return random.randint(start, 2 ** (byte_count*8))

    def send_message(self, message_type: str, message_string: str = None, reciever_identifier: int = None, remote_address: tuple = None) -> None:
        """adds a message to the message_out_queue

        ## Note:
        #   use either one of reciever_identifier or remote_address 

        Args:
            - message_type         : a single char specifying the type of the message
            - message_string       : the variable length part of the message
            - reciever_identifier  : the unique identifier for the reciever, use either this or the remote_address
            - remote_address       : the (IP, PORT) for the reciever, use either this or the reciever_identifier
        
        """

        """
        stores a message in self.message_out_queue, ready to be sent

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
                - port
                - username
                - (gamekey)
                - (identifier = 0 (not set))

            k (join response accept):  send back an accept after a join request
                - identifier for the new player
                - solution word # TODO
                - list of players (IP + Port)
               
            m (join response deny) :  send back a deny after a join request
                - reason

            n (join note)         :  note to all players after
                - port
                - username

            o (join note response):  
                - username

            s (start game)        : starts a game
                - solution word # TODO
                - time as Unicode timestamp
            
            e (err info)          :  note from NetworkCommunicator to Client to report an error
                - reason

            r (ready)             :  transmits a notice to all players that one player is ready to play or to restart
            u (unready)           :  transmits a notice to all players that one player is not ready anymore
            c (char add)          :  transmits one char to be added
            d (char remove)       :  transmits one char to be removed
            w (word)              :  transmits one word (5 chars)
            l (leave)             :  transmits a notice of leaving the network
        all types: ['j', 'k', 'l', 'm', 'n', 'r', 's', 'u', 'c', 'd', 'w', 'l', 'e']
        """

        if remote_address is None:
            if reciever_identifier is None:
                raise ValueError(f"only one of {remote_address, reciever_identifier} can be None, NOT BOTH")
            remote_address = self.identifier_to_raddr_dict[reciever_identifier]
        
        if message_string is None:
            message_string = ""

        sender_identifier = self.client_identifier

        message_data = self.gamekey, sender_identifier, message_type, message_string

        print(f"put message in queue: {message_type=}, {remote_address=}, {message_string=}") # DEBUG

        self.message_out_queue.put((remote_address, *message_data)) # FIXME: might not add a tuple but uses one as self ?? already fixed it??

    def check_for_recieved_messages(self) -> None:
        """checks for new messages and handles them

        to be called every so often from the mainloop
        
        """

        while not self.message_in_queue.empty():
            self.handle_recieved_message(self.message_in_queue.get())

    def handle_recieved_message(self, extended_message_data: tuple) -> None:

        remote_address, gamekey, sender_identifier, message_type_int, byte_message = extended_message_data

        message_type = chr(message_type_int)
        message_string = byte_message.decode()

        print(f"{red}recieved a message{reset}: {message_type=}, {sender_identifier=}") # DEBUG

        # TODO fill out big if statement
        # sort out messages first whether self-player is part of a network / currently joining a network
        if message_type == 'j':
            self.recieved_message_join_request(remote_address, message_string=message_string)
        elif message_type == 'k':
            self.recieved_message_join_response_accept(message_string)
        elif message_type == 'm':
            self.recieved_message_join_response_deny(message_string)
        elif message_type == 'n':
            self.recieved_message_join_note(
                message_string=message_string,
                remote_address=remote_address, 
                sender_identifier=sender_identifier
            )
        elif message_type == 'o':
            self.recieved_message_join_note_response(
                message_string=message_string, 
                remote_address=remote_address, 
                sender_identifier=sender_identifier
            )
        elif message_type == 's':
            # TODO
            pass
        elif message_type == 'e':
            # TODO
            pass
        elif message_type == 'r':
            # TODO
            pass
        elif message_type == 'u':
            # TODO
            pass
        elif message_type == 'c':
            self.recieved_message_char_add(
                sender_identifier=sender_identifier,
                message_string=message_string
            )
        elif message_type == 'd':
            self.recieved_message_char_remove(
                sender_identifier=sender_identifier,
                message_string=message_string
            )
            pass
        elif message_type == 'w':
            # TODO
            pass
        elif message_type == 'l':
            # TODO
            pass


    def join_network(self, gamekey: int, remote_address: tuple) -> None:

        # starting the communicator
        self.network_communicator.start()

        if self.has_joined_a_network:
            raise CouldNotJoinError("Could not join, already joining a network")
        if self.currently_joining_a_network:
            raise CouldNotJoinError("Could not join, already trying to join a network")
        else:
            self.gamekey = gamekey
            self.send_message_join_request(remote_address)


    def create_network(self, debug_gamekey, solution_word) -> None:

        # starting the communicator
        self.network_communicator.start()

        if self.has_joined_a_network:
            raise CouldNotCreateNetworkError("Could not create Network, already joining a network")
        if self.currently_joining_a_network:
            raise CouldNotCreateNetworkError("Could not create Network, already trying to join a network")

        # switch the client_identifier from a temporary one
        if self.client_identifier == 0:
            client_player: MultiPlayer = self.identifier_to_player_dict[0]
            del self.identifier_to_player_dict[0]
            del self.identifier_to_raddr_dict[0]

            self.client_identifier = self.gen_random_bytes(byte_count=8, start=1)

            self.identifier_to_raddr_dict[self.client_identifier] = client_player.remote_address
            self.identifier_to_player_dict[self.client_identifier] = client_player
            # print(f"self.identifier_to_raddr_dict(one None is okay, more than one not):{self.identifier_to_raddr_dict}") # DEBUG

        self.gamekey = self.gen_random_bytes(8, start=1)
        self.gamekey = debug_gamekey
        self.has_joined_a_network = True

        self.solution_word = solution_word
        self.identifier_to_player_dict[self.client_identifier].solution_word = solution_word

    
    def send_to_all(self, send_message_function, *args, include_reciever_identifier: bool = True) -> None:
        """will call a send_message_ ...(*args) to every player in the identifier_to_player_dict (except for the client itself)

        Args:
            - send_message_function       :  the send_message_ ...()-function to be called for all players
            - *args                       :  an iterable of the arguments to be passed to the function-'send_message_function'
            - include_reciever_identifier :  bool, whether to include the reciever identifier as the first argument to the 'send_message_function' 
        
        """

        for reciever_identifier, player in zip(self.identifier_to_player_dict.keys(), self.identifier_to_player_dict.values()):
            if reciever_identifier != self.client_identifier:    # excluding the client itself
                if include_reciever_identifier:
                    send_message_function(reciever_identifier, *args)
                else:
                    send_message_function(*args)


    def send_message_join_request(self, remote_address) -> None:
        """
        j (join request)      :  request to join the game
            - PORT!! # TODO
            - username
            - (gamekey)
            - (identifier = 0 (not set))
        """

        local_port_string = str(hex(self.port)[2:]).rjust(10, '_')
        username = self.username

        message_string = local_port_string + username

        self.send_message(
            remote_address=remote_address, 
            message_type='j', 
            message_string=message_string
        )

    def recieved_message_join_request(self, remote_address: tuple, message_string: str) -> None:
        """
        j (join request)      :  request to join the game
            - PORT
            - username
            - (gamekey)
            - (identifier = 0 (not set))
        """

        remote_port = int("0x" + message_string[:10].replace('_', ''), 16)
        username = message_string[10:]

        # replace the port on which the prev messge was sent with the port that the remote is listening on
        remote_address = remote_address[0], remote_port

        # TODO send deny if a game is already running
        if not self.has_joined_a_network:
            # send a denial
            self.send_message_join_response_deny(remote_address, "user has not joined a network to connect to")
        if len(self.identifier_to_player_dict) >= self.max_network_size:
            # the size will only be roughly controlled, as 2 players joining at the same time will probably be allowed to join even though only one would already fill the cap of max_network_size
            # send a denial
            self.send_message_join_response_deny(remote_address, "network already has too many users")
        else:
            # send an accept
            self.send_message_join_response_accept(remote_address)

    def send_message_join_response_accept(self, remote_address: tuple) -> None:
        """
        k (join response accept):  send back an accept after a join request
            - identifier for the new player
            - list of players (IP + Port)
        """ 
        # generate a new identifier for the new player (retry if it is already in use)
        new_player_identifier = self.gen_random_bytes(8, start=1)
        while new_player_identifier in self.identifier_to_raddr_dict:
            new_player_identifier = self.gen_random_bytes(8, start=1)

        if len(self.solution_word) != 5:
            raise ValueError(f"solution word has to be of length 5 but is: {self.solution_word!r}")

        # get the remote_addresses (raddr) of all the players (including self/client)
        remote_addresses_list = [player.remote_address for player in self.identifier_to_player_dict.values()]
        remote_addresses_list.remove(None)
        remote_addresses_list.append((self.host, self.port))

        # sending the list directly, not that great since i will use eval() to it back to a list
        self.send_message(
            remote_address=remote_address, 
            message_type='k', 
            message_string=self.solution_word + str(new_player_identifier).rjust(20, '_') + str(remote_addresses_list)
        )

    def recieved_message_join_response_accept(self, message_string: str) -> None:
        """
        k (join response accept):  send back an accept after a join request
            - identifier for the new player
            - list of players (IP + Port)
        """ 
        # using eval() is just asking for security problems ...
        # TODO replace eval with something diffrent (such as padding + using a seperator char)
        solution_word = message_string[:5]
        new_player_identifier = eval(message_string[5:25].replace('_', '')) # maybe use int() instead?
        remote_addresses_list = eval(message_string[25:])

        self.solution_word = solution_word
        self.identifier_to_player_dict[self.client_identifier].solution_word = solution_word

        # self.client_identifier = new_player_identifier

        # switch the client_identifier from a temporary one
        if self.client_identifier == 0:
            client_player: MultiPlayer = self.identifier_to_player_dict[0]
            del self.identifier_to_player_dict[0]
            del self.identifier_to_raddr_dict[0]

            self.client_identifier = new_player_identifier

            self.identifier_to_raddr_dict[self.client_identifier] = client_player.remote_address
            self.identifier_to_player_dict[self.client_identifier] = client_player
            # print(f"self.identifier_to_raddr_dict(one None is okay, more than one not):{self.identifier_to_raddr_dict}") # DEBUG

        for remote_address in remote_addresses_list:
            self.send_message_join_note(remote_address)

        self.has_joined_a_network = True

    def send_message_join_response_deny(self, remote_address: tuple, reason: str) -> None:
        """
        m (join response deny) :  send back a deny after a join request
            - reason
        """ 
        self.send_message(
            remote_address=remote_address, 
            message_type='m', 
            message_string=reason
        )

    def recieved_message_join_response_deny(self, message_string) -> None:
        """
        m (join response deny) :  send back a deny after a join request
            - reason
        """ 
        reason = message_string
        raise CouldNotJoinError(reason)

    def send_message_join_note(self, remote_address) -> None:
        """
        n (join note)         :  note to all players after
            - username
            - Port
        """ 

        local_port_string = str(hex(self.port)[2:]).rjust(10, '_')

        self.send_message(
            remote_address=remote_address, 
            message_type='n', 
            message_string=local_port_string + self.username
        )

    def recieved_message_join_note(self, message_string: str, remote_address: tuple, sender_identifier: int) -> None:
        """
        n (join note)         :  note to all players after
            - username
            - ort
        """ 

        remote_port = int("0x" + message_string[:10].replace('_', ''), 16)
        username = message_string[10:]

        remote_address = remote_address[0], remote_port

        self.add_player(
            username=username,
            identifier=sender_identifier,
            remote_address=remote_address
        )

        # send the response byck to the sender
        reciever_identifier = sender_identifier
        self.send_message_join_note_response(reciever_identifier)

    def send_message_join_note_response(self, reciever_identifier) -> None:
        """
        o (join note response):  
            - username
        """ 

        local_port_string = str(hex(self.port)[2:]).rjust(10, '_')
        username = self.identifier_to_player_dict[self.client_identifier].username

        self.send_message(
            reciever_identifier=reciever_identifier,
            message_type='o', 
            message_string=local_port_string + username
        )
    
    def recieved_message_join_note_response(self, message_string: str, remote_address: tuple, sender_identifier: int) -> None:
        """
        O (join note response):  
            - username
        """ 

        remote_port = int("0x" + message_string[:10].replace('_', ''), 16)
        username = message_string[10:]

        remote_address = remote_address[0], remote_port

        self.add_player(
            username=username,
            identifier=sender_identifier,
            remote_address=remote_address
        )

    def everyone_is_ready(self) -> bool:
        """
        returns True if every player in 'self.identifier_to_player_dict' is ready
        """

        everyone_ready = True
        player: MultiPlayer
        for player in self.identifier_to_player_dict.values():
                everyone_ready = False if not player.is_ready else everyone_ready
        return everyone_ready

    def send_message_ready_player(self, reciever_identifier: tuple) -> None:
        """
        r (ready player message)
            - solution word # TODO
        """
        self.send_message(
            reciever_identifier=reciever_identifier,
            message_type='r', 
            message_string=self.username
        )

        if self.everyone_is_ready():
            self.send_to_all(
                send_message_function=self.send_message_start,
                args=(datetime.now().timestamp()),
                include_reciever_address=True
            )


    def recieved_message_ready_player(self, sender_identifier: int) -> None:
        self.identifier_to_player_dict[sender_identifier].is_ready = True
        
        if self.everyone_is_ready():
            self.send_to_all(
                send_message_function=self.send_message_start,
                args=(datetime.now().timestamp()),
                include_reciever_address=True
            )

    def send_message_unready_player(self, reciever_identifier: int) -> None:
        """
        u (unready message)
        """
        self.send_message(
            reciever_identifier=reciever_identifier,
            message_type='u', 
            message_string=""
        )
        

    def recieved_message_unready_player(self, sender_identifier: int) -> None:
        """
        u (unready message)
        """
        # TODO there could be a sending a unready after the client has already started
        # maybe check if 90% of players are already ready and then lock the unready button
        self.identifier_to_player_dict[sender_identifier].is_ready = False

    def send_message_start(self, reciever_identifier, timestamp) -> None:
        """
        s (start message):
            - timestamp
        """
        self.send_message(
            reciever_identifier=reciever_identifier,
            message_type='s',
            message_string=str(timestamp),
        )

    def recieve_message_start(self, sender_identifier: int, message_string:str) -> None:
        """
        s (start message):
            - timestamp
        """
        self.identifier_to_player_dict[sender_identifier].starttime = float(message_string)
        # TODO
        # maybe do some checks
        self.game_has_started # maybe do this somewhere diffrent


    def send_message_char_add(self, reciever_identifier: int, char: str) -> None:
        """
        c (char add):
            - char
        """

        if len(char) != 1:
            raise CharTooLongError(f"'char' should be a char (or a string with length 1), but is {len(char)!r} long and contains: {char!r}")

        self.send_message(
            message_type='c',
            message_string=char,
            reciever_identifier=reciever_identifier
        )

    def recieved_message_char_add(self, sender_identifier: int, message_string: str) -> None:
        """
        c (char add):
            - char
        """
        player: MultiPlayer = self.identifier_to_player_dict[sender_identifier]

        if len(message_string) != 1:
            raise CharTooLongError(f"'message_string' should be a char (or a string with length 1), but is {len(message_string)!r} long and contains: {message_string!r}")
        char = message_string.casefold()

        # TODO might have to think about the other player filling up his entire grid

        if player.add_char(char=char) == [CharStatus.correct_position]*5:
            # the player won
            player.endtime = datetime.now().timestamp()
            player.won = True
            # TODO there might be more stuff todo if a player wins
    
    def send_message_char_remove(self, reciever_identifier: int, char: str) -> None:
        """
        d (char remove):
            - char
        """
        
        if len(char) != 1:
            raise CharTooLongError(f"'char' should be a char (or a string with length 1), but is {len(char)!r} long and contains: {char!r}")

        self.send_message(
            message_type='d',
            message_string=char,
            reciever_identifier=reciever_identifier
        )
    
    def recieved_message_char_remove(self, sender_identifier: int, message_string: str) -> None:
        """
        d (char remove):
            - char
        """
        
        player: MultiPlayer = self.identifier_to_player_dict[sender_identifier]

        if len(message_string) != 1:
            raise CharTooLongError(f"'message_string' should be a char (or a string with length 1), but is {len(message_string)!r} long and contains: {message_string!r}")
        char = message_string.casefold()

        player.remove_char(char=char)


    def send_message_word(self, reciever_identifier: int, word: str) -> None:
        """
        w (send word):
            - word
        """

        if len(word) != 5:
            raise WordTooLongError(f"'word' should be of length 5, but is {len(word)!r} long and contains: {word!r}")
        
        self.send_message(
            message_type='w',
            message_string=word,
            reciever_identifier=reciever_identifier
        )

    def recieved_message_word(self, sender_identifier: int, message_string) -> None:
        """
        w (send word):
            - word
        """
        
        player: MultiPlayer = self.identifier_to_player_dict[sender_identifier]

        if len(message_string) != 5:
            raise WordTooLongError(f"'message_string' should be of length 5, but is {len(message_string)!r} long and contains: {message_string!r}")
        word = message_string.casefold()

        match = player.add_word(word)

        # NOTE since the player sends the starttime, but the endtime is taken locally, if there is a high ping the remoteplayer may get a diffrent time for his win/loss
        if match == [CharStatus.correct_position]*5:
            # the player won
            player.endtime = datetime.now().timestamp()
            player.won = True
        elif match and player.current_word_index >= player.max_word_guesses:
            # player lost
            player.endtime = datetime.now().timestamp()


    def send_message_leave(self, reciever_identifier: int) -> None:
        """
        l (leave message)
        """
        self.send_message(
            message_type='l',
            message_string="",
            reciever_identifier=reciever_identifier
        )

    def recieved_message_leave(self, sender_identifier: int) -> None:
        """
        l (leave message)
        """
        # TODO unsure whether this is enough 
        if sender_identifier in self.identifier_to_player_dict:
            del self.identifier_to_player_dict[sender_identifier]
            del self.identifier_to_raddr_dict[sender_identifier]