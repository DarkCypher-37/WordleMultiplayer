import arcade
from Game import MultiplayerGame

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
        print(f"{self.game.network_handler.client_identifier=}")

    def on_draw(self):
        """
        Render the screen.
        """
        self.clear()

        text = str(self.game.player)
        arcade.draw_text(text, 0, SCREEN_HEIGHT-100, arcade.color.BLACK, 40, SCREEN_WIDTH, align='center')

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
            self.game.add_char(char)

    def on_mouse_motion(self, x, y, delta_x, delta_y):
        """
        Called whenever the mouse moves.
        """
        pass

    def on_mouse_press(self, x, y, button, key_modifiers):
        """
        Called when the user presses a mouse button.
        """
        pass

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