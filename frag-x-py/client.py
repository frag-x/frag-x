import pygame
from network import FragNetwork
from player import ClientPlayer
from game_engine_constants import ARROW_MOVEMENT_KEYS, WASD_MOVEMENT_KEYS, WIDTH, HEIGHT, FPS, GAME_TITLE, SCREEN_CENTER_POINT, ORIGIN
from converters import convert_player_data_to_str, convert_str_to_player_data

## Initialize network
fn = FragNetwork()
fn.connect()


## initialize pygame and create window
pygame.init()
pygame.mixer.init()  ## For sound
screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption(GAME_TITLE)
clock = pygame.time.Clock()     ## For syncing the FPS

## group all the sprites together for ease of update
all_sprites = pygame.sprite.Group()

p1 = ClientPlayer(ORIGIN, 50, 50, (50, 255, 5),ARROW_MOVEMENT_KEYS, WIDTH, HEIGHT, fn)
p2 = ClientPlayer(SCREEN_CENTER_POINT, 50, 50, (50, 120, 255), WASD_MOVEMENT_KEYS, WIDTH, HEIGHT, fn)

#all_sprites.add(p1)
all_sprites.add(p2)


## Game loop
running = True
ticks_from_previous_iteration = 0
while running:
    
    print("running")

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

    print("update start")

    # Note: Multiplayer logic occurs in the update method
    all_sprites.update(events, delta_time)

    print("update end")

    #3 Draw/render
    screen.fill(pygame.color.THECOLORS['black'])

    all_sprites.draw(screen)
    ########################

    ### Put code here

    ########################

    ## Done after drawing everything to the screen
    pygame.display.flip()       

pygame.quit()
