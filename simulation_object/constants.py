import pygame

PLAYER_DEATH_SECONDS = 3
PLAYER_HEALTH = 100

PLAYER_AIM_LENGTH = 100

PLAYER_DEATH_COLOR = pygame.color.THECOLORS['red'] # type: ignore
# TODO this is fucked
PLAYER_COLORS = [(r, g, b, a) for r, g, b, a in pygame.color.THECOLORS.values() if r + g + b > 300 and abs(r - g) + abs(g - b) + abs(b - r) > 50 and (r, g, b, a) != PLAYER_DEATH_COLOR] # type: ignore

