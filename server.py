import socket
import pickle
import pygame
import helpers, managers, game_modes
import argparse

from typing import List
from queue import Queue
from converters import str_to_player_data
from threading import Lock, Thread

import game_engine_constants

from managers.server_manager import FirstToNFragsDMServerGameManager

def game_state_sender(server_game_manager, game_state_queue):
    while True:
        # Incase someone joins in the middle - would that be so bad??? - TODO maybe remove these locks

        # consume the message
        if (
            not game_state_queue.empty()
        ):
            game_state_message = game_state_queue.get()

            # Send the game state to each of the players
            # TODO instead of doing this use the socket they are connected on
            for player in server_game_manager.get_players():
                byte_message = pickle.dumps(game_state_message)
                try:
                    player.network.sendall(
                        len(byte_message).to_bytes(4, "little") + byte_message
                    )
                except BrokenPipeError:
                    # TODO remove player
                    pass


def client_listener(socket, state_queue):
    """
    This function gets run as a thread, it is associated with a single player and retreives their inputs
    """
    while True:
        size_bytes = helpers.recv_exactly(socket, 4)
        size = int.from_bytes(size_bytes, "little")
        data = helpers.recv_exactly(socket, size)
        player_input_message = pickle.loads(data)

        state_queue.put(player_input_message)


def threaded_server_acceptor(server_game_manager, server_socket, state_queue):
    while True:
        client_socket, addr = server_socket.accept()

        player_id = server_game_manager.add_player(client_socket)

        # TODO do I need to send this?
        client_socket.send(str.encode(str(player_id)))
        print(f"Accept connection from {addr}")

        # If a player connects they get their own thread
        # TODO START a thread that sends them data too
        t = Thread(target=client_listener, args=(client_socket, state_queue))
        t.start()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip_address', '-i', type=str, 
                        default=game_engine_constants.DEFAULT_IP,
                        help='ip to host server on')
    parser.add_argument('--port', '-p', type=int, 
                        default=game_engine_constants.DEFAULT_PORT,
                        help='port to host server on')
    parser.add_argument('--map', '-m', type=str, 
                        default=game_engine_constants.DEFAULT_MAP,
                        help='game map')
    return parser.parse_args()

def initialize_server(map):
    map_fullpath = f'{game_engine_constants.MAP_PREFIX}{map}'
    try:
        return FirstToNFragsDMServerGameManager(map_fullpath)
    except Exception:
        # TODO catch bad maps
        pass

def initialize_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_socket.bind((args.ip_address, args.port))

    except socket.error as e:
        str(e)
        raise

    server_socket.listen(2)
    print(f"Server started on {(args.ip_address, args.port)}")
    
    return server_socket

def run_server(args):
    server_game_manager = initialize_server(args.map)

    server_socket = initialize_socket()

    # FPS synchronization
    clock = pygame.time.Clock()

    # TODO Rename this
    state_queue = Queue()
    # TODO add threads for this
    game_state_queue = Queue()

    tsa_t = Thread(target=threaded_server_acceptor, args=(server_game_manager, server_socket, state_queue,))
    tsa_t.start()

    gss_t = Thread(target=game_state_sender, args=(server_game_manager, game_state_queue,))
    gss_t.start()

    ticks_from_previous_iteration = 0
    num_frames = 0
    while True:
        num_frames += 1

        clock.tick(
            game_engine_constants.SERVER_TICK_RATE_HZ
        )  ## will make the loop run at the same speed all the time

        t = pygame.time.get_ticks()
        # deltaTime in seconds.
        time_since_last_iteration = (t - ticks_from_previous_iteration) / 1000.0
        ticks_from_previous_iteration = t

        while not state_queue.empty():  # TODO why does removing this cause immense lag?
            # print("q is drainable")
            # TODO use class
            # player_id, dx, dy, dm, delta_time, firing, weapon_request = state_queue.get()
            input_message = state_queue.get()

            # TODO store input messages directly in the queue or something like that.

            # input_message = client_server_communication.InputNetworkMessage(
            #     player_id, dx, dy, dm, delta_time, firing, weapon_request
            # )

            server_game_manager.perform_all_server_operations(
                time_since_last_iteration, input_message, game_state_queue
            )

if __name__ == '__main__':
    args = parse_args()
    run_server(args)