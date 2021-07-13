import pygame
from network import FragNetwork
from player import ClientPlayer
from game_engine_constants import ARROW_MOVEMENT_KEYS, WASD_MOVEMENT_KEYS, WIDTH, HEIGHT, FPS, GAME_TITLE, SCREEN_CENTER_POINT, ORIGIN, BUF_SIZE, DEV_MAP
from converters import str_to_player_data_no_dt
from threading import Thread, Lock
import map_loading
import pickle
import time
import random
import logging
from fractions import Fraction
import math
#logging.basicConfig(level=logging.INFO)

# START MAP LOAD TODO server should only send the name of the map and then we load it in

map_grid = map_loading.MapGrid(map_loading.get_pixels(DEV_MAP))
partitioned_map_grid = map_loading.PartitionedMapGrid(map_loading.get_pixels(DEV_MAP),10, 10)

# END MAP LOAD


## initialize pygame and create window
pygame.init()
pygame.mixer.init()  ## For sound
pygame.font.init() # you have to call this at the start, 
myfont = pygame.font.SysFont(pygame.font.get_default_font(), 30)
screen = pygame.display.set_mode((WIDTH, HEIGHT))


pygame.display.set_caption(GAME_TITLE)
clock = pygame.time.Clock()     ## For syncing the FPS

## group all the sprites together for ease of update
all_sprites = pygame.sprite.Group()


## Initialize network
fn = FragNetwork()
player_id = fn.connect()

player_id = int(player_id)

print(f"You are player {player_id}")


# initially we don't know what our id is we only get it back from the server so we need to do 
# a type of responce thing..
rand_color = random.choices(range(256), k=3)
curr_player = ClientPlayer(SCREEN_CENTER_POINT, 50, 50, rand_color,WASD_MOVEMENT_KEYS, player_id, fn)

all_sprites.add(curr_player)

id_to_player = {}

id_to_player[player_id] = curr_player

def game_state_watcher():
    # CONNECT LOOP
    while True:
        logging.info("watching for game state")
        raw_data = fn.client.recv(BUF_SIZE)
        game_state = pickle.loads(raw_data)
        logging.info(f"GAME STATE RECEIVED: {game_state}")

        for player_state in game_state:
            logging.info(f"player state: {player_state}")
            player_id, x, y, rotation_angle = str_to_player_data_no_dt(player_state)

            if player_id not in id_to_player:
                id_to_player[player_id] = ClientPlayer((x,y), 50, 50, (50, 255, 5),ARROW_MOVEMENT_KEYS, player_id, fn)
                all_sprites.add(id_to_player[player_id])
            else:
                #logging.info(id_to_player, player_id)
                id_to_player[player_id].set_pos(x,y)
                # In real life we can't change their view or they will freak - do it for now
                id_to_player[player_id].rotation_angle = rotation_angle


t = Thread(target=game_state_watcher, args=() )
t.start()

## Game loop
running = True
ticks_from_previous_iteration = 0

# Initialization
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

while running:
    
    #print("running")

    #1 Process input/events
    clock.tick(FPS)     ## will make the loop run at the same speed all the time

    events = pygame.event.get()

    for event in events:        # gets all the events which have occured till now and keeps tab of them.
        ## listening for the the X button at the top
        if event.type == pygame.QUIT:
            running = False

    #2 Update

    t = pygame.time.get_ticks()
    # deltaTime in seconds.
    delta_time = (t - ticks_from_previous_iteration ) / 1000.0
    ticks_from_previous_iteration = t

    #print("update start")

    # Note: This sends the users inputs to the server
    all_sprites.update(events, delta_time)
    curr_player.send_inputs(events, delta_time)

    #print("update end")

    #3 Draw/render
    screen.fill(pygame.color.THECOLORS['black'])


    camera_v = SCREEN_CENTER_POINT - curr_player.pos

    for row in partitioned_map_grid.collision_partitioned_map:
        for partition in row:
            pygame.draw.rect(screen,pygame.color.THECOLORS['gold'] , partition.rect.move(camera_v.x, camera_v.y), width=1)
    
            for wall in partition.walls:
                pygame.draw.rect(screen, wall.color, wall.rect.move(camera_v.x, camera_v.y))

            for b_wall in partition.bounding_walls:
                pygame.draw.rect(screen, b_wall.color, b_wall.rect.move(camera_v.x, camera_v.y))


    #for wall in map_grid.walls:
    #    pygame.draw.rect(screen, wall.color, wall.rect.move(camera_v.x, camera_v.y))

    #for b_wall in map_grid.bounding_walls:
    #    pygame.draw.rect(screen, b_wall.color, b_wall.rect.move(camera_v.x, camera_v.y))

    #all_sprites.draw(screen)

    # TODO it might be easier to always just draw a circle in the middle of the screen
    # instead fo actually simulating its movement that way it seems more solid
    for sprite in all_sprites:
        # Add the player's camera offset to the coords of all sprites.
        screen.blit(sprite.image, sprite.rect.topleft + camera_v)

    # FONTS

    font_color = pygame.color.THECOLORS['brown3']

    speed = myfont.render(str(round(curr_player.velocity.magnitude())), False, font_color)
    pos = myfont.render(str(curr_player.pos), False, font_color)
    aim_angle_frac = Fraction(curr_player.rotation_angle/math.tau).limit_denominator(10)
    angle = myfont.render(str(aim_angle_frac) + "τ", False, font_color)

    screen.blit(speed,(0,0))
    screen.blit(pos,(0,25))
    screen.blit(angle,(0,50))

    ########################

    ### Put code here

    # check if there are any updates

    ########################

    ## Done after drawing everything to the screen
    pygame.display.flip()       

pygame.quit()
