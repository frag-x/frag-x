import socket
import pickle
import pygame
from typing import List
from game_engine_constants import SCREEN_CENTER_POINT, ORIGIN, BUF_SIZE, PORT, LOCAL_IP, SERVER_TICK_RATE_HZ, REMOTE_IP, RUNNING_LOCALLY, DEV_MAP
from network import FragNetwork
from converters import str_to_player_data
from player import ServerPlayer
from threading import Lock, Thread
import collisions
import logging
#logging.basicConfig(level=logging.INFO)
import map_loading
from queue import Queue
import time
import math
from player import ServerPlayer

# START MAP LOAD

map_grid = map_loading.MapGrid(map_loading.get_pixels(DEV_MAP))
partitioned_map_grid = map_loading.PartitionedMapGrid(map_loading.get_pixels(DEV_MAP),10, 10)

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

players = []

player_start_positions = [ORIGIN, SCREEN_CENTER_POINT]

def client_state_producer(conn, state_queue):
    """
    This function gets run as a thread, it is associated with a single player and retreives their inputs
    """
    # This sends the initial position of the player
    # conn.send(str.encode(convert_pos_int_repr_to_str_repr(player_start_positions[player_id])))

    #p = ServerPlayer(player_start_positions[player_id], 50, 50)

    #players.append(p)

    iterations = 0
    recv_buffer = ""
    while True:
        try: 
            data = conn.recv(BUF_SIZE)

            if not data:
                # Likely means we've disconnected
                break
            else:
                #print(f'Received: {data.decode("utf-8")}')

                recv_buffer += data.decode("utf-8")

                messages = recv_buffer.split('~')

                recv_buffer = messages[-1]

                for player_data in messages[:-1]:

                    q_drain_lock.acquire()

                    state_queue.put(str_to_player_data(player_data))

                    q_drain_lock.release()

        except Exception as e:
            print(f"wasn't able to get data because {e}")
            break
        iterations += 1

    print("Lost connection")
    conn.close()

id_to_player = {}

def threaded_server_acceptor(state_queue):
    # Allowing this because it's not being accessed anywhere else
    player_id = 0
    # CONNECT LOOP
    while True:
        conn, addr = s.accept()
        conn.send(str.encode(str(player_id)))
        print(f"Accept connection from {addr}")

        player_lock.acquire()

        id_to_player[player_id] = ServerPlayer(SCREEN_CENTER_POINT, 50, 50, player_id, conn)

        player_lock.release()

        # If a player connects they get their own thread
        t = Thread(target=client_state_producer, args=(conn, state_queue))
        t.start()
        
        player_id += 1


# for batching the inputs and running physics simulation

q_drain_lock = Lock()
player_lock = Lock()
clock = pygame.time.Clock()     ## For syncing the FPS
state_queue = Queue()
server_updates = []

tsa_t = Thread(target=threaded_server_acceptor, args=(state_queue,))
tsa_t.start()

ticks_from_previous_iteration = 0

while True:

    clock.tick(SERVER_TICK_RATE_HZ)     ## will make the loop run at the same speed all the time

    t = pygame.time.get_ticks()

    q_drain_lock.acquire()  

    start_player_computation_time = time.time()

    while not state_queue.empty():
        #print("q is drainable")
        player_id, dx, dy, dm, delta_time, firing = state_queue.get()

        # TODO and if it's not??
        if player_id in id_to_player:
            p = id_to_player[player_id]
            p.update_position(dx, dy, delta_time)
            p.update_aim(dm)

        if firing:
            beam = p.weapon.get_beam()
            players = list(id_to_player.values())
            other_players = [x for x in players if x is not p]
        #    #closest_hit, closest_entity = p.weapon.get_all_intersecting_objects(map_grid.bounding_walls, other_players)
            closest_hit, closest_entity = p.weapon.get_closest_intersecting_object_in_pmg(partitioned_map_grid, beam)

            if type(closest_entity) is ServerPlayer:
                # Then also send a weapon message saying hit and draw a line shooting the other player
                hit_v = pygame.math.Vector2(0,0)
                # Because from polar is in deg apparently ...
                # TODO add a polar version to pygame
                deg = p.rotation_angle * 360/math.tau
                hit_v.from_polar((p.weapon.power, deg))
                closest_entity.velocity += hit_v

        start_collision_time = time.time()
        # Now that their positions have been updated we can check for collisions
        # TODO we only need to iterate over the four boxes around them or something similar to the hitscan case.

        # We reset and then refill with updated information
        partitioned_map_grid.reset_players_in_partitions()
        bodies = list(id_to_player.values())
        n = len(bodies)
        # This iterates over all the possible 
        for i in range(n):
            b1 = bodies[i]
            # Checks for collisions with other bodies
            for j in range(i+1, n):
                b2 = bodies[j]
                if collisions.bodies_colliding(b1.pos, b1.radius, b2.pos, b2.radius):
                    collisions.elastic_collision_update(b1, b2)

            # Checks for collisions with walls

            
            # TODO Move this to the server side
            partition_idx_x = int(b1.pos.x // partitioned_map_grid.partition_width)
            partition_idx_y = int(b1.pos.y // partitioned_map_grid.partition_height)

            # Put the player in the corresponding box
            partitioned_map_grid.partitioned_map[partition_idx_y][partition_idx_x].players.append(b1)

            curr_partition = partitioned_map_grid.collision_partitioned_map[partition_idx_y][partition_idx_x]

            # TODO add the player to this partitions playerlist


            for b_wall in curr_partition.bounding_walls:
                colliding, closest_v = collisions.colliding_and_closest(b1, b_wall)
                if colliding:
                    collisions.simulate_collision_v2(b1, b_wall, closest_v)

        end_collsion_time = time.time()

        logging.info(f"Amount of time to compute collisions for player {p.player_id}: {end_collsion_time - start_collision_time}")


    end_player_computation_time = time.time()
    logging.info(f"Amount of time to compute operations for all players: {end_player_computation_time - start_player_computation_time}")
    
    q_drain_lock.release()  


    player_lock.acquire()

    start_send_time = time.time()

    # get the game state ready to be sent
    for p in id_to_player.values():
        server_updates.append(p.get_sendable_state())

    # Send the game state to each of the players
    for p in id_to_player.values():
        #print("server updates", server_updates)
        p.socket.sendall(pickle.dumps(server_updates))

    end_send_time = time.time()

    logging.info(f"Amount of time to send game data: {end_send_time - start_send_time}")

    # reset server updates
    server_updates = []

    player_lock.release()

