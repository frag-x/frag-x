import pygame
import pickle
import random
import math
import argparse
import socket
import uuid

from typing import cast, Tuple
from converters import str_to_player_data_no_dt
from threading import Thread, Lock
from fractions import Fraction

import game_engine_constants
import commands
import map_loading
import helpers
from comms import network, message

from simulation_object.player import ClientPlayer
from client_manager import ClientGameManager


def server_listener(
    client_game_manager: ClientGameManager, socket: socket.socket
) -> None:
    while True:
        input_message = cast(message.ServerMessage, network.recv(socket))
        client_game_manager.parse_input_message(input_message)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ip_address",
        "-i",
        type=str,
        default="localhost",
        help="ip to connect to server on",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=game_engine_constants.DEFAULT_PORT,
        help="port to connect to server on",
    )
    parser.add_argument(
        "--map",
        "-m",
        type=str,
        default=game_engine_constants.DEFAULT_MAP,
        help="game map",
    )
    parser.add_argument(
        "--windowed",
        "-w",
        dest="fullscreen",
        action="store_false",
        help="run in windowed mode",
    )
    parser.add_argument(
        "--sensitivity",
        "-s",
        type=float,
        default=game_engine_constants.DEFAULT_SENSITIVITY,
        help="mouse sensitivity",
    )
    parser.set_defaults(fullscreen=True)
    return parser.parse_args()


def initialize_pygame(fullscreen: bool):
    ## initialize pygame and create window
    pygame.init()
    pygame.mixer.init()  ## For sound
    pygame.font.init()  # you have to call this at the start,

    font = pygame.font.SysFont(pygame.font.get_default_font(), 30)

    if fullscreen:
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
        screen = pygame.display.set_mode(
            (game_engine_constants.WIDTH, game_engine_constants.HEIGHT)
        )

    pygame.display.set_caption(game_engine_constants.GAME_TITLE)
    clock = pygame.time.Clock()

    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    return screen, font, clock


def initialize_network(ip_address: str, port: int) -> Tuple[socket.socket, str]:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((ip_address, port))

    join_message = network.recv(server_socket)
    if type(join_message) is message.ServerJoinMessage:
        player_id = join_message.player_id
    else:
        raise message.UnknownMessageTypeError

    print(f"You are player {player_id}")
    return server_socket, player_id


def initialize_player(
    socket: socket.socket, player_id: str, sensitivity: float
) -> ClientPlayer:
    rand_color = random.choices(range(256), k=3)
    return ClientPlayer(
        game_engine_constants.ORIGIN,
        game_engine_constants.TILE_SIZE,
        game_engine_constants.TILE_SIZE,
        rand_color,
        game_engine_constants.WASD_MOVEMENT_KEYS,
        game_engine_constants.WEAPON_KEYS,
        player_id,
        socket,
        sensitivity,
    )


def update(
    client_game_manager: ClientGameManager, player: ClientPlayer, events
) -> None:
    just_started = False

    if not client_game_manager.is_typing:
        if helpers.started_typing(events):  # only check if they pressd when not typing
            client_game_manager.is_typing = True
            just_started = True
    else:
        if helpers.ended_typing_and_do_action(
            events
        ):  # they are typing and then press return
            client_game_manager.is_typing = False
            # DO ACTION
            text = client_game_manager.user_text_box.text
            if commands.is_command(text):
                successful = (
                    client_game_manager.client_command_runner.attempt_run_command(text)
                )
                if successful:
                    print("command went through!")
                else:
                    print("command failed")
            else:
                # then we're dealing with a normal chat message
                text_message = message.PlayerTextMessage(
                    player_id=player.player_id, text=text
                )
                network.send(player.socket, text_message)

            # print(f"sending {client_game_manager.user_text_box.text}")
            client_game_manager.user_text_box.text = ""
        elif helpers.ended_typing_and_do_nothing(events):
            client_game_manager.is_typing = False
            client_game_manager.user_text_box.text = ""

    if client_game_manager.is_typing and not just_started:
        client_game_manager.user_text_box.update(events)

    # Note: This sends the users inputs to the server
    client_game_manager.all_sprites.update()

    player.send_inputs(client_game_manager.is_typing)


def render(
    client_game_manager: ClientGameManager,
    delta_time: float,
    player: ClientPlayer,
    screen,
    font,
) -> None:
    screen.fill(pygame.color.THECOLORS["black"])  # type: ignore

    for row in client_game_manager.partitioned_map_grid.partitioned_map:
        for partition in row:
            pygame.draw.rect(
                screen,
                pygame.color.THECOLORS["gold"],  # type: ignore
                partition.rect.move(player.camera_v),
                width=1,
            )

            for wall in partition.walls:
                pygame.draw.rect(screen, wall.color, wall.rect.move(player.camera_v))

            for b_wall in partition.bounding_walls:
                pygame.draw.rect(
                    screen, b_wall.color, b_wall.rect.move(player.camera_v)
                )

    client_game_manager.draw_projectiles(player.camera_v)
    client_game_manager.draw_beams(player.camera_v)

    # A drawing is based on a single network message from the server.
    # The reason why it looks like we have shifted tiles is that we received a message in the middle, so this needs to be locked.
    # instead of actually simulating its movement that way it seems more solid
    for sprite in client_game_manager.all_sprites:
        # Add the player's camera offset to the coords of all sprites.
        screen.blit(sprite.image, sprite.rect.topleft + player.camera_v)

    # PLAYER PROPERTIES START

    font_color = pygame.color.THECOLORS["brown3"]  # type: ignore

    pos = font.render(str(player.position), False, font_color)
    aim_angle_str = (
        str(9 - math.floor(player.rotation_angle / math.tau * 10)) + "/" + str(10)
    )
    angle = font.render(aim_angle_str + "τ", False, font_color)

    screen.blit(pos, (0, 25))
    screen.blit(angle, (0, 50))

    client_game_manager.user_chat_box.update_message_times(delta_time)

    client_game_manager.user_chat_box.draw_messages()
    client_game_manager.user_text_box.render_text()

    utb_width, utb_height = client_game_manager.user_text_box.image.get_size()

    screen.blit(
        client_game_manager.user_text_box.image,
        (
            game_engine_constants.WIDTH
            - (utb_width + 2 * client_game_manager.user_text_box.border_thickness),
            game_engine_constants.HEIGHT
            - (utb_height + 2 * client_game_manager.user_text_box.border_thickness),
        ),
    )


def run_client(args):
    screen, font, clock = initialize_pygame(args.fullscreen)
    socket, player_id = initialize_network(args.ip_address, args.port)
    player = initialize_player(socket, player_id, args.sensitivity)

    map_fullname = f"{game_engine_constants.MAP_PREFIX}{args.map}"
    client_game_manager = ClientGameManager(
        screen, font, map_fullname, player_id, player
    )

    t = Thread(target=server_listener, args=(client_game_manager, socket))
    t.start()

    running = True
    while running:
        # Run at constant rate
        delta_time = clock.tick(game_engine_constants.FPS)
        delta_time /= 1000

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        update(client_game_manager, player, events)

        render(client_game_manager, delta_time, player, screen, font)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    args = parse_args()
    run_client(args)
