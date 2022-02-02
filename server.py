import socket
import argparse

from queue import Queue
from threading import Thread

import game_engine_constants

from comms import network, message
from simulation import Simulation

import global_simulation


def tcp_listener(
    tcp_socket: socket.socket, udp_port: int, input_messages: Queue[message.Message]
) -> None:
    while True:
        client_socket, addr = tcp_socket.accept()
        player_id = global_simulation.SIMULATION.add_player(client_socket, addr)
        network.send(
            client_socket,
            message.ServerJoinMessage(
                player_id=player_id,
                map_name=global_simulation.SIMULATION.map_name,
                udp_port=udp_port,
            ),
        )
        print(f"Accepted connection from {addr}")

        t = Thread(target=client_listener, args=(client_socket, input_messages))
        t.start()


def udp_listener(
    udp_socket: socket.socket, input_messages: Queue[message.Message]
) -> None:
    while True:
        msg, addr = network.recvfrom(udp_socket)
        if type(msg) == message.UDPSetMessage:
            if msg.player_id in global_simulation.SIMULATION.players:
                # TODO: validate that the player is who they say they are
                global_simulation.SIMULATION.players[msg.player_id].set_udp(addr)
            else:
                print(f"unknown player connecting via udp: {addr}")
        else:
            input_messages.put(msg)


def client_listener(
    socket: socket.socket, input_messages: Queue[message.Message]
) -> None:
    while True:
        try:
            message = network.recv(socket)
            input_messages.put(message)
        except ConnectionResetError:
            exit()


def server_messager(
    udp_socket: socket.socket, output_messages: Queue[message.Message]
) -> None:
    while True:
        if not output_messages.empty():
            message = output_messages.get()
            players = global_simulation.SIMULATION.get_players()
            for player in players:
                try:
                    if player.udp_addr is not None:
                        network.sendto(udp_socket, player.udp_addr, message)
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


def initialize_sockets(args: argparse.Namespace) -> tuple[socket.socket, socket.socket]:
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip_address = "localhost" if args.local else ""

    tcp_socket.bind((ip_address, args.port))
    tcp_socket.listen()
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((ip_address, args.port))
    print(f"Server started on {(ip_address, args.port)}")

    return (tcp_socket, udp_socket)


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

    tcp_socket, udp_socket = initialize_sockets(args)

    tsa_t = Thread(
        target=tcp_listener,
        args=(
            tcp_socket,
            args.port,
            input_messages,
        ),
    )
    tsa_t.start()

    usa_t = Thread(
        target=udp_listener,
        args=(
            udp_socket,
            input_messages,
        ),
    )
    usa_t.start()

    gss_t = Thread(
        target=server_messager,
        args=(
            udp_socket,
            output_messages,
        ),
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
