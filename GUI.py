from datetime import datetime
import arcade
from Errors import AlreadyWonError, CharTooLongError, OutOfWordTableBounds
from Game import MultiplayerGame
from WordList import CharStatus
import Shapes

from color import *

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600


class StartView(arcade.View):
    """
    THE STARTVIEW.
    """

    def __init__(self) -> None:
        super().__init__()
        arcade.set_background_color(arcade.color.AMAZON)

        self.splash_text = None
        self.create_button = None
        self.join_button = None

    def setup(self) -> None:
        self.splash_text = Shapes.Text(
            text="WORDLE",
            x=SCREEN_WIDTH/2,
            y=SCREEN_HEIGHT * 4/5,
            color=arcade.color.WARM_BLACK,
            font_size=60,
        )

        self.join_button = Shapes.Button(
            x=SCREEN_WIDTH/2,
            y=SCREEN_HEIGHT*7/20,
            width=200,
            height=80,
            color=arcade.color.BLUE_GRAY, #(102, 153, 204)	
            hover_color=arcade.color_from_hex_string("#5783AE"),
            text_color=arcade.color.WARM_BLACK,
            text="Join Network",
            font_size=20
        )

        self.create_button = Shapes.Button(
            x=SCREEN_WIDTH/2,
            y=SCREEN_HEIGHT * 11/20,
            width=200,
            height=80,
            color=arcade.color.GOLDENROD,
            hover_color=arcade.color.DARK_GOLDENROD,
            text_color=arcade.color.WARM_BLACK,
            text="Create Network",
            font_size=20
        )

    def on_draw(self) -> None:
        self.clear()

        self.splash_text.draw()
        
        self.join_button.draw()
        self.create_button.draw()


    def on_update(self, delta_time) -> None:
        pass

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.join_button.is_mouse_hovering(x, y)
        self.create_button.is_mouse_hovering(x, y)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> None:
        if self.join_button.hover:
            enter_port_view = EnterPortView()
            enter_port_view.setup()
            self.window.show_view(enter_port_view)

        elif self.create_button.hover:
            enter_username_view = EnterUsernameView()
            enter_username_view.setup()
            self.window.show_view(enter_username_view)

class EnterPortView(arcade.View):
    """
    ENTER THE IP, PORT, GAMEKEY.
    """

    def __init__(self) -> None:
        super().__init__()
        arcade.set_background_color(arcade.color.AMAZON)
        self.input_port = None
        self.input_ip = None
        self.cursor_time = 0
        self.cursor_time_threshold = 0.3
        self.current_active_input = None
        self.inputs = []

    def setup(self) -> None:

        self.input_ip = Shapes.InputPrompt(
            x=SCREEN_WIDTH/2,
            y=SCREEN_HEIGHT * 12/20,
            height=50,
            width=500,
            hover_color=arcade.color.DARK_RED,
            text_color=arcade.color.WARM_BLACK,
            active_color=arcade.color_from_hex_string("#002929"),
            font_size=20,
            text="IP: ",
            input_length=15
        )
        self.inputs.append(self.input_ip)

        self.input_port = Shapes.InputPrompt(
            x=SCREEN_WIDTH/2,
            y=SCREEN_HEIGHT * 10/20,
            height=50,
            width=300,
            hover_color=arcade.color.DARK_RED,
            text_color=arcade.color.WARM_BLACK,
            active_color=arcade.color_from_hex_string("#002929"),
            font_size=20,
            text="PORT: ",
            input_length=5
        )
        self.inputs.append(self.input_port)

        self.input_gamekey = Shapes.InputPrompt(
            x=SCREEN_WIDTH/2,
            y=SCREEN_HEIGHT * 8/20,
            height=50,
            width=500,
            hover_color=arcade.color.DARK_RED,
            text_color=arcade.color.WARM_BLACK,
            active_color=arcade.color_from_hex_string("#002929"),
            font_size=20,
            text="GAMEKEY: ",
            input_length=16
        )

        self.inputs.append(self.input_gamekey)

        self.current_active_input = 0
        self.inputs[self.current_active_input].set_active()

    def loop_active_input(self) -> None:
        if self.current_active_input >= len(self.inputs)-1:
            self.inputs[self.current_active_input].set_inactive()
            self.current_active_input = 0
            self.inputs[self.current_active_input].set_active()
        else:
            self.inputs[self.current_active_input].set_inactive()
            self.current_active_input += 1
            self.inputs[self.current_active_input].set_active()

    def next_active_input(self) -> None:
        if self.current_active_input >= len(self.inputs)-1:
            self.validate_inputs()
        else:
            self.inputs[self.current_active_input].set_inactive()
            self.current_active_input += 1
            self.inputs[self.current_active_input].set_active()

    def on_draw(self) -> None:
        self.clear()
        for element in self.inputs:
            element.draw()

    def on_update(self, delta_time) -> None:
        self.cursor_time += delta_time
        if self.cursor_time >= self.cursor_time_threshold:
            self.inputs[self.current_active_input].blink()
            self.cursor_time = 0

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        for element in self.inputs:
            element.is_mouse_hovering(x, y)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> None:
        for index, element in enumerate(self.inputs):
            if element.hover:
                self.inputs[self.current_active_input].set_inactive()
                self.current_active_input = index
                self.inputs[self.current_active_input].set_active()

    def validate_inputs(self) -> None:
            success = True
            ip = self.input_ip.input
            try:
                _ = int(ip.replace('.', ''))
            except:
                if ip == "":
                    ip = "127.0.0.1"
                else:
                    success = False
                    self.input_ip.illegal_input()

            try:
                port = int(self.input_port.input)
            except:
                success = False
                self.input_port.illegal_input()

            try:
                gamekey = int(self.input_gamekey.input, 16)
            except:
                success = False
                self.input_gamekey.illegal_input()

            if success:
                info = ((ip, port), gamekey)
                enter_username_view = EnterUsernameView()
                enter_username_view.setup(info)
                self.window.show_view(enter_username_view)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol in range(ord('a'), ord('z')+1) or symbol in range(ord('0'), ord('9')+1) or symbol == ord('.'):
            char = chr(symbol)
            self.inputs[self.current_active_input].add_input(char)

        # include Numpad
        elif symbol in range(65456, 65465+1):
            char = chr(symbol - 65456 + ord('0'))
            self.inputs[self.current_active_input].add_input(char)

        elif symbol == arcade.key.BACKSPACE:
            self.inputs[self.current_active_input].remove_input()
        elif symbol == arcade.key.ENTER:
            # if self.inputs[self.current_active_input].is_full():
            self.next_active_input()

        elif symbol == arcade.key.TAB:
            self.loop_active_input()


class EnterUsernameView(arcade.View):
    """
    ENTER THE USERNAME.
    """

    def __init__(self):
        super().__init__()

        arcade.set_background_color(arcade.color.AMAZON)

        self.input_username = None
        self.remote_address = None
        self.gamekey = None

    def setup(self, info: tuple[tuple[str, int], int]=None):
        if info is not None:
            self.remote_address, self.gamekey = info

        self.input_username = Shapes.InputPrompt(
            x=SCREEN_WIDTH/2,
            y=SCREEN_HEIGHT * 10/20,
            height=50,
            width=300,
            hover_color=arcade.color.DARK_RED,
            text_color=arcade.color.WARM_BLACK,
            active_color=arcade.color_from_hex_string("#002929"),
            font_size=20,
            text="username: ",
            input_length=10
        )

    def on_draw(self):
        self.clear()
        self.input_username.draw()

    def on_update(self, delta_time: float):
        pass

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol in range(ord('a'), ord('z')+1):
            char = chr(symbol)
            self.input_username.add_input(char)

        elif symbol == arcade.key.BACKSPACE:
            self.input_username.remove_input()

        elif symbol == arcade.key.ENTER:
            username = self.input_username.input

            game_view = GameView()
            game_view.setup(
                username=username,
                remote_address=self.remote_address,
                gamekey=self.gamekey
            )

            self.window.show_view(game_view)


class GameView(arcade.View):
    """
    THE GAMEVIEW.
    """

    def __init__(self) -> None:

        super().__init__()

        arcade.set_background_color(arcade.color.AMAZON)

        self.game = None
        self.ready_button = None
        self.won = None

        self.client_word_table = None
        self.player_word_tables = []

    def setup(self, username: str, remote_address = None, gamekey = None) -> None:
        """ Set up the game variables. Call to re-start the game. """
        self.game = MultiplayerGame()

        print(f"{username=}, {remote_address=}, {gamekey=}")
        if gamekey is not None and remote_address is not None:
            self.game.join_network(
            gamekey=gamekey,
            remote_address=remote_address
            )
        else:
            self.game.create_network()
        
        self.client_word_table = Shapes.WordTable(
            x=SCREEN_WIDTH/2 - (2*50),
            y=SCREEN_HEIGHT - 100,
            pad=50,
            word_table=self.game.player.word_table,
            match_table=self.game.player.match_table
        )

        self.update_players()

        self.ready_button = Shapes.Button(
            x=SCREEN_WIDTH*3/20,
            y=SCREEN_HEIGHT*18/20,
            width=200,
            height=80,
            color=arcade.color.BLUE_GRAY, #(102, 153, 204)	
            hover_color=arcade.color_from_hex_string("#5783AE"),
            text_color=arcade.color.WARM_BLACK,
            text="NOT READY",
            font_size=20
        )


    def on_close(self) -> None:
        self.game.close()

    def on_draw(self) -> None:
        """
        Render the screen.
        """
        self.clear()
        
        if not self.game.network_handler.game_has_started:
            self.ready_button.draw()
        
        if self.game.player.starttime is not None:
            time_elapsed = datetime.fromtimestamp(datetime.now().timestamp() - self.game.player.starttime).strftime('%M:%S.%f')
        else:
            time_elapsed = "00:00"

        self.draw_info(
            f"HOST: {self.game.network_handler.host}",
            f"PORT: {self.game.network_handler.port}",
            f"players: {len(self.game.network_handler.identifier_to_player_dict)}",
            f"solution word: {self.game.network_handler.solution_word}",
            f"Gamekey: {self.game.network_handler.gamekey}",
            f"Time: {time_elapsed}"
        )

        self.client_word_table.draw()

        for element in self.player_word_tables:
            element.draw()

    def draw_info(self, *args) -> None:

        x_start = SCREEN_WIDTH-330
        y_start = SCREEN_HEIGHT-40

        y_pad = 20

        for index, text in enumerate(args):

            arcade.draw_text(
                text=f"{text}",
                start_x=x_start,
                start_y=y_start - index*y_pad,
                color=arcade.color.WARM_BLACK,
                font_size=10,
                width=300,
                align='right'
            )

    def update_players(self) -> None:
        start_x = 100
        pad = 30
        for index, player in enumerate(list(self.game.network_handler.identifier_to_player_dict.values())):
            if player != self.game.player:
                table = Shapes.WordTable(
                    x=start_x + index*pad,
                    y=SCREEN_HEIGHT - 400,
                    pad=25,
                    word_table=player.word_table,
                    match_table=player.match_table
                )
                self.player_word_tables.append(table)

    def on_update(self, delta_time) -> None:
        self.client_word_table.word_table = self.game.player.word_table
        self.client_word_table.match_table = self.game.player.match_table
        if len(self.player_word_tables) < len(self.game.network_handler.identifier_to_player_dict.values()):
            self.update_players()
        self.game.update()
        # print(self.won)
        if self.game.network_handler.everyone_finished_the_game() and self.won is not None:
            rank_list = {}
            for player in self.game.network_handler.identifier_to_player_dict.values():
                rank_list[player.identifier] = player.username, player.starttime - player.endtime
            
            game_over_view = GameOverView()
            game_over_view.setup(self.game.player.identifier, rank_list, self.game)
            self.window.show_view(game_over_view)
            

    def on_key_release(self, key, key_modifiers) -> None:
        """
        Called whenever the user lets off a previously pressed key.
        """

        # get the char from the key code, as it uses 97..122 for a..z (the same as ascii)
        if key in range(ord('a'), ord('z')+1):
            char = chr(key)
            try:
                if self.game.network_handler.game_has_started:
                    won = self.game.add_char(char)
                    if won:
                        self.won = True
            except OutOfWordTableBounds:
                self.won = False
            except AlreadyWonError:
                print(f"player already won")

        elif key == arcade.key.BACKSPACE:
            try:
                self.game.remove_char()
            except OutOfWordTableBounds:
                print(f"prob. too empty")
        elif key == arcade.key.ENTER:
            print(f"{self.game.network_handler.game_has_started=}")

    def on_mouse_motion(self, x, y, delta_x, delta_y) -> None:
        """
        Called whenever the mouse moves.
        """
        self.ready_button.is_mouse_hovering(x, y)

    def on_mouse_release(self, x, y, button, key_modifiers) -> None:
        """
        Called when a user releases a mouse button.
        """
        if self.ready_button.hover:
            if not self.game.player.is_ready:
                self.game.ready()
                self.ready_button.normal_color = arcade.color.APPLE_GREEN
                self.ready_button.hover_color = arcade.color.AVOCADO
                self.ready_button.text_lable.text = "READY"
            else:
                self.game.unready()
                self.ready_button.normal_color = arcade.color.RUFOUS
                self.ready_button.hover_color = arcade.color.OU_CRIMSON_RED
                self.ready_button.text_lable.text = "NOT READY"
            self.ready_button.color = self.ready_button.hover_color

class GameOverView(arcade.View):

    def __init__(self) -> None:
        super().__init__()
        self.close_delay = 5

    def setup(self, client_identifier: int, rank_list: dict[int, tuple[str, float]], game) -> None:
        print("setup..")
        # TODO display ranked list and the solution word
        self.rank_lable = Shapes.Text(
            x=SCREEN_WIDTH/2,
            y=SCREEN_HEIGHT/2,
            color=arcade.color.BLACK,
            font_size=20,
            text = rank_list
        )
        self.game = game

    def on_update(self, delta_time) -> None:
        # FIXME doesn't get triggered by a full word_table
        if self.close_delay < 0 and self.close_delay > - 100:
            self.game.close()
            self.close_delay = -110
        self.close_delay -= delta_time

    def on_draw(self) -> None:
        self.clear()
        self.rank_lable.draw()

def main() -> None:
    """ Main function """

    window = arcade.Window(
        width = SCREEN_WIDTH,
        height = SCREEN_HEIGHT, 
        title = 'Wordle Clone',
        fullscreen = False, 
        resizable = False,
        update_rate = 1 / 60, 
        antialiasing = True
    )
    
    start_view = StartView()
    window.show_view(start_view)
    start_view.setup()
    arcade.run()

if __name__ == "__main__":
    main()