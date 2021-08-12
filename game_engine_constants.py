import pygame

# Primary config variables

DEFAULT_IP = 'localhost'
DEFAULT_PORT = 50000

MAP_PREFIX = 'maps/'
DEFAULT_MAP = 'dm_s2.png'

FULL_SCREEN = False
WIDTH = 750
HEIGHT = 750

FPS = 60
SERVER_TICK_RATE_HZ = 60


# Secondary config variables

SCREEN_CENTER_POINT = (WIDTH / 2, HEIGHT / 2)
ORIGIN = (0, 0)

GAME_TITLE = 'frag-x'

ARROW_MOVEMENT_KEYS = [pygame.K_LEFT, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN]
WASD_MOVEMENT_KEYS = [pygame.K_a, pygame.K_w, pygame.K_d, pygame.K_s]

# Weapon keys maps onto the weapons in this order: # TODO make this a dictionary
# rocket launcher, rail gun
WEAPON_KEYS = [pygame.K_c, pygame.K_x]

MAX_SPEED = 1000

BUF_SIZE = 2 ** 12

TILE_SIZE = 32
PLAYER_RADIUS = TILE_SIZE // 2
MAP_BASE_DIM_X = 160
MAP_BASE_DIM_Y = 90

SPAWN_COLOR = (100, 100, 100)

DEBUG_RADIUS = 10

MAP_DIM_X = MAP_BASE_DIM_X * TILE_SIZE
MAP_DIM_Y = MAP_BASE_DIM_Y * TILE_SIZE
