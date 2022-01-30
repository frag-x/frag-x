from typing import cast, Tuple
import socket
import pygame
from comms import network, message
import argparse
import game_engine_constants
from threading import Thread
from client_instance import ClientInstance
from comms.message import ServerJoinMessage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--ip_address",
        type=str,
        default="localhost",
        help="ip to connect to server on",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=game_engine_constants.DEFAULT_PORT,
        help="port to connect to server on",
    )
    parser.add_argument(
        "-w",
        "--windowed",
        dest="fullscreen",
        action="store_false",
        help="run in windowed mode",
    )
    parser.add_argument(
        "-s",
        "--sensitivity",
        type=float,
        default=game_engine_constants.DEFAULT_SENSITIVITY,
        help="mouse sensitivity",
    )
    parser.add_argument(
        "-f",
        "--frame_rate",
        type=float,
        default=game_engine_constants.FPS,
        help="frame rate",
    )
    parser.set_defaults(fullscreen=True)
    return parser.parse_args()


def server_listener(
    socket: socket.socket,
    client_instance: ClientInstance,
) -> None:
    """
    Waits for messages from the server and then processes them

    :param socket: the connection to the server
    :param client_instance: the instance of the client
    :return:
    """
    while True:  # TODO kill thread when client quits by checking flag
        input_message = cast(message.ServerMessage, network.recv(socket))
        client_instance.process_input_message(input_message)


def initialize_network(
    ip_address: str, port: int
) -> Tuple[socket.socket, ServerJoinMessage]:
    """
    Makes an initial connection with the server, returns the socket it is connected through
    and the join message from the server

    :param ip_address: the ip address of the server
    :param port: the port of the server
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((ip_address, port))

    server_join_message = network.recv(server_socket)
    if type(server_join_message) is message.ServerJoinMessage:
        print(f"You are player {server_join_message.player_id}")
        return server_socket, server_join_message
    else:
        raise message.UnknownMessageTypeError


def run_client(args: argparse.Namespace) -> None:
    """
    Starts a client

    :param args: command line arguments parsed by argparse
    """
    server_socket, server_join_message = initialize_network(args.ip_address, args.port)

    client_instance = ClientInstance(
        server_socket,
        server_join_message,
        args.fullscreen,
        args.frame_rate,
        args.sensitivity,
    )

    t = Thread(target=server_listener, args=(server_socket, client_instance))
    t.start()

    running = True
    while running:
        running = client_instance.step()

    pygame.quit()


if __name__ == "__main__":
    args = parse_args()
    run_client(args)
