import socket
import pygame
import argparse

from typing import List
from queue import Queue
from converters import str_to_player_data
from threading import Lock, Thread

import game_engine_constants

from comms import network, message
from simulation import Simulation

import global_simulation


def listener(simulation, server_socket, state_queue):
    while True:
        client_socket, addr = server_socket.accept()
        player_id = simulation.add_player(client_socket)
        network.send(client_socket, message.ServerJoinMessage(player_id=player_id))
        print(f"Accepted connection from {addr}")

        t = Thread(target=client_listener, args=(client_socket, state_queue))
        t.start()


def client_listener(socket, input_messages):
    while True:
        try:
            input_messages.put(network.recv(socket))
        except ConnectionResetError:
            exit()


def server_messager(simulation, output_messages):
    while True:
        if not output_messages.empty():
            message = output_messages.get()
            players = simulation.get_players()
            for player in players:
                try:
                    network.send(player.socket, message)
                except BrokenPipeError:
                    print(f"Player {player} forcibly disconnected!")
                    simulation.remove_player(player)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", "-l", dest="local", action="store_true")
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=game_engine_constants.DEFAULT_PORT,
        help="port to host server on",
    )
    parser.add_argument(
        "--map",
        "-m",
        type=str,
        default=game_engine_constants.DEFAULT_MAP,
        help="game map",
    )
    parser.set_defaults(local=False)
    return parser.parse_args()


def initialize_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip_address = "localhost" if args.local else ""

    server_socket.bind((ip_address, args.port))
    server_socket.listen()
    print(f"Server started on {(ip_address, args.port)}")

    return server_socket


def run_server(args):
    server_socket = initialize_socket()

    input_messages = Queue()
    output_messages = Queue()

    global_simulation.SIMULATION = Simulation(args.map, input_messages, output_messages)

    tsa_t = Thread(
        target=listener,
        args=(
            global_simulation.SIMULATION,
            server_socket,
            input_messages,
        ),
    )
    tsa_t.start()

    gss_t = Thread(
        target=server_messager,
        args=(
            global_simulation.SIMULATION,
            output_messages,
        ),
    )
    gss_t.start()

    while True:
        vote_result = global_simulation.SIMULATION.step()
        if vote_result:
            raise NotImplementedError


if __name__ == "__main__":
    args = parse_args()
    run_server(args)
