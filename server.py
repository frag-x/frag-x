import socket
import pygame
import argparse

from typing import List
from queue import Queue
from converters import str_to_player_data
from threading import Lock, Thread

import game_engine_constants

from managers.server_manager import FirstToNFragsDMServerGameManager
from comms import network, message

def listener(server_game_manager, server_socket, state_queue):
    while True:
        client_socket, addr = server_socket.accept()
        player_id = server_game_manager.add_player(client_socket)
        network.send(client_socket, message.ServerJoinMessage(player_id=player_id))
        print(f"Accepted connection from {addr}")

        t = Thread(target=client_listener, args=(client_socket, state_queue))
        t.start()

def client_listener(socket, input_messages):
    while True:
        input_messages.put(network.recv(socket))

def server_messager(server_game_manager, output_messages):
    while True:
        # TODO: what if someone joins in the middle?
        if not output_messages.empty():
            message = output_messages.get()
            for player in server_game_manager.get_players():
                network.send(player.socket, message)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--local', '-l', dest='local', action='store_true')
    parser.add_argument('--port', '-p', type=int, 
                        default=game_engine_constants.DEFAULT_PORT,
                        help='port to host server on')
    parser.add_argument('--map', '-m', type=str, 
                        default=game_engine_constants.DEFAULT_MAP,
                        help='game map')
    parser.set_defaults(local=False)
    return parser.parse_args()

def initialize_server(map):
    map_fullpath = f'{game_engine_constants.MAP_PREFIX}{map}'
    try:
        return FirstToNFragsDMServerGameManager(map_fullpath)
    except Exception:
        # TODO: catch bad maps
        raise

def initialize_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip_address = 'localhost' if args.local else ''

    server_socket.bind((ip_address, args.port))
    server_socket.listen()
    print(f"Server started on {(ip_address, args.port)}")
    
    return server_socket

def run_server(args):
    server_game_manager = initialize_server(args.map)
    server_socket = initialize_socket()

    clock = pygame.time.Clock() # FPS synchronization

    input_messages = Queue() # client to server
    output_messages = Queue() # server to client

    tsa_t = Thread(target=listener, args=(server_game_manager, server_socket, input_messages,))
    tsa_t.start()

    gss_t = Thread(target=server_messager, args=(server_game_manager, output_messages,))
    gss_t.start()

    num_frames = 0
    while True:
        num_frames += 1

        clock.tick(
            game_engine_constants.SERVER_TICK_RATE_HZ
        )  ## will make the loop run at the same speed all the time

        delta_time = clock.tick()
        delta_time /= 1000

        while not input_messages.empty():  # TODO why does removing this cause immense lag?
            input_message = input_messages.get()
            server_game_manager.perform_all_server_operations(
                delta_time, input_message, output_messages
            )

if __name__ == '__main__':
    args = parse_args()
    run_server(args)