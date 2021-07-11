import map_loading
import math
from fractions import Fraction
import pygame
import collisions
from player import Player

WIDTH = 1366
HEIGHT = 786
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
#walls = [(5,5)]
#walls = [map_loading.SquareWall(x, y, pygame.color.THECOLORS['green'], 100) for x, y in walls]
bounding_walls = map_loading.construct_bounding_walls(map_loading.get_pixels("../maps/m1_no_layers.png"))
#bounding_walls = walls

map_loading.classify_bounding_walls(bounding_walls, "../maps/m1_no_layers.png")

curr_player = Player((WIDTH/2, HEIGHT/2), 50, 50, (50, 120, 255), [pygame.K_a, pygame.K_w, pygame.K_d, pygame.K_s], WIDTH, HEIGHT)
p1 = Player((WIDTH/2, HEIGHT/2), 50, 50, (50, 120, 255), [pygame.K_LEFT, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN], WIDTH, HEIGHT)

all_sprites.add(curr_player)
all_sprites.add(p1)

players = [p1, curr_player]

pygame.font.init() # you have to call this at the start, 
                   # if you want to use this module.
myfont = pygame.font.SysFont(pygame.font.get_default_font(), 30)

## Game loop
running = True
ticks_from_previous_iteration = 0
prev_list = []
center = pygame.math.Vector2(WIDTH/2, HEIGHT/2)
hits = []
closest_hit = None

# Initialization
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)
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



    t = pygame.time.get_ticks()
    # deltaTime in seconds.
    delta_time = (t - ticks_from_previous_iteration ) / 1000.0
    ticks_from_previous_iteration = t


    all_sprites.update(events, delta_time)

    mouse_pressed = pygame.mouse.get_pressed()[0]
    if mouse_pressed:
        closest_hit, closest_entity = curr_player.weapon.get_all_intersecting_objects(bounding_walls, [p1])
        if type(closest_entity) is Player:
            hit_v = pygame.math.Vector2(0,0)
            deg = curr_player.rotation_angle * 360/math.tau
            hit_v.from_polar((curr_player.weapon.power, deg))
            closest_entity.velocity += hit_v

    if curr_player.velocity.x != 0 or curr_player.velocity.y != 0:
        vel_display_vector = curr_player.velocity/ 2
    else:
        vel_display_vector = curr_player.velocity
    #pygame.draw.line(screen, (255, 0, 0), curr_player.pos, curr_player.pos + vel_display_vector, 3)

    #pygame.draw.polygon(screen, (255, 255, 255), ((), (0, 200), (200, 200), (200, 300), (300, 150), (200, 0), (200, 100)))

    #for b_wall in bounding_walls[:1]:
    #    b_wall.color = (255, 0, 0)
    for b_wall in bounding_walls:
        for p in players:

            colliding, closest_v = collisions.colliding_and_closest(p, b_wall)
            #pygame.draw.line(screen, (255, 255, 255), p.pos, closest_v)
            if colliding:
                #print(f"player coliding at {p.pos.x} {p.pos.y}")
                #collisions.simulate_collision(p, b_wall, closest_v)
                collisions.simulate_collision_v2(p, b_wall, closest_v)


    camera_v = center - curr_player.pos

    if mouse_pressed:
        if closest_hit:
            pygame.draw.line(screen, (255, 0, 255), curr_player.pos + camera_v, curr_player.pos + closest_hit + camera_v , 3)

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


    # display info

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

    ########################

    ## Done after drawing everything to the screen
    pygame.display.flip()       

pygame.quit()
