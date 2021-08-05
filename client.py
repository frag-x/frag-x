import pygame, queue
from network import FragNetwork
import game_engine_constants
from player import ClientPlayer
from game_engine_constants import (
    ARROW_MOVEMENT_KEYS,
    WASD_MOVEMENT_KEYS,
    WIDTH,
    HEIGHT,
    FPS,
    GAME_TITLE,
    SCREEN_CENTER_POINT,
    ORIGIN,
    BUF_SIZE,
    DEV_MAP,
)
from converters import str_to_player_data_no_dt
from threading import Thread, Lock
import map_loading, dev_constants, managers, client_server_communication, player, game_modes, helpers
import pickle
import time
import random
import logging
from fractions import Fraction
import math

# logging.basicConfig(level=logging.INFO)

# START MAP LOAD TODO server should only send the name of the map and then we load it in

map_grid = map_loading.MapGrid(map_loading.get_pixels(DEV_MAP))
partitioned_map_grid = map_loading.PartitionedMapGrid(
    map_loading.get_pixels(DEV_MAP), 10, 10
)

# END MAP LOAD


## initialize pygame and create window
pygame.init()
pygame.mixer.init()  ## For sound
pygame.font.init()  # you have to call this at the start,
myfont = pygame.font.SysFont(pygame.font.get_default_font(), 30)
if game_engine_constants.FULL_SCREEN:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    (
        game_engine_constants.WIDTH,
        game_engine_constants.HEIGHT,
    ) = pygame.display.get_surface().get_size()
    game_engine_constants.SCREEN_CENTER_POINT = (
        game_engine_constants.WIDTH / 2,
        game_engine_constants.HEIGHT / 2,
    )
else:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

cgm = managers.ClientGameManager(screen, DEV_MAP)

# The client uses the server logic to simulate live reactions
# and uses the servers responce to fix/verify differences
if game_engine_constants.CLIENT_GAME_SIMULATION:
    SGM = managers.ServerGameManager(DEV_MAP, game_modes.FirstToNFrags(1))
    game_engine_constants.MOCK_SERVER_QUEUE = queue.Queue()

dev_constants.CLIENT_VISUAL_DEBUGGING = True
if dev_constants.CLIENT_VISUAL_DEBUGGING:
    dev_constants.SCREEN_FOR_DEBUGGING = screen

pygame.display.set_caption(GAME_TITLE)
clock = pygame.time.Clock()  ## For syncing the FPS

## group all the sprites together for ease of update
# TODO REMOVE THIS AND JUST USE A SET
cgm.all_sprites = pygame.sprite.Group()


## Initialize network
fn = FragNetwork()
player_id = fn.connect()

print(f"You are player {player_id}")

# initially we don't know what our id is we only get it back from the server so we need to do
# a type of responce thing..
spawn = random.choice(partitioned_map_grid.spawns)
rand_color = random.choices(range(256), k=3)
curr_player = ClientPlayer(
    spawn.pos,
    game_engine_constants.TILE_SIZE,
    game_engine_constants.TILE_SIZE,
    rand_color,
    WASD_MOVEMENT_KEYS,
    game_engine_constants.WEAPON_KEYS,
    player_id,
    fn,
)

cgm.all_sprites.add(curr_player)

cgm.id_to_player[player_id] = curr_player

if game_engine_constants.CLIENT_GAME_SIMULATION:
    # "connecting"
    mock_socket = None
    # not using .add_player because that would generate a different id
    SGM.id_to_player[player_id] = player.KillableServerPlayer(
        game_engine_constants.SCREEN_CENTER_POINT, 50, 50, player_id, mock_socket
    )  # for testing out first to n frags
    # SGM.id_to_player[player_id] = player.ServerPlayer(game_engine_constants.SCREEN_CENTER_POINT, 50, 50, player_id, mock_socket)


def mock_server():
    """This function gets run as a thread and simulates what the server does so we can update the players view without waiting for the server responce, when the server responce comes then we can check positions and fix them if required"""
    while True:
        (
            player_id,
            dx,
            dy,
            dm,
            delta_time,
            firing,
            weapon_request,
        ) = game_engine_constants.MOCK_SERVER_QUEUE.get()

        input_message = client_server_communication.InputMessage(
            player_id, dx, dy, dm, delta_time, firing, weapon_request
        )

        SGM.perform_all_server_operations(delta_time, input_message)


def game_state_watcher():
    # CONNECT LOOP
    recv_buffer = b""
    while True:
        if True:
            size_bytes = helpers.recv_exactly(fn.client, 4)
            size = int.from_bytes(size_bytes, "little")
            data = helpers.recv_exactly(fn.client, size)
            message = pickle.loads(data)
            cgm.client_message_parser.run_command_from_message(message)
        else:
            try:
                data = fn.client.recv(BUF_SIZE)

                if not data:
                    # Likely means we've disconnected
                    break
                else:
                    # print(f'Received: {data.decode("utf-8")}')
                    if False:
                        recv_buffer += data

                        if len(recv_buffer) >= 4:
                            message_size = int.from_bytes(recv_buffer[:4], "little")

                            if len(recv_buffer) - 4 >= message_size:
                                message = pickle.loads(
                                    recv_buffer[4 : 4 + message_size]
                                )
                                recv_buffer = recv_buffer[4 + message_size :]

                                # Do stuff with message

                                if dev_constants.DEBUGGING_NETWORK_MESSAGES:
                                    print(
                                        f"GAME STATE RECEIVED: {message}, with size: {len(message)}"
                                    )
                                print(f"GAME STATE RECEIVED: {message}")

                                cgm.client_message_parser.run_command_from_message(
                                    message
                                )
                    else:
                        cgm.client_message_parser.run_command_from_message(
                            pickle.loads(data)
                        )

            except Exception as e:
                print(f"wasn't able to get data because {e}")
                break

        # for player_state in game_state:
        #    logging.info(f"player state: {player_state}")
        #    player_id, x, y, rotation_angle = str_to_player_data_no_dt(player_state)
        #    if player_id not in cgm.id_to_player:
        #        cgm.id_to_player[player_id] = ClientPlayer((x,y), 50, 50, (50, 255, 5),ARROW_MOVEMENT_KEYS, player_id, fn)
        #        cgm.all_sprites.add(cgm.id_to_player[player_id])
        #    else:
        #        #logging.info(cgm.id_to_player, player_id)
        #        # this needs to be locked because if we are doing collisions or hitscan which depends on the position of the player then we can have issues where their position is updated after translating a point with respect to it's original position and then there are no valid
        #        player_data_lock.acquire()
        #        cgm.id_to_player[player_id].set_pos(x,y)
        #        # In real life we can't change their view or they will freak - do it for now
        #        cgm.id_to_player[player_id].rotation_angle = rotation_angle
        #        player_data_lock.release()


t = Thread(target=game_state_watcher, args=())
t.start()

if game_engine_constants.CLIENT_GAME_SIMULATION:
    mock_server_thread = Thread(target=mock_server, args=())
    mock_server_thread.start()

player_data_lock = Lock()

## Game loop
running = True
ticks_from_previous_iteration = 0

# Initialization
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

while running:

    # print("running")

    # 1 Process input/events
    clock.tick(FPS)  ## will make the loop run at the same speed all the time

    events = pygame.event.get()

    for (
        event
    ) in (
        events
    ):  # gets all the events which have occured till now and keeps tab of them.
        ## listening for the the X button at the top
        if event.type == pygame.QUIT:
            running = False

    # 2 Update

    t = pygame.time.get_ticks()
    # deltaTime in seconds.
    delta_time = (t - ticks_from_previous_iteration) / 1000.0
    ticks_from_previous_iteration = t

    # print("update start")

    # Note: This sends the users inputs to the server
    cgm.all_sprites.update(events, delta_time)
    curr_player.send_inputs(events, delta_time)

    # print("update end")

    # 3 Draw/render
    screen.fill(pygame.color.THECOLORS["black"])

    cgm.player_data_lock.acquire()
    for row in partitioned_map_grid.partitioned_map:
        for partition in row:
            pygame.draw.rect(
                screen,
                pygame.color.THECOLORS["gold"],
                partition.rect.move(curr_player.camera_v),
                width=1,
            )

            for wall in partition.walls:
                pygame.draw.rect(
                    screen, wall.color, wall.rect.move(curr_player.camera_v)
                )

            for b_wall in partition.bounding_walls:
                pygame.draw.rect(
                    screen, b_wall.color, b_wall.rect.move(curr_player.camera_v)
                )
    cgm.player_data_lock.release()

    # if dev_constants.CLIENT_VISUAL_DEBUGGING:
    #    for explosion in dev_constants.EXPLOSIONS_FOR_DEBUGGING:
    #        for beam in explosion.beams:
    #            pygame.draw.line(dev_constants.SCREEN_FOR_DEBUGGING, pygame.color.THECOLORS['green'], beam.start_point + curr_player.camera_v, beam.end_point + curr_player.camera_v)

    if dev_constants.DEBUGGING_INTERSECTIONS:
        for hit_v in dev_constants.INTERSECTIONS_FOR_DEBUGGING:
            pygame.draw.circle(
                dev_constants.SCREEN_FOR_DEBUGGING,
                pygame.color.THECOLORS["purple"],
                hit_v + curr_player.camera_v,
                3,
            )

        for partition in dev_constants.INTERSECTED_PARTITIONS_FOR_DEBUGGING:
            pygame.draw.rect(
                screen,
                pygame.color.THECOLORS["blueviolet"],
                partition.rect.move(curr_player.camera_v),
                width=1,
            )

        for point_v in dev_constants.INTERSECTED_PARTITION_PATCH_MARKERS:
            pygame.draw.circle(
                dev_constants.SCREEN_FOR_DEBUGGING,
                pygame.color.THECOLORS["red"],
                point_v + curr_player.camera_v,
                3,
            )

        for point_v in dev_constants.INTERSECTED_PARTITION_SEAMS_FOR_DEBUGGING:
            pygame.draw.circle(
                dev_constants.SCREEN_FOR_DEBUGGING,
                pygame.color.THECOLORS["yellow"],
                point_v + curr_player.camera_v,
                3,
            )

        for beam in dev_constants.BEAMS_FOR_DEBUGGING:
            pygame.draw.line(
                dev_constants.SCREEN_FOR_DEBUGGING,
                pygame.color.THECOLORS["green"],
                beam.start_point + curr_player.camera_v,
                beam.end_point + curr_player.camera_v,
            )

    cgm.draw_projectiles(curr_player.camera_v)
    cgm.draw_beams(curr_player.camera_v)

    firing = int(pygame.mouse.get_pressed()[0])

    # A drawing is based on a single network message from the server.
    # The reason why it looks like we have shifted tiles is that we received a message in the middle, so this needs to be locked.
    # instead fo actually simulating its movement that way it seems more solid
    for sprite in cgm.all_sprites:
        # Add the player's camera offset to the coords of all sprites.
        screen.blit(sprite.image, sprite.rect.topleft + curr_player.camera_v)

    # FONTS

    font_color = pygame.color.THECOLORS["brown3"]

    # speed = myfont.render(
    #    str(round(curr_player.velocity.magnitude())),
    #    False,
    #    font_color,  # TODO this needs to be done client side
    # )
    pos = myfont.render(str(curr_player.pos), False, font_color)
    aim_angle_str = (
        str(9 - math.floor(curr_player.rotation_angle / math.tau * 10)) + "/" + str(10)
    )
    angle = myfont.render(aim_angle_str + "τ", False, font_color)

    # screen.blit(speed, (0, 0))
    screen.blit(pos, (0, 25))
    screen.blit(angle, (0, 50))

    ########################

    ### Put code here

    # check if there are any updates

    ########################

    ## Done after drawing everything to the screen
    pygame.display.flip()

pygame.quit()
