import enum

import pygame


class JustificationSetting(enum.Enum):
    LEFT_JUSTIFIED = enum.auto()
    RIGHT_JUSTIFIED = enum.auto()
    CENTER_JUSTIFIED = enum.auto()


class TextRectException:
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message


class ChatBox:
    """
    A chatbox represents an area which is to be filled with other surfaces from the bottom to the top.

    When it is at maximum capacity we remove the oldest item from the chatbox.

    After a certian amount of time (measured in seconds) messages fade away and are removed from the chat
    """

    def __init__(self, screen, x, y, width, height, font, time_on_screen=10):
        self.screen = screen
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.time_on_screen = time_on_screen
        self.message_to_time = {}
        self.messages = []
        self.curr_height = 0

    def add_message(self, message: str) -> None:
        # TODO check if enough space if we were to add it in
        # message_surface = MultiLineSurface(message, self.font, self.rect, )

        message_surface = self.font.render(message, False, pygame.Color("white"))
        # if there is enough space then do this
        message_height = message_surface.get_height()
        if self.curr_height + message_height <= self.rect.height:
            self.curr_height += message_height
            self.messages.append(message_surface)
            self.message_to_time[message_surface] = 0
        # otherwise there is not enough space, so we
        # remove one element and try addining the message again?
        # recursively? what if it's still too big, well then their message is too long
        # we will have an upper bound on message height so we can figure that out later

    def draw_messages(self):
        """This method takes all the messages and draws them from the bottom to the top"""
        accumulated_height = 0
        for message in self.messages:
            accumulated_height += message.get_height()
            x = self.rect.x
            y = self.rect.y + self.rect.height - accumulated_height
            text_pos = (x, y)
            self.screen.blit(message, text_pos)

    def update_message_times(self, time_since_last_frame: float) -> None:
        """Updates the amount of time that messages have been shown for, and deletes any messages that have been there for too long"""
        to_be_removed = []
        for message, time in self.message_to_time.items():
            self.message_to_time[message] = time + time_since_last_frame
            if self.message_to_time[message] / 1000 > self.time_on_screen:
                to_be_removed.append(message)

        for message in to_be_removed:
            del self.message_to_time[message]
            self.messages.remove(message)


class MultiLineSurface:  # TODO don't worry about this until later on
    def __init__(self, string, font, rect, font_color, bg_color, justification=0):
        self.string = string
        self.font = font
        self.rect = rect  # TODO it only needs to know about the width
        self.font_color = font_color
        self.bg_color = bg_color
        self.justification = justification
        self.surface = self.construct_surface()

    def construct_surface(self):
        """Returns a surface containing the passed text string, reformatted
        to fit within the given rect, word-wrapping as necessary. The text
        will be anti-aliased.

        Parameters
        ----------
        string - the text you wish to render Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam iaculis magna vel sollicitudin ultricies. Phasellus leo sapien, consequat sed nulla quis, consequat laoreet metus. Duis maximus id libero pellentesque malesuada. Donec ac suscipit augue, et pellentesque libero. Etiam eu vestibulum velit, vitae laoreet orci. Aliquam vehicula tellus elit, et vestibulum quam condimentum eget. Mauris tincidunt fermentum dolor vitae elementum. Pellentesque maximus magna at pellentesque posuere. . \n begins a new line.
        font - a Font object
        rect - a rect style giving the size of the surface requested.
        fontColour - a three-byte tuple of the rgb value of the
                 text color. ex (0, 0, 0) = BLACK
        BGColour - a three-byte tuple of the rgb value of the surface.
        justification - 0 (default) left-justified
                    1 horizontally centered
                    2 right-justified

        Returns
        -------
        Success - a surface object with the text rendered onto it.
        Failure - raises a TextRectException if the text won't fit onto the surface.
        """
        final_lines = []
        # splitlines doesn't make sense here. we just give it a long string right?
        # we are going to give a textlimit for messages and additionally not allow there to be newlines,
        # due to this we will just have to iterate through the words and just keep that logic
        requested_lines = self.string.splitlines()
        # Create a series of lines that will fit on the provided
        # rectangle.
        for requested_line in requested_lines:
            if self.font.size(requested_line)[0] > self.rect.width:  # overfull
                words = requested_line.split(" ")
                # if any of our words are too long to fit, return.
                # TODO add line break then
                for word in words:
                    if self.font.size(word)[0] >= self.rect.width:
                        raise TextRectException(
                            "The word "
                            + word
                            + " is too long to fit in the rect passed."
                        )
                # Start a new line
                accumulated_line = ""
                for word in words:
                    test_line = accumulated_line + word + " "
                    # Build the line while the words fit.
                    if self.font.size(test_line)[0] < self.rect.width:
                        accumulated_line = test_line
                    else:
                        # add current line and reset
                        final_lines.append(accumulated_line)
                        accumulated_line = word + " "
                final_lines.append(accumulated_line)
            else:
                final_lines.append(requested_line)

        # Let's try to write the text out on the surface.
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA, 32)
        accumulated_height = 0

        for line in final_lines:
            if accumulated_height + self.font.size(line)[1] >= self.rect.height:
                raise TextRectException(
                    "Once word-wrapped, the text string was too tall to fit in the rect."
                )
            if line != "":
                temp_surface = self.font.render(line, 1, self.font_color)
            if self.justification == 0:
                surface.blit(temp_surface, (0, accumulated_height))
            elif self.justification == 1:
                surface.blit(
                    temp_surface,
                    (
                        (self.rect.width - temp_surface.get_width()) / 2,
                        accumulated_height,
                    ),
                )
            elif self.justification == 2:
                surface.blit(
                    temp_surface,
                    (self.rect.width - temp_surface.get_width(), accumulated_height),
                )
            else:
                raise TextRectException(
                    "Invalid justification argument: " + str(self.justification)
                )
            accumulated_height += self.font.size(line)[1]
        return surface
