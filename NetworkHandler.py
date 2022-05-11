from operator import ne
import queue
import random
import struct

import NetworkCommunicator

class CouldNotJoinError(Exception):
    pass

class NetworkHandler:
    def __init__(self, playerlist: list, username: str) -> None:
        self.message_in_queue = queue.LifoQueue
        self.message_out_queue = queue.LifoQueue
        self.username = username

        self.network_communicator = NetworkCommunicator.NetworkCommunicator(self.message_in_queue, self.message_out_queue)
        self.port = self.network_communicator.get_port

        self.client_identifier = None
        self.gamekey = None
        self.max_network_size = 5
        self.has_joined_a_network = False
        self.message_types = ['j', 'k', 'm', 'n', 'o', 'r', 'u', 'c', 'd', 'w', 'l', 'e']

        self.identifier_to_raddr_dict = {}
        self.identifier_to_player_dict = {}
        for player in playerlist:
            self.identifier_to_raddr_dict[player.identifier] = player.remote_address
            self.identifier_to_player_dict[player.identifier] = player

    def gen_random_bytes(self, byte_count, start = 0):
        return random.randint(start, 2 ** (byte_count*8))

    def send_message(self, message_type: str, message_string: str, reciever_identifier: int = None, remote_address: tuple = None) -> None:
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
        all types: ['j', 'k', 'l', 'm', 'n', 'r', 'u', 'c', 'd', 'w', 'l', 'e']
        """
        if remote_address is None:
            if reciever_identifier is None:
                raise ValueError(f"only one of [remote_address, reciever_identifier} can be None, NOT BOTH")
            remote_address = self.identifier_to_raddr_dict[reciever_identifier]
        
        sender_identifier = self.client_identifier

        message_data = self.gamekey, sender_identifier, message_type, message_string

        self.message_out_queue.put(remote_address, *message_data)

    def check_for_recieved_messages(self):
        while self.message_in_queue.not_empty():
            self.handle_recieved_message(self.message_in_queue.get())

    def handle_recieved_message(self, extended_message_data: tuple):

        remote_address, gamekey, sender_identifier, message_type, byte_message = extended_message_data

        # TODO prob. a big if statement
        pass


    def join_network(self, gamekey: int):
        self.gamekey = gamekey
        self.has_joined_a_network = 

    def create_network(self):
        self.gamekey = 
        self.has_joined_a_network = 

    
    def send_to_all(self, f, *args, include_reciever_address: bool = False):
        if include_reciever_address:
            for player in self.identifier_to_player_dict.values():
                f(player.reciever_address, *args)
        else:
            for player in self.identifier_to_player_dict.values():
                f(*args)


    def send_message_join_request(self, remote_address) -> None:
        self.send_message(
            remote_address=remote_address, 
            message_type='j', 
            message_string=self.username
        )

    def recieved_message_join_request(self, remote_address: tuple):
        # TODO game already running
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

        # generate a new identifier for the new player (retry if it is already in use)
        new_player_identifier = self.gen_random_bytes(8, start=1)
        while not new_player_identifier in self.identifier_to_raddr_dict:
            new_player_identifier = self.gen_random_bytes(8, start=1)

        # list of remote_addresses_list, not that great since i will use eval() to it back to a list
        remote_addresses_list = [player.remote_address for player in self.identifier_to_player_dict.value()]

        self.send_message(
            remote_address=remote_address, 
            message_type='k', 
            message_string=str(new_player_identifier).rjust(20, '_') + str(remote_addresses_list)
        )

    def recieved_message_join_response_accept(self, message_string: str):
        
        # using eval() could be dangerous 
        new_player_identifier = eval(message_string[:20].replace('_', ''))
        remote_addresses_list = eval(message_string[20:])

        print(f"{new_player_identifier, remote_addresses_list, type(new_player_identifier), type(remote_addresses_list)=}")
        
        self.client_identifier = new_player_identifier

        for remote_address in remote_addresses_list:
            self.send_message_join_note(remote_address)

    def send_message_join_response_deny(self, remote_address: tuple, reason: str) -> None:
        self.send_message(
            remote_address=remote_address, 
            message_type='m', 
            message_string=reason
        )

    def recieved_message_join_response_deny(self, message_string):
        reason = message_string
        raise CouldNotJoinError(reason)

    def send_message_join_note(self, remote_address) -> None:
        self.send_message(
            remote_address=remote_address, 
            message_type='n', 
            message_string=self.username
        )
    
    def recieved_message_join_note(self, username: str, remote_address: tuple, sender_identifier: int):
        # TODO create a new player

        # send the response bck to the sender
        reciever_identifier = sender_identifier
        self.send_message_join_note_response(reciever_identifier)

    def send_message_join_note_response(self, reciever_identifier) -> None:
        self.send_message(
            reciever_identifier=reciever_identifier,
            message_type='o', 
            message_string=self.username
        )
    
    def recieved_message_join_note_response(self, message_string, sender_identifier, ):
        # TODO create a new player with username: message_string
        pass


    def send_message_ready_player(self, reciever_identifier: tuple) -> None:
        self.send_message(
            reciever_identifier=reciever_identifier,
            message_type='r', 
            message_string=self.username
        )

    def recieved_message_ready_player(self, sender_identifier: int):
        self.identifier_to_player_dict[sender_identifier]

    def send_message_unready_player(self) -> None:
        pass

    def recieved_message_unready_player(self):
        pass


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
        pass

    def recieved_message_leave(self):
        pass