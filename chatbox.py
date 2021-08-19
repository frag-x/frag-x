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
        for message in reversed(self.messages):
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
