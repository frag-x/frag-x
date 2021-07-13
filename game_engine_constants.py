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


import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
LOCAL_IP = s.getsockname()[0]
s.close()

# TODO LAN: https://stackoverflow.com/questions/20695493/python-connect-via-lan
#REMOTE_IP = "cuppajoeman.com"
REMOTE_IP = "168.100.233.209"
#REMOTE_IP = socket.gethostname()

PORT = 50000

