import pygame

class ClientTextElement:
    def __init__(self, screen, x, y, width, height, font):
        self.screen = screen
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
    def render(self):
        raise NotImplementedError