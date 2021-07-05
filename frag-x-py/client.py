import pygame
from network import FragNetwork
from player import ClientPlayer
from game_engine_constants import ARROW_MOVEMENT_KEYS, WASD_MOVEMENT_KEYS, WIDTH, HEIGHT, FPS, GAME_TITLE, SCREEN_CENTER_POINT, ORIGIN, BUF_SIZE
from converters import str_to_player_data_no_dt
from threading import Thread, Lock
import pickle
import time
import random

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

# initially we don't know what our id is we only get it back from the server so we need to do 
# a type of responce thing..
rand_color = random.choices(range(256), k=3)
curr_player = ClientPlayer(ORIGIN, 50, 50, rand_color,ARROW_MOVEMENT_KEYS, WIDTH, HEIGHT, player_id, fn)

all_sprites.add(curr_player)

id_to_player = {}

id_to_player[player_id] = curr_player

def game_state_watcher():
    # CONNECT LOOP
    while True:
        print("watching for game state")
        raw_data = fn.client.recv(BUF_SIZE)
        game_state = pickle.loads(raw_data)
        print("GAME STATE RECEIVED: ", game_state)

        for player_state in game_state:
            print("player state", player_state)
            player_id, x, y, rotation_angle = str_to_player_data_no_dt(player_state)

            if player_id not in id_to_player:
                id_to_player[player_id] = ClientPlayer((x,y), 50, 50, (50, 255, 5),ARROW_MOVEMENT_KEYS, WIDTH, HEIGHT, player_id, fn)
                all_sprites.add(id_to_player[player_id])
            else:
                print(id_to_player, player_id)
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

    all_sprites.draw(screen)

    ########################

    ### Put code here

    # check if there are any updates

    ########################

    ## Done after drawing everything to the screen
    pygame.display.flip()       

pygame.quit()
