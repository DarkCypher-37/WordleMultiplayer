from datetime import datetime

import queue
import random

from Player import Player, MultiPlayer
from NetworkCommunicator import NetworkCommunicator

# TODO join needs to send the right port to connect to
# TODO join_note needs to send the right port to connect to

import colorama                    # DEBUG
colorama.init()                    # DEBUG
green = colorama.Fore.GREEN        # DEBUG
red = colorama.Fore.RED            # DEBUG
reset = colorama.Style.RESET_ALL   # DEBUG

class CouldNotCreateNetwork(Exception):
    pass

class CouldNotJoinError(Exception):
    pass

class NetworkHandler:
    def __init__(self, playerlist: list, username: str, debug_port, localhost: bool = False) -> None:

        if len(playerlist) != 1:
            raise ValueError("playerlist can only contain the client player upon creation of the Network Handler")

        self.message_in_queue = queue.LifoQueue()
        self.message_out_queue = queue.LifoQueue()
        self.username = username

        self.network_communicator = NetworkCommunicator(
            message_in_queue=self.message_in_queue, 
            message_out_queue=self.message_out_queue,
            localhost=localhost,
            port=debug_port
        )

        self.port = self.network_communicator.get_port # display the port to the mainloop / game
        self.host = self.network_communicator.get_host # display the host to the mainloop / game

        self.gamekey = None
        self.max_network_size = 5
        self.game_has_started = False
        self.has_joined_a_network = False
        self.currently_joining_a_network = False
        self.message_types = ['j', 'k', 'm', 'n', 'o', 'r', 's', 'u', 'c', 'd', 'w', 'l', 'e']

        self.client_identifier = 0
        self.identifier_to_raddr_dict = {}
        self.identifier_to_player_dict = {}
        for player in playerlist:
            self.identifier_to_raddr_dict[player.identifier] = player.remote_address
            self.identifier_to_player_dict[player.identifier] = player

    def add_player(self, username: str, identifier: int, remote_address) -> None:
        player = MultiPlayer(
            solution_word="teest",      # DEBUG get the real solution word
            username=username,
            identifier=identifier,
            raddr=remote_address
        )

        self.identifier_to_raddr_dict[player.identifier] = player.remote_address
        self.identifier_to_player_dict[player.identifier] = player

        print(f"{green} USER ADDED: {player.username=}{reset}")

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
                - PORT
                - username
                - (gamekey)
                - (identifier = 0 (not set))

            k (join response accept):  send back an accept after a join request
                - identifier for the new player
                - list of players (IP + Port)
               
            l (join response deny) :  send back a deny after a join request
                - reason
            
            e (err info)          :  note from NetworkCommunicator to Client to report an error
                - reason

            m (join note)         :  note to all players after
                - PORT !! # TODO
                - username

            n (join note response):  
                - username

            s (start game)        : starts a game
                - time as Unicode timestamp

            r (ready)             :  transmits a notice to all players that one player is ready to play or to restart
            u (unready)           :  transmits a notice to all players that one player is not ready anymore
            c (char add)          :  transmits one char to be added
            d (char remove)       :  transmits one char to be removed
            w (word)              :  transmits one word (5 chars)
            l (leave)             :  transmits a notice of leaving the network
        all types: ['j', 'k', 'l', 'm', 'n', 'r', 's', 'u', 'c', 'd', 'w', 'l', 'e']
        """

        # print("send executed") # DEBUG

        if remote_address is None:
            if reciever_identifier is None:
                raise ValueError(f"only one of {remote_address, reciever_identifier} can be None, NOT BOTH")
            remote_address = self.identifier_to_raddr_dict[reciever_identifier]
        
        if message_string is None:
            print(f"DEBUG: {message_string=} may cause an error or not, idk man")       # DEBUG
            message_string = ""

        sender_identifier = self.client_identifier

        message_data = self.gamekey, sender_identifier, message_type, message_string

        # print(f"qsending: {remote_address, message_data=}")  # DEBUG
        print(f"putting a message in the queue: {message_type=}, {remote_address=}") # DEBUG

        self.message_out_queue.put((remote_address, *message_data)) # FIXME: might not add a tuple but uses one as self ?? already fixed it??

    def check_for_recieved_messages(self):
        """checks for new messages and handles them

        to be called every so often from the mainloop
        
        """

        while not self.message_in_queue.empty():
            # print("something is lurking in the in_queue") # DEBUG
            self.handle_recieved_message(self.message_in_queue.get())

    def handle_recieved_message(self, extended_message_data: tuple):

        remote_address, gamekey, sender_identifier, message_type_int, byte_message = extended_message_data

        message_type = chr(message_type_int)
        message_string = byte_message.decode()

        # print(f"from: {remote_address} | type: {message_type} | says: {message_string}") # DEBUG
        print(f"recieved a message: {message_type=}, {sender_identifier=}") # DEBUG

        # TODO prob. a big if statement
        # sort out messages first whether self-player is part of a network / currently joining a network
        if message_type == 'j':
            self.recieved_message_join_request(remote_address, message_string=message_string)
        if message_type == 'k':
            self.recieved_message_join_response_accept(message_string)
        if message_type == 'm':
            self.recieved_message_join_response_deny(message_string)
        if message_type == 'n':
            self.recieved_message_join_note(
                message_string=message_string, 
                remote_address=remote_address, 
                sender_identifier=sender_identifier
            )
        if message_type == 'o':
            self.recieved_message_join_note_response(
                message_string=message_string, 
                sender_identifier=sender_identifier
            )
        # if message_type == 'j':
        #     pass


    def join_network(self, gamekey: int, remote_address: tuple):

        # print("executed join_network, starting the NC") # DEBUG

        # starting the communicator
        self.network_communicator.start()

        self.temporary_join_network_remote_address = remote_address

        if self.has_joined_a_network:
            raise CouldNotJoinError("Could not join, already joining a network")
        if self.currently_joining_a_network:
            raise CouldNotJoinError("Could not join, already trying to join a network")
        else:
            self.gamekey = gamekey
            self.send_message_join_request(remote_address)


    def create_network(self, debug_gamekey):

        # print("executed create_network, starting the NC") # DEBUG

        # starting the communicator
        self.network_communicator.start()

        if self.has_joined_a_network:
            raise CouldNotCreateNetwork("Could not create Network, already joining a network")
        if self.currently_joining_a_network:
            raise CouldNotCreateNetwork("Could not create Network, already trying to join a network")

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
        print("finished creating the network") # DEBUG

    
    def send_to_all(self, send_message_function, *args, include_reciever_identifier: bool = False):
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

    def recieved_message_join_request(self, remote_address: tuple, message_string: str):
        """
        j (join request)      :  request to join the game
            - PORT !!! # TODO
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
        # print("message_join_resp_acc") # DEBUG

        # get the remote_addresses (raddr) of all the players (including self/client)
        remote_addresses_list = [player.remote_address for player in self.identifier_to_player_dict.values()]
        remote_addresses_list.remove(None)
        remote_addresses_list.append((self.host, self.port))

        # sending the list directly, not that great since i will use eval() to it back to a list
        self.send_message(
            remote_address=remote_address, 
            message_type='k', 
            message_string=str(new_player_identifier).rjust(20, '_') + str(remote_addresses_list)
        )

    def recieved_message_join_response_accept(self, message_string: str):
        """
        k (join response accept):  send back an accept after a join request
            - identifier for the new player
            - list of players (IP + Port)
        """ 
        # using eval() is just asking for security problems ...
        # TODO replace eval with something diffrent (such as padding + using a seperator char)
        new_player_identifier = eval(message_string[:20].replace('_', ''))
        remote_addresses_list = eval(message_string[20:])
        
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

    def recieved_message_join_response_deny(self, message_string):
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
            # TODO Port
        """ 

        local_port_string = str(hex(self.port)[2:]).rjust(10, '_')

        self.send_message(
            remote_address=remote_address, 
            message_type='n', 
            message_string=local_port_string + self.username
        )

    def recieved_message_join_note(self, message_string: str, remote_address: tuple, sender_identifier: int):
        """
        n (join note)         :  note to all players after
            - username
            # TODO Port
        """ 
        # TODO create a new player (username!!)

        remote_port = int("0x" + message_string[:10].replace('_', ''), 16)
        username = message_string[10:]

        remote_address = remote_address[0], remote_port

        self.add_player(
            username=username,
            identifier=sender_identifier,
            remote_address=remote_address
        )

        # send the response bck to the sender
        reciever_identifier = sender_identifier
        self.send_message_join_note_response(reciever_identifier)

    def send_message_join_note_response(self, reciever_identifier) -> None:
        """
        o (join note response):  
            - username
        """ 
        self.send_message(
            reciever_identifier=reciever_identifier,
            message_type='o', 
            message_string=self.username
        )
    
    def recieved_message_join_note_response(self, message_string: str, sender_identifier: int):
        """
        O (join note response):  
            - username
        """ 

        username = message_string

        self.add_player(
            username=username,
            identifier=sender_identifier,
            remote_address=self.temporary_join_network_remote_address
        )

        del self.temporary_join_network_remote_address

    def everyone_is_ready(self) -> bool:
        """returns True if every player in 'self.identifier_to_player_dict' is ready
        
        """

        everyone_ready = True
        player: MultiPlayer
        for player in self.identifier_to_player_dict.values():
                everyone_ready = False if not player.is_ready else everyone_ready
        return everyone_ready

    def send_message_ready_player(self, reciever_identifier: tuple) -> None:
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


    def recieved_message_ready_player(self, sender_identifier: int):
        self.identifier_to_player_dict[sender_identifier].is_ready = True
        
        if self.everyone_is_ready():
            self.send_to_all(
                send_message_function=self.send_message_start,
                args=(datetime.now().timestamp()),
                include_reciever_address=True
            )

    def send_message_unready_player(self, reciever_identifier: int) -> None:
        self.send_message(
            reciever_identifier=reciever_identifier,
            message_type='u', 
            message_string=""
        )
        

    def recieved_message_unready_player(self, sender_identifier: int):
        # TODO there could be a sending a unready after the client has already started
        # maybe check if 90% of players are already ready and then lock the unready button
        self.identifier_to_player_dict[sender_identifier].is_ready = False

    def send_message_start(self, reciever_identifier, timestamp):
        self.send_message(
            reciever_identifier=reciever_identifier,
            message_type='s',
            message_string=str(timestamp),
        )

    def recieve_message_start(self, sender_identifier: int, message_string:str) -> None:
        self.identifier_to_player_dict[sender_identifier].starttime = float(message_string)
        self.game_has_started # maybe do this somewhere diffrent


    def send_message_char_add(self) -> None:
        pass

    def recieved_message_char_add(self):
        pass
    
    def send_message_char_remove(self) -> None:
        pass
    
    def recieved_message_char_remove(self):
        pass
    

    def send_message_word(self) -> None:
        pass

    def recieved_message_word(self):
        pass

    def send_message_leave(self) -> None:
        # TODO empty out the playerlist
        pass

    def recieved_message_leave(self):
        pass