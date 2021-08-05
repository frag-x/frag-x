import socket
import pickle
import pygame
from typing import List
from game_engine_constants import (
    SCREEN_CENTER_POINT,
    ORIGIN,
    BUF_SIZE,
    PORT,
    LOCAL_IP,
    SERVER_TICK_RATE_HZ,
    REMOTE_IP,
    RUNNING_LOCALLY,
    DEV_MAP,
)
import game_engine_constants
from network import FragNetwork
from converters import str_to_player_data
from threading import Lock, Thread
import collisions, dev_constants
import logging

# logging.basicConfig(level=logging.INFO)
import map_loading, client_server_communication, helpers, intersections, weapons, managers, game_modes
from queue import Queue
import time
import math

if dev_constants.PROFILING_PROGRAM:
    import yappi

    yappi.start()


# START MAP LOAD

# chosen_map = "dm_m1.png"
chosen_map = DEV_MAP

print(chosen_map, game_engine_constants.DM_MAPS)
if chosen_map in game_engine_constants.DM_MAPS:
    print("we have a DM map")
    SGM = managers.FirstToNFragsDMServerGameManager(chosen_map)
else:
    SGM = managers.ServerGameManager(DEV_MAP, game_modes.FirstToNFrags(2))

# END MAP LOAD

# START SOCKET SETUP

if RUNNING_LOCALLY:
    SERVER_ADDRESS = LOCAL_IP
else:
    SERVER_ADDRESS = ""

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((SERVER_ADDRESS, PORT))

except socket.error as e:
    str(e)

s.listen(2)

print(f"Server started on {(SERVER_ADDRESS, PORT)}")

# END SOCKET SETUP


player_start_positions = [ORIGIN, SCREEN_CENTER_POINT]


def game_state_sender(game_state_queue):
    while True:

        # Incase someone joins in the middle - would that be so bad??? - TODO maybe remove these locks

        # consume the message
        if (
            not game_state_queue.empty()
        ):  # TODO why does removing this cause immense lag?
            game_state_message = game_state_queue.get()

            # Send the game state to each of the players
            # TODO instead of doing this use the socket they are connected on
            for p in list(SGM.id_to_player.values()):
                # if dev_constants.DEBUGGING_NETWORK_MESSAGES:
                byte_message = pickle.dumps(game_state_message)
                if True:
                    p.socket.sendall(
                        len(byte_message).to_bytes(4, "little") + byte_message
                    )
                else:
                    p.socket.sendall(byte_message)


def client_state_producer(conn, state_queue):
    """
    This function gets run as a thread, it is associated with a single player and retreives their inputs
    """
    # This sends the initial position of the player
    # conn.send(str.encode(convert_pos_int_repr_to_str_repr(player_start_positions[player_id])))

    iterations = 0
    recv_buffer = ""
    while True:
        try:
            data = conn.recv(BUF_SIZE)

            if not data:
                # Likely means we've disconnected
                break
            else:
                # print(f'Received: {data.decode("utf-8")}')

                recv_buffer += data.decode("utf-8")

                # Our network manager delimits all messages this way
                messages = recv_buffer.split("~")

                recv_buffer = messages[-1]

                for player_data in messages[:-1]:

                    if dev_constants.DEBUGGING_NETWORK_MESSAGES:
                        print(f"RECEIVED: {player_data}")

                    player_data = "|".join(player_data.split("|")[1:])

                    state_queue.put(str_to_player_data(player_data))

        except Exception as e:
            print(f"wasn't able to get data because {e}")
            break
        iterations += 1

    print("Lost connection")
    conn.close()


def threaded_server_acceptor(state_queue):
    while True:
        client_socket, addr = s.accept()

        player_id = SGM.add_player(client_socket)

        # TODO do I need to send this?
        client_socket.send(str.encode(str(player_id)))
        print(f"Accept connection from {addr}")

        # If a player connects they get their own thread
        # TODO START a thread that sends them data too
        t = Thread(target=client_state_producer, args=(client_socket, state_queue))
        t.start()


# for batching the inputs and running physics simulation


player_lock = Lock()

socket_send_lock = Lock()

clock = pygame.time.Clock()  ## For syncing the FPS

# TODO Rename this
state_queue = Queue()
# TODO add threads for this
game_state_queue = Queue()

positional_player_data_queue = Queue()
positional_player_data_lock = Lock()
projectile_data_queue = Queue()
projectile_data_lock = Lock()

server_updates = []

# START THREAD SETUP

tsa_t = Thread(target=threaded_server_acceptor, args=(state_queue,))
tsa_t.start()

gss_t = Thread(target=game_state_sender, args=(game_state_queue,))
gss_t.start()

# END THREAD SETUP

ticks_from_previous_iteration = 0

count_down = game_engine_constants.SERVER_TICK_RATE_HZ * 10

num_frames = 0

while True:
    # while count_down == num_frames: if you're profiling the program

    num_frames += 1

    clock.tick(
        SERVER_TICK_RATE_HZ
    )  ## will make the loop run at the same speed all the time

    t = pygame.time.get_ticks()
    # deltaTime in seconds.
    time_since_last_iteration = (t - ticks_from_previous_iteration) / 1000.0
    ticks_from_previous_iteration = t

    start_player_computation_time = time.time()

    while not state_queue.empty():  # TODO why does removing this cause immense lag?
        # print("q is drainable")
        player_id, dx, dy, dm, delta_time, firing, weapon_request = state_queue.get()

        # TODO store input messages directly in the queue or something like that.

        input_message = client_server_communication.InputMessage(
            player_id, dx, dy, dm, delta_time, firing, weapon_request
        )

        SGM.perform_all_server_operations(
            time_since_last_iteration, input_message, game_state_queue
        )


if dev_constants.PROFILING_PROGRAM:
    yappi.stop()

    # retrieve thread stats by their thread id (given by yappi)
    threads = yappi.get_thread_stats()
    for thread in threads:
        print(
            "Function stats for (%s) (%d)" % (thread.name, thread.id)
        )  # it is the Thread.__class__.__name__
        yappi.get_func_stats(ctx_id=thread.id).print_all()
