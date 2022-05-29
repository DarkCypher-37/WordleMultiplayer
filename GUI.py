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

    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.AMAZON)

        self.splash_text = None
        self.create_button = None
        self.join_button = None

    def setup(self):
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

    def on_draw(self):
        self.clear()

        self.splash_text.draw()
        
        self.join_button.draw()
        self.create_button.draw()


    def on_update(self, delta_time):
        pass

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.join_button.is_mouse_hovering(x, y)
        self.create_button.is_mouse_hovering(x, y)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if self.join_button.hover:
            enter_port_view = EnterPortView()
            enter_port_view.setup()
            self.window.show_view(enter_port_view)
        elif self.create_button.hover:
            # enter_username_view = EnterUsernameView()
            # enter_username_view.setup()
            # self.window.show_view(enter_username_view)
            
            game_view = GameView()
            game_view.setup()
            self.window.show_view(game_view)


class EnterPortView(arcade.View):
    """
    ENTER THE IP, PORT, GAMEKEY.
    """

    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.AMAZON)
        self.input_port = None
        self.input_ip = None
        self.cursor_time = 0
        self.cursor_time_threshold = 0.3
        self.current_active_input = None
        self.inputs = []

    def setup(self):

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

    def loop_active_input(self):
        if self.current_active_input >= len(self.inputs)-1:
            self.inputs[self.current_active_input].set_inactive()
            self.current_active_input = 0
            self.inputs[self.current_active_input].set_active()
        else:
            self.inputs[self.current_active_input].set_inactive()
            self.current_active_input += 1
            self.inputs[self.current_active_input].set_active()

    def next_active_input(self):
        if self.current_active_input >= len(self.inputs)-1:
            self.validate_inputs()
        else:
            self.inputs[self.current_active_input].set_inactive()
            self.current_active_input += 1
            self.inputs[self.current_active_input].set_active()

    def on_draw(self):
        self.clear()
        for element in self.inputs:
            element.draw()

    def on_update(self, delta_time):
        self.cursor_time += delta_time
        if self.cursor_time >= self.cursor_time_threshold:
            self.inputs[self.current_active_input].blink()
            self.cursor_time = 0

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        for element in self.inputs:
            element.is_mouse_hovering(x, y)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        for index, element in enumerate(self.inputs):
            if element.hover:
                self.inputs[self.current_active_input].set_inactive()
                self.current_active_input = index
                self.inputs[self.current_active_input].set_active()

    def validate_inputs(self):
            succes = True
            try:
                ip = self.input_ip.input
                _ = int(ip.replace('.', ''))
            except:
                succes = False
                self.input_ip.illegal_input()

            try:
                port = int(self.input_port.input)
            except:
                succes = False
                self.input_port.illegal_input()

            try:
                gamekey = int(self.input_gamekey.input, 16)
            except:
                succes = False
                self.input_gamekey.illegal_input()

            if succes:
                # enter_username_view = EnterUsernameView()
                # enter_username_view.setup(port)
                # self.window.show_view(enter_username_view)
                        
                game_view = GameView()
                game_view.setup(port=port)
                self.window.show_view(game_view)

    def on_key_press(self, symbol: int, modifiers: int):
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


    def setup(self, port=0):
        print("pls enter username")

        game_view = GameView()
        game_view.setup(port=port)
        self.window.show_view(game_view)

    def on_draw(self):
        self.clear()

    def on_update(self, delta_time: float):
        pass


class GameView(arcade.View):
    """
    THE GAMEVIEW.
    """

    def __init__(self):

        super().__init__()

        arcade.set_background_color(arcade.color.AMAZON)

        self.game = None

    def setup(self, port = 0):
        """ Set up the game variables. Call to re-start the game. """
        self.debug_port = port
        self.game = MultiplayerGame()

    def close(self):
        super().close()
        self.game.close()
        print("closed")

    def on_draw(self):
        """
        Render the screen.
        """
        self.clear()

        if not self.game.network_handler.has_joined_a_network:
            arcade.draw_rectangle_filled(
                center_x=0 + 40,
                center_y=SCREEN_HEIGHT-40,
                width=40,
                height=40,
                color=arcade.color.DARK_GOLDENROD
                # color=arcade.color_from_hex_string("#")
            )

            arcade.draw_rectangle_filled(
                center_x=0 + 100,
                center_y=SCREEN_HEIGHT-40,
                width=40,
                height=40,
                color=arcade.color.DARK_CYAN
                # color=arcade.color_from_hex_string("#")
            )

        self.draw_info(
            f"HOST: {self.game.network_handler.host}",
            f"PORT: {self.game.network_handler.port}",
            f"players: {len(self.game.network_handler.identifier_to_player_dict)}",
            f"solution word: {self.game.network_handler.solution_word}",
            f"Gamekey: {self.game.network_handler.gamekey}"
        )

        self.draw_table(
            start_x=SCREEN_WIDTH/2 - (2*50),
            start_y=SCREEN_HEIGHT - 100,
            pad=50,
            word_table=self.game.player.word_table,
            match_table=self.game.player.match_table
        )

        # TODO display a table for other players
        start_x = 100
        pad = 30
        for index, player in enumerate(list(self.game.network_handler.identifier_to_player_dict.values())):
            if player != self.game.player:
                self.draw_table(
                    start_x=start_x + index*pad,
                    start_y=SCREEN_HEIGHT - 400,
                    pad=25,
                    word_table=player.word_table,
                    match_table=player.match_table
                )

    def draw_info(self, *args):

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


    def draw_table(self, start_x, start_y, pad, word_table, match_table: list[list[CharStatus]]):

        colors = [arcade.color.ASH_GREY, arcade.color.YELLOW, arcade.color.GREEN, arcade.color.GRAY]

        for word_index, word in enumerate(word_table):
            for char_index, char in enumerate(word):
                self.draw_char(
                    x=start_x + char_index*pad,
                    y=start_y - word_index*pad,
                    char=char,
                    color=colors[match_table[word_index][char_index].value],
                    pad=pad
                )

    def draw_char(self, x, y, char, color, pad) -> None:

        if char is None:
            char = '▢'

        if len(char) != 1:
            raise CharTooLongError(f"Char has to be length 1, but is: {char!r}")

        arcade.draw_rectangle_filled(
            center_x=x,
            center_y=y,
            width=pad*4/5,
            height=pad*4/5,
            color=color
            # color=arcade.color_from_hex_string("#88888888")
        )

        arcade.draw_text(
            text=char,
            start_x=x,
            start_y=y,
            color=arcade.color.BLACK,
            font_size=pad*2/4,
            anchor_x='center',
            anchor_y='center',
        )


    def on_update(self, delta_time):
        self.game.update()

    def on_key_press(self, key, key_modifiers):
        pass

    def on_key_release(self, key, key_modifiers):
        """
        Called whenever the user lets off a previously pressed key.
        """

        # get the char from the key code, as it uses 97..122 for a..z (the same as ascii)
        if key in range(ord('a'), ord('z')+1):
            char = chr(key)
            try:
                self.game.add_char(char)
            except OutOfWordTableBounds:
                print(f"prob. TOO FULL")
            except AlreadyWonError:
                print(f"player already won")

        elif key == arcade.key.BACKSPACE:
            try:
                self.game.remove_char()
            except OutOfWordTableBounds:
                print(f"prob. too empty")
        elif key == arcade.key.ENTER:
            pass

    def on_mouse_motion(self, x, y, delta_x, delta_y):
        """
        Called whenever the mouse moves.
        """
        pass

    def on_mouse_press(self, x, y, button, key_modifiers):
        """
        Called when the user presses a mouse button.
        """
        
        # center_x=0 + 40,
        # center_y=SCREEN_HEIGHT-40,
        # width=40,
        # height=40,
        if not self.game.network_handler.has_joined_a_network:
            if x < 0 + 40 + 20 and x > 0 + 40 - 20 and \
                y < SCREEN_HEIGHT-40 +20 and y > SCREEN_HEIGHT-40 - 20:

                self.game.create_network()

            if x < 0 + 100 + 20 and x > 0 + 100 - 20 and \
                y < SCREEN_HEIGHT-40 +20 and y > SCREEN_HEIGHT-40 - 20:

                self.game.join_network(self.debug_port)

    def on_mouse_release(self, x, y, button, key_modifiers):
        """
        Called when a user releases a mouse button.
        """
        pass


def main():
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