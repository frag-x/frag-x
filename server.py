import socket
import argparse

from queue import Queue
from threading import Thread

import game_engine_constants

from comms import network, message
from simulation import Simulation

import global_simulation


def listener(server_socket: socket.socket, state_queue: Queue[message.Message]) -> None:
    while True:
        client_socket, addr = server_socket.accept()
        player_id = global_simulation.SIMULATION.add_player(client_socket)
        network.send(
            client_socket,
            message.ServerJoinMessage(
                player_id=player_id, map_name=global_simulation.SIMULATION.map_name
            ),
        )
        print(f"Accepted connection from {addr}")

        t = Thread(target=client_listener, args=(client_socket, state_queue))
        t.start()


def client_listener(
    socket: socket.socket, input_messages: Queue[message.Message]
) -> None:
    while True:
        try:
            input_messages.put(network.recv(socket))
        except ConnectionResetError:
            exit()


def server_messager(output_messages: Queue[message.Message]) -> None:
    while True:
        if not output_messages.empty():
            message = output_messages.get()
            players = global_simulation.SIMULATION.get_players()
            for player in players:
                try:
                    network.send(player.socket, message)
                except BrokenPipeError:
                    print(f"Player {player} forcibly disconnected!")
                    global_simulation.SIMULATION.remove_player(player)


def parse_args() -> argparse.Namespace:
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


def initialize_socket() -> socket.socket:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip_address = "localhost" if args.local else ""

    server_socket.bind((ip_address, args.port))
    server_socket.listen()
    print(f"Server started on {(ip_address, args.port)}")

    return server_socket


def load_requested_map(
    map_name: str | None,
    invalid_map_names: set[str],
    input_messages: Queue[message.Message],
    output_messages: Queue[message.Message],
) -> bool:
    if map_name in invalid_map_names:
        return False

    players = global_simulation.SIMULATION.players
    try:
        global_simulation.SIMULATION = Simulation(
            map_name, input_messages, output_messages, players=players
        )
    except FileNotFoundError:
        print(f"Could not load requested map {map_name}")
        invalid_map_names.add(map_name)
        return False
    else:
        output_messages.put(message.ServerMapChangeMessage(map_name=map_name))
        return True


def run_server(args: argparse.Namespace) -> None:
    input_messages: Queue[message.Message] = Queue()
    output_messages: Queue[message.Message] = Queue()

    global_simulation.SIMULATION = Simulation(args.map, input_messages, output_messages)

    server_socket = initialize_socket()

    tsa_t = Thread(
        target=listener,
        args=(
            server_socket,
            input_messages,
        ),
    )
    tsa_t.start()

    gss_t = Thread(
        target=server_messager,
        args=(output_messages,),
    )
    gss_t.start()

    invalid_map_names: set[str] = set()
    while True:
        keep_map, requested_map_name = global_simulation.SIMULATION.step()
        if not keep_map:
            load_requested_map(
                requested_map_name, invalid_map_names, input_messages, output_messages
            )


if __name__ == "__main__":
    args = parse_args()
    run_server(args)
