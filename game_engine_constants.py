import pygame

FULL_SCREEN = True
WIDTH = 750
HEIGHT = 750

FPS = 60
SERVER_TICK_RATE_HZ = 60

SCREEN_CENTER_POINT = (WIDTH / 2, HEIGHT / 2)
ORIGIN = (0, 0)

GAME_TITLE = "frag-x"

ARROW_MOVEMENT_KEYS = [pygame.K_LEFT, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN]
WASD_MOVEMENT_KEYS = [pygame.K_a, pygame.K_w, pygame.K_d, pygame.K_s]

# Weapon keys maps onto the weapons in this order: # TODO make this a dictionary
# rocket launcher, rail gun
WEAPON_KEYS = [pygame.K_c, pygame.K_x]

# MAX_SPEED = 4000
# MAX_SPEED = 2000
MAX_SPEED = 1000

BUF_SIZE = 2 ** 12

RUNNING_LOCALLY = False
RUNNING_ON_LAN = False
# RUNNING_LOCALLY = False

CLIENT_GAME_SIMULATION = False
CLIENT_SERVER_MANAGER = None  # what is this???
MOCK_SERVER_QUEUE = None  # this will be set if CLIENT_GAME_SIMULATION IS TRUE

# DEV_MAP = "maps/simple_map.png"
# DEV_MAP = "maps/dm_m1.png"
DEV_MAP = "maps/dm_s2.png"  # TODO automatically add the maps folder so we don't have to type /maps
# DEV_MAP = "maps/dm_blank.png"  # TODO automatically add the maps folder so we don't have to type /maps
DM_MAPS = ["maps/dm_m1.png", "maps/dm_s1.png", "maps/dm_s2.png", "maps/dm_blank.png"]
TILE_SIZE = 32
PLAYER_RADIUS = TILE_SIZE // 2
MAP_BASE_DIM_X = 160
MAP_BASE_DIM_Y = 90

SPAWN_COLOR = (100, 100, 100)

DEBUG_RADIUS = 10

MAP_DIM_X = MAP_BASE_DIM_X * TILE_SIZE
MAP_DIM_Y = MAP_BASE_DIM_Y * TILE_SIZE


# import socket
# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# s.connect(("8.8.8.8", 80))
# LOCAL_IP = s.getsockname()[0]
LOCAL_IP = "localhost"
# s.close()

# REMOTE_IP = "cuppajoeman.com"
REMOTE_IP = "168.100.233.209"
# LAN_IP = "192.168.2.24"
LAN_IP = "192.168.0.26"  # gollins house
# LAN_IP = "192.168.2.21"
# REMOTE_IP = socket.gethostname()

# PORT = 50000
PORT = 49999
