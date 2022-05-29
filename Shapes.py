from turtle import width
import arcade

class Rectangle():
    
    def __init__(self, x, y, width, height, color, outline=False):
        self.x = x
        self.y = y

        self.width = width
        self.height = height

        self.color = color

        self.outline = outline

    def draw(self):
        if not self.outline:
            arcade.draw_rectangle_filled(
                center_x=self.x,
                center_y=self.y,

                color=self.color,

                width=self.width,
                height=self.height
            )
        else:
            arcade.draw_rectangle_outline(
                center_x=self.x,
                center_y=self.y,

                color=self.color,

                width=self.width,
                height=self.height,
                border_width=5
            )

class Text():
    
    def __init__(self, x, y, color, text, font_size):
        self.x = x
        self.y = y

        self.color = color

        self.text = text
        self.font_size = font_size

    def draw(self):
        arcade.draw_text(
            start_x=self.x,
            start_y=self.y,

            color=self.color,

            text=self.text,
            font_size=self.font_size,

            anchor_x='center',
            anchor_y='center',
        )


class Button(Rectangle):

    def __init__(self, x, y, width, height, color, hover_color, text_color, text, font_size):
        super().__init__(x, y, width, height, color)
        self.text = Text(x, y, text_color, text, font_size)
        self.normal_color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hover = None
    
    def draw(self):
        super().draw()
        self.text.draw()
    
    def is_mouse_hovering(self, mx, my):
        if mx < self.x + self.width/2 and mx > self.x - self.width/2 \
            and my < self.y + self.height/2 and my > self.y - self.height/2:

            self.color = self.hover_color
            self.hover = True
        else:
            self.color = self.normal_color
            self.hover = False

class InputPrompt(Rectangle):

    def __init__(self, x, y, width, height, hover_color, text_color, active_color, font_size, text, input_length, color = arcade.color_from_hex_string("#00000000")):
        super().__init__(x, y, width, height, color, outline=True)

        self.text = text
        self.font_size = font_size

        self.text_lable = Text(x, y, text_color, text + "_" * input_length, font_size)

        self.input = ""
        self.input_length = input_length

        self.normal_color = arcade.color_from_hex_string("#00000000")
        self.hover_color = hover_color
        self.text_color = text_color
        self.active_color = active_color

        self.hover = None
        self.cursor_visible = True
    
    def set_active(self):
        self.text_lable.color = self.active_color

    def set_inactive(self):
        self.text_lable.color = self.text_color

    def draw(self):
        super().draw()
        self.text_lable.draw()
    
    def is_full(self):
        return not bool(self.input_length - len(self.input))

    def blink(self):
        if (self.input_length - len(self.input)) > 0:
            if self.cursor_visible:
                self.text_lable.text = self.text + self.input + "_" * (self.input_length - len(self.input))
            else:
                self.text_lable.text = self.text + self.input + "  " + "_" * (self.input_length - len(self.input) - 1)
            self.cursor_visible = not self.cursor_visible

    def add_input(self, char):
        self.unillegal_input()
        if len(self.input) < self.input_length:
            self.input += char
            self.text_lable.text = self.text + self.input + "_" * (self.input_length - len(self.input))

    def remove_input(self):
        self.unillegal_input()
        if len(self.input) > 0:
            self.input = self.input[:-1]
            self.text_lable.text = self.text + self.input + "_" * (self.input_length - len(self.input))

    def illegal_input(self):
        self.text_lable.color = arcade.color.DARK_RED

    def unillegal_input(self):
        self.text_lable.color = self.active_color
        

    def is_mouse_hovering(self, mx, my):
        if mx < self.x + self.width/2 and mx > self.x - self.width/2 \
            and my < self.y + self.height/2 and my > self.y - self.height/2:

            self.color = self.hover_color
            self.hover = True
        else:
            self.color = self.normal_color
            self.hover = False