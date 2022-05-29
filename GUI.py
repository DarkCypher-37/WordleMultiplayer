import arcade
from Errors import AlreadyWonError, CharTooLongError, OutOfWordTableBounds
from Game import MultiplayerGame
from WordList import CharStatus

from color import *

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

class GUI(arcade.Window):
    """
    THE GUI.
    """

    def __init__(self, 
            width: int = 800,
            height: int = 600, 
            title: str = 'Wordle Clone',
            fullscreen: bool = False, 
            resizable: bool = False,
            update_rate = 1 / 60, 
            antialiasing: bool = True
        ):

        super().__init__(width, height, title, fullscreen, resizable, update_rate, antialiasing)

        arcade.set_background_color(arcade.color.AMAZON)

        self.game = None

    def setup(self):
        """ Set up the game variables. Call to re-start the game. """
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
            start_x=0 - (5 * 50)/2,
            start_y=SCREEN_HEIGHT - 100,
            y_pad=50,
            x_pad=50,
            word_table=self.game.player.word_table,
            match_table=self.game.player.match_table
        )

        # TODO display a table for other players
        # for index, player in self.game.player_list[1:]:
        #     if 

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


    def draw_table(self, start_x, start_y, y_pad, x_pad, word_table, match_table: list[list[CharStatus]]):

        colors = [arcade.color.BLACK, arcade.color.YELLOW, arcade.color.GREEN, arcade.color.RED]

        for word_index, word in enumerate(word_table):
            for char_index, char in enumerate(word):
                self.draw_char(
                    x=start_x + char_index*x_pad,
                    y=start_y - y_pad*word_index,
                    char=char,
                    color=colors[match_table[word_index][char_index].value]
                )

    def draw_char(self, x, y, char, color) -> None:

        if char is None:
            char = '▢'

        if len(char) != 1:
            raise CharTooLongError(f"Char has to be length 1, but is: {char!r}")

        arcade.draw_text(
            text=char,
            start_x=x,
            start_y=y,
            color=color,
            font_size=40,
            width=SCREEN_WIDTH,
            align='center'
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
            self.game.remove_char()
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

                self.game.join_network()

    def on_mouse_release(self, x, y, button, key_modifiers):
        """
        Called when a user releases a mouse button.
        """
        pass


def main():
    """ Main function """
    gui = GUI(SCREEN_WIDTH, SCREEN_HEIGHT)
    gui.setup()
    arcade.run()

if __name__ == "__main__":
    main()