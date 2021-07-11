import pygame
from network import FragNetwork
from player import ClientPlayer
from game_engine_constants import ARROW_MOVEMENT_KEYS, WASD_MOVEMENT_KEYS, WIDTH, HEIGHT, FPS, GAME_TITLE, SCREEN_CENTER_POINT, ORIGIN, BUF_SIZE
from converters import str_to_player_data_no_dt
from threading import Thread, Lock
import map_loading
import pickle
import time
import random
import logging

## Initialize network
fn = FragNetwork()
player_id = fn.connect()

player_id = int(player_id)

print(f"You are player {player_id}")

## initialize pygame and create window
pygame.init()
pygame.mixer.init()  ## For sound
screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption(GAME_TITLE)
clock = pygame.time.Clock()     ## For syncing the FPS

## group all the sprites together for ease of update
all_sprites = pygame.sprite.Group()



# START MAP LOAD TODO server should only send the name of the map and then we load it in

walls = map_loading.construct_walls(map_loading.get_pixels("maps/m1_no_layers.png"))
#walls = [(4, 3), (4,4), (4, 5), (5,5), (6,5), (7,5), (8,5), (4, 6)]
#walls = [(5,5)]
#walls = [map_loading.SquareWall(x, y, pygame.color.THECOLORS['green'], 100) for x, y in walls]
bounding_walls = map_loading.construct_bounding_walls(map_loading.get_pixels("maps/m1_no_layers.png"))
#bounding_walls = walls

map_loading.classify_bounding_walls(bounding_walls, "maps/m1_no_layers.png")

# END MAP LOAD



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
        logging.info("GAME STATE RECEIVED: ", game_state)

        for player_state in game_state:
            logging.info("player state", player_state)
            player_id, x, y, rotation_angle = str_to_player_data_no_dt(player_state)

            if player_id not in id_to_player:
                id_to_player[player_id] = ClientPlayer((x,y), 50, 50, (50, 255, 5),ARROW_MOVEMENT_KEYS, player_id, fn)
                all_sprites.add(id_to_player[player_id])
            else:
                logging.info(id_to_player, player_id)
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

    for wall in walls:
        pygame.draw.rect(screen, wall.color, wall.rect.move(camera_v.x, camera_v.y))

    for b_wall in bounding_walls:
        pygame.draw.rect(screen, b_wall.color, b_wall.rect.move(camera_v.x, camera_v.y))

    #all_sprites.draw(screen)

    # TODO it might be easier to always just draw a circle in the middle of the screen
    # instead fo actually simulating its movement that way it seems more solid
    for sprite in all_sprites:
        # Add the player's camera offset to the coords of all sprites.
        screen.blit(sprite.image, sprite.rect.topleft + camera_v)

    ########################

    ### Put code here

    # check if there are any updates

    ########################

    ## Done after drawing everything to the screen
    pygame.display.flip()       

pygame.quit()
