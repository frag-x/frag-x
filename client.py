from typing import cast, Tuple
import socket
import pygame
from comms import network, message
import argparse
import game_engine_constants
from threading import Thread
from client_instance import ClientInstance
from comms.message import ServerJoinMessage

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

def server_listener(
    socket: socket.socket,
    client_instance: ClientInstance,
) -> None:
    while True:
        input_message = cast(message.ServerMessage, network.recv(socket))
        client_instance.process_input_message(input_message)

def initialize_network(ip_address: str, port: int) -> Tuple[socket.socket, ServerJoinMessage]:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((ip_address, port))

    server_join_message = network.recv(server_socket)
    if type(server_join_message) is message.ServerJoinMessage:
        print(f"You are player {server_join_message.player_id}")
        return server_socket, server_join_message
    else:
        raise message.UnknownMessageTypeError

def run_client(args):
    server_socket, server_join_message = initialize_network(args.ip_address, args.port)

    client_instance = ClientInstance(server_socket, server_join_message, args.fullscreen, args.sensitivity)

    t = Thread(target=server_listener, args=(server_socket, client_instance))
    t.start()

    running = True
    while running:
        running = client_instance.step()

    pygame.quit()


if __name__ == "__main__":
    args = parse_args()
    run_client(args)
