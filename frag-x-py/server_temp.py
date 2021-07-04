import socket
import _thread
import sys 
import pygame
from typing import List
from game_engine_constants import SCREEN_CENTER_POINT, ORIGIN, BUF_SIZE, PORT, LOCAL_IP
from network import FragNetwork
from converters import convert_player_data_to_str, convert_str_to_player_data, convert_pos_str_to_player_pos, convert_player_pos_to_pos_str
from player import ServerPlayer

SERVER_ADDRESS = LOCAL_IP

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try: 
    s.bind((SERVER_ADDRESS, PORT))

except socket.error as e:
    str(e)

s.listen(2)

print("Server started")

players = []

player_start_positions = [ORIGIN, SCREEN_CENTER_POINT]

def threaded_client(conn, player_id):
    # This sends the initial position of the player
    #conn.send(str.encode(convert_pos_int_repr_to_str_repr(player_start_positions[player_id])))

    p = ServerPlayer(player_start_positions[player_id], 50, 50)

    players.append(p)

    reply = ""
    print("in the thread")
    iterations = 0
    while True:
        print(f"in the while iteration {iterations}")
        try: 
            data = conn.recv(BUF_SIZE)
            print("in try block")

            if not data:
                # Likely means we've disconnected
                print("Disconnected")
                break
            else:

                print(f"Received: {data}")

                player_data = convert_str_to_player_data(data.decode("utf-8"))
                x,y,delta_time = player_data

                print("fuck")

                p.update_movement_vector(x,y)

                p.update_position(delta_time)

                # We can't use convert player data again because it would require delta time
                # which isn't required for the return trip ... yet?
                reply = convert_player_pos_to_pos_str(int(p.pos.x), int(p.pos.y))

                print(f"Sending: {reply}")

            conn.sendall(str.encode(reply))
        except Exception as e:
            print(f"wasn't able to get data because {e}")
            break
        iterations += 1

    print("Lost connection")
    conn.close()

player_id = 0
while True:
    conn, addr = s.accept()
    print(f"Accept connection from {addr}")

    _thread.start_new_thread(threaded_client, (conn,player_id))
    player_id += 1

