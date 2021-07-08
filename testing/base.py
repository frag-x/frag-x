import map_loading
import math
import pygame
import collisions
from player import Player

WIDTH = 1500
HEIGHT = 1000
FPS = 60

## initialize pygame and create window
pygame.init()
pygame.mixer.init()  ## For sound
screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Name")
clock = pygame.time.Clock()     ## For syncing the FPS

## group all the sprites together for ease of update
all_sprites = pygame.sprite.Group()

walls = map_loading.construct_walls(map_loading.get_pixels("../maps/m1_no_layers.png"))
#walls = [(4, 3), (4,4), (4, 5), (5,5), (6,5), (7,5), (8,5), (4, 6)]
#walls = [map_loading.SquareWall(x, y, pygame.color.THECOLORS['green'], 100) for x, y in walls]
bounding_walls = map_loading.construct_bounding_walls(map_loading.get_pixels("../maps/m1_no_layers.png"))
#bounding_walls = walls

map_loading.classify_bounding_walls(bounding_walls, "../maps/m1_no_layers.png")

p2 = Player((WIDTH/2, HEIGHT/2), 50, 50, (50, 120, 255), [pygame.K_a, pygame.K_w, pygame.K_d, pygame.K_s], WIDTH, HEIGHT)

all_sprites.add(p2)

pygame.font.init() # you have to call this at the start, 
                   # if you want to use this module.
myfont = pygame.font.SysFont(pygame.font.get_default_font(), 30)

## Game loop
running = True
ticks_from_previous_iteration = 0
prev_list = []
center = pygame.math.Vector2(WIDTH/2, HEIGHT/2)
while running:

    #1 Process input/events
    clock.tick(FPS)     ## will make the loop run at the same speed all the time
    events = pygame.event.get()
    for event in events:        # gets all the events which have occured till now and keeps tab of them.
        ## listening for the the X button at the top
        if event.type == pygame.QUIT:
            running = False

    #3 Draw/render

    screen.fill(pygame.color.THECOLORS['black'])

    textsurface = myfont.render(str(round(p2.velocity.magnitude())), False, (100, 100, 100))

    screen.blit(textsurface,(0,0))


    t = pygame.time.get_ticks()
    # deltaTime in seconds.
    delta_time = (t - ticks_from_previous_iteration ) / 1000.0
    ticks_from_previous_iteration = t


    all_sprites.update(events, delta_time)

    if p2.velocity.x != 0 or p2.velocity.y != 0:
        vel_display_vector = p2.velocity/ 2
    else:
        vel_display_vector = p2.velocity
    #pygame.draw.line(screen, (255, 0, 0), p2.pos, p2.pos + vel_display_vector, 3)

    #pygame.draw.polygon(screen, (255, 255, 255), ((), (0, 200), (200, 200), (200, 300), (300, 150), (200, 0), (200, 100)))

    #for b_wall in bounding_walls[:1]:
    #    b_wall.color = (255, 0, 0)
    for b_wall in bounding_walls:
        colliding, closest_v = collisions.colliding_and_closest(p2, b_wall)
        #pygame.draw.line(screen, (255, 255, 255), p2.pos, closest_v)
        if colliding:
            print(f"player coliding at {p2.pos.x} {p2.pos.y}")
            #collisions.simulate_collision(p2, b_wall, closest_v)
            collisions.simulate_collision_v2(p2, b_wall, closest_v)
            #p2.pos = p2.previous_pos
            #prev_list.append((p2.pos.x, p2.pos.y))
        else:
            prev_list = []


    camera_v = center - p2.pos

    for wall in walls:
        pygame.draw.rect(screen, wall.color, wall.rect.move(camera_v.x, camera_v.y))

    for b_wall in bounding_walls:
        pygame.draw.rect(screen, b_wall.color, b_wall.rect.move(camera_v.x, camera_v.y))

    #all_sprites.draw(screen)

    for sprite in all_sprites:
        # Add the player's camera offset to the coords of all sprites.
        screen.blit(sprite.image, sprite.rect.topleft + camera_v)

    ########################

    ### Put code here

    ########################

    ## Done after drawing everything to the screen
    pygame.display.flip()       

pygame.quit()
