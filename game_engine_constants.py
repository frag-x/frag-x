import pygame

WIDTH = 750
HEIGHT = 750
FPS = 60
SERVER_TICK_RATE_HZ = 60

SCREEN_CENTER_POINT = (WIDTH/2, HEIGHT/2)
ORIGIN = (0,0)

GAME_TITLE = "frag-x"

ARROW_MOVEMENT_KEYS = [pygame.K_LEFT, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN]
WASD_MOVEMENT_KEYS = [pygame.K_a, pygame.K_w, pygame.K_d, pygame.K_s]

# Weapon keys maps onto the weapons in this order: # TODO make this a dictionary
# rocket launcher, rail gun
WEAPON_KEYS = [pygame.K_c, pygame.K_x] 

MAX_SPEED = 4000

BUF_SIZE = 2 ** 12 

RUNNING_LOCALLY = False
RUNNING_ON_LAN = False
#RUNNING_LOCALLY = False

CLIENT_GAME_SIMULATION = True
CLIENT_SERVER_MANAGER = None # what is this???
MOCK_SERVER_QUEUE = None # this will be set if CLIENT_GAME_SIMULATION IS TRUE

#DEV_MAP = "maps/simple_map.png"
DEV_MAP = "maps/m1_no_layers.png"
TILE_SIZE = 32
MAP_BASE_DIM_X = 160
MAP_BASE_DIM_Y = 90

DEBUG_RADIUS = 10

MAP_DIM_X = MAP_BASE_DIM_X * TILE_SIZE
MAP_DIM_Y = MAP_BASE_DIM_Y * TILE_SIZE


#import socket
#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#s.connect(("8.8.8.8", 80))
#LOCAL_IP = s.getsockname()[0]
LOCAL_IP = "localhost"
#s.close()

# TODO LAN: https://stackoverflow.com/questions/20695493/python-connect-via-lan
#REMOTE_IP = "cuppajoeman.com"
REMOTE_IP = "168.100.233.209"
LAN_IP = "192.168.2.24"
#LAN_IP = "192.168.2.21"
#REMOTE_IP = socket.gethostname()

#PORT = 50000
PORT = 49999

