import pygame

WIDTH = 1366
HEIGHT = 786
FPS = 60
SERVER_TICK_RATE_HZ = 60

SCREEN_CENTER_POINT = (WIDTH/2, HEIGHT/2)
ORIGIN = (0,0)

GAME_TITLE = "frag-x"

ARROW_MOVEMENT_KEYS = [pygame.K_LEFT, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN]
WASD_MOVEMENT_KEYS = [pygame.K_a, pygame.K_w, pygame.K_d, pygame.K_s]

BUF_SIZE = 2 ** 12 

RUNNING_LOCALLY = True
#RUNNING_LOCALLY = False

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
#REMOTE_IP = socket.gethostname()

#PORT = 50000
PORT = 49999

