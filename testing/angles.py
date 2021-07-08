import pygame
import math

WIDTH = 800
HEIGHT = 800
FPS = 60


## initialize pygame and create window
pygame.init()
pygame.mixer.init()  ## For sound
screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Name")
clock = pygame.time.Clock()     ## For syncing the FPS


## group all the sprites together for ease of update
all_sprites = pygame.sprite.Group()

## Game loop
running = True
while running:

    #1 Process input/events
    clock.tick(FPS)     ## will make the loop run at the same speed all the time
    for event in pygame.event.get():        # gets all the events which have occured till now and keeps tab of them.
        ## listening for the the X button at the top
        if event.type == pygame.QUIT:
            running = False


    #2 Update
    all_sprites.update()
    v = pygame.math.Vector2(1,0) * 50

    center = pygame.math.Vector2(WIDTH/2, HEIGHT/2)

    pygame.draw.line(screen, (255, 0, 0), center, center + v)
    pygame.draw.line(screen, (0, 255, 0), center, center + v.rotate_rad(math.tau/8))
    pygame.draw.line(screen, (0, 0, 255), center, center + v.rotate_rad(-math.tau/8))


    #3 Draw/render
    #screen.fill(pygame.color.THECOLORS['black'])

    all_sprites.draw(screen)
    ########################

    ### Put code here

    ########################

    ## Done after drawing everything to the screen
    pygame.display.flip()       

pygame.quit()
