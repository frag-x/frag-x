import socket
import pickle
import pygame
from typing import List
from game_engine_constants import SCREEN_CENTER_POINT, ORIGIN, BUF_SIZE, PORT, LOCAL_IP, SERVER_TICK_RATE_HZ, REMOTE_IP, RUNNING_LOCALLY, DEV_MAP
import game_engine_constants
from network import FragNetwork
from converters import str_to_player_data
from player import ServerPlayer
from threading import Lock, Thread
import collisions, dev_constants
import logging
#logging.basicConfig(level=logging.INFO)
import map_loading, client_server_communication, helpers, intersections, weapons, managers
from queue import Queue
import time
import math
from player import ServerPlayer

if dev_constants.PROFILING_PROGRAM:
    import yappi
    yappi.start()


SGM = managers.ServerGameManager(DEV_MAP)

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


player_start_positions = [ORIGIN, SCREEN_CENTER_POINT]

def game_state_sender(game_state_queue):
    while True:

        # consume the message
        _ = game_state_queue.get()

        # Incase someone joins in the middle - would that be so bad??? - TODO maybe remove these locks

        game_state_message = SGM.construct_game_state_message()

        # Send the game state to each of the players
        # TODO instead of doing this use the socket they are connected on
        for p in list(SGM.id_to_player.values()):
            if dev_constants.DEBUGGING_NETWORK_MESSAGES:
                print("SERVER SENDING", game_state_message)
            p.socket.sendall(pickle.dumps(game_state_message))



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

                # Our network manager delimits all messages this way
                messages = recv_buffer.split('~')

                recv_buffer = messages[-1]

                for player_data in messages[:-1]:



                    if dev_constants.DEBUGGING_NETWORK_MESSAGES:
                        print(f"RECEIVED: {player_data}")

                    player_data = '|'.join(player_data.split('|')[1:])

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

clock = pygame.time.Clock()     ## For syncing the FPS

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

#ppds_t = Thread(target=positional_player_data_sender, args=(positional_player_data_queue,game_state_queue))
#ppds_t.start()
#
#pds_t = Thread(target=projectile_data_sender, args=(projectile_data_queue,game_state_queue))
#pds_t.start()

gss_t = Thread(target=game_state_sender, args=(game_state_queue,))
gss_t.start()

# END THREAD SETUP

ticks_from_previous_iteration = 0

count_down = game_engine_constants.SERVER_TICK_RATE_HZ * 10

num_frames = 0

while True:
#while count_down == num_frames: if you're profiling the program

    num_frames += 1

    clock.tick(SERVER_TICK_RATE_HZ)     ## will make the loop run at the same speed all the time

    t = pygame.time.get_ticks()


    start_player_computation_time = time.time()

    while not state_queue.empty(): # TODO why does removing this cause immense lag?
        #print("q is drainable")
        player_id, dx, dy, dm, delta_time, firing = state_queue.get()

        # TODO store input messages directly in the queue or something like that.

        input_message = client_server_communication.InputMessage(player_id, dx, dy, dm, delta_time, firing)

        SGM.perform_all_server_operations(input_message)

        #hitscan = False

        ## TODO and if it's not??
        #if player_id in id_to_player:
        #    p = id_to_player[player_id]
        #    p.update_position(dx, dy, delta_time)
        #    p.update_aim(dm)
        #    p.weapon.time_since_last_shot += delta_time
        #    if not hitscan:
        #        for rocket in p.weapon.fired_projectiles:
        #            # TODO Does using the players delta time make sense?
        #            # We should rather update this on the server side ?
        #            p.weapon.update_projectile_positions(delta_time)

        #if firing:
        #    if p.weapon.time_since_last_shot >= p.weapon.seconds_per_shot:
        #        # reset time on gun
        #        p.weapon.time_since_last_shot = 0
        #        if hitscan:
        #            beam = p.weapon.get_beam()
        #            players = list(id_to_player.values())
        #            other_players = [x for x in players if x is not p]
        #        #    #closest_hit, closest_entity = p.weapon.get_all_intersecting_objects(map_grid.bounding_walls, other_players)
        #            closest_hit, closest_entity = intersections.get_closest_intersecting_object_in_pmg(p.weapon, partitioned_map_grid, beam)

        #            if type(closest_entity) is ServerPlayer:
        #                # Then also send a weapon message saying hit and draw a line shooting the other player
        #                hit_v = pygame.math.Vector2(0,0)
        #                # Because from polar is in deg apparently ...
        #                # TODO add a polar version to pygame
        #                deg = p.rotation_angle * 360/math.tau
        #                hit_v.from_polar((p.weapon.power, deg))
        #                closest_entity.velocity += hit_v
        #        else:
        #            p.weapon.fire_projectile()

        #start_collision_time = time.time()
        ## Now that their positions have been updated we can check for collisions
        ## TODO we only need to iterate over the four boxes around them or something similar to the hitscan case.

        ## We reset and then refill with updated information
        #partitioned_map_grid.reset_players_in_partitions()
        #bodies = list(id_to_player.values())
        #n = len(bodies)
        ## This iterates over all the possible 
        #for i in range(n):
        #    b1 = bodies[i]
        #    # Checks for collisions with other bodies
        #    for j in range(i+1, n):
        #        b2 = bodies[j]
        #        if collisions.bodies_colliding(b1.pos, b1.radius, b2.pos, b2.radius):
        #            collisions.elastic_collision_update(b1, b2)

        #    # Checks for collisions with walls

        #    # START WALL COLISIONS

        #    partition_idx_x, partition_idx_y = helpers.get_partition_index(partitioned_map_grid, b1.pos)
        #    #partition_idx_x = int(b1.pos.x // partitioned_map_grid.partition_width)
        #    #partition_idx_y = int(b1.pos.y // partitioned_map_grid.partition_height)

        #    # Put the player in the corresponding box
        #    partitioned_map_grid.partitioned_map[partition_idx_y][partition_idx_x].players.append(b1)

        #    curr_partition = partitioned_map_grid.collision_partitioned_map[partition_idx_y][partition_idx_x]


        #    for b_wall in curr_partition.bounding_walls:
        #        colliding, closest_v = collisions.colliding_and_closest(b1, b_wall)
        #        if colliding:
        #            collisions.simulate_collision_v2(b1, b_wall, closest_v)

        #    # END WALL COLLISIONS

        #    # START ROCKET COLLISIONS TODO also check for collisions with OTHER players as well

        #    projectiles_to_explode = set()
        #    #print(b1.weapon.fired_projectiles)
        #    for rocket in b1.weapon.fired_projectiles:
        #        projectile_idx_x, projectile_idx_y = helpers.get_partition_index(partitioned_map_grid, rocket.pos)
        #        projectile_partition = partitioned_map_grid.collision_partitioned_map[projectile_idx_y][projectile_idx_x]

        #        for p_wall in projectile_partition.bounding_walls:
        #            colliding, closest_v = collisions.colliding_and_closest(rocket, p_wall)
        #            if colliding:
        #                projectiles_to_explode.add(rocket)
        #                # Move it out of the wall
        #                rocket.pos = rocket.previous_pos
        #                rocket_explosion = weapons.Explosion(rocket.pos)
        #                for beam in rocket_explosion.beams:
        #                    print("beam", beam)
        #                    closest_hit, closest_entity = intersections.get_closest_intersecting_object_in_pmg(b1.weapon, partitioned_map_grid, beam)

        #                    if type(closest_entity) is ServerPlayer:
        #                        print(f"Explosion at {rocket_explosion.pos - b1.pos} hit by beam {beam.direction_vector}")
        #                        # Then also send a weapon message saying hit and draw a line shooting the other player
        #                        closest_entity.velocity += beam.direction_vector * rocket_explosion.power
        #                    print("bang")

        #    for projectile in projectiles_to_explode:
        #        b1.weapon.fired_projectiles.remove(projectile)

        #    # END ROCKET COLLISIONS

        #end_collsion_time = time.time()

        #logging.info(f"Amount of time to compute collisions for player {p.player_id}: {end_collsion_time - start_collision_time}")


    end_player_computation_time = time.time()
    logging.info(f"Amount of time to compute operations for all players: {end_player_computation_time - start_player_computation_time}")
    


    #player_lock.acquire()

    start_send_time = time.time()

    #server_updates = [client_server_communication.ClientMessageType.PLAYER_POSITIONS.value]

    # TODO NEED MULTITHREADING FOR THIS.

    # === START SEND PLAYER POSITIONS ===
   #3 for p in id_to_player.values():
   #3     server_updates.append(client_server_communication.PlayerPositionMessage(p))

   #3 # Send the game state to each of the players
   #3 for p in id_to_player.values():
   #3     #player_positions = str(client_server_communication.ClientMessageType.PLAYER_POSITIONS.value) + "|" + str(server_updates)
   #3     if dev_constants.DEBUGGING_NETWORK_MESSAGES:
   #3         print("server updates", server_updates)
   #3     p.socket.sendall(pickle.dumps(server_updates))

    #projectile_data_queue.put("send request")
    #positional_player_data_queue.put("send request")

    game_state_queue.put("send request")

    # === END SEND PLAYER POSITIONS ===

    # === START SEND PROJECTILE POSITIONS ===
    #projectile_positions =  []
    #for p in id_to_player.values():
    #    for projectile in p.weapon.fired_projectiles:
    #        projectile_positions.append(client_server_communication.ProjectilePositionMessage(projectile.pos.x, projectile.pos.y))
    #
    ## Don't send empty data
    #if len(projectile_positions) != 0:
    #    for p in id_to_player.values():
    #        if dev_constants.DEBUGGING_NETWORK_MESSAGES:
    #            print(f"sending projectile positions: {projectile_positions}")
    #        print("fugg", [(pos.x, pos.y) for pos in projectile_positions])
    #        p.socket.sendall(pickle.dumps(projectile_positions))
    

    # === END SEND PROJECTILE POSITIONS ===


    end_send_time = time.time()

    logging.info(f"Amount of time to send game data: {end_send_time - start_send_time}")

    # reset server updates
    server_updates = []

    #player_lock.release()


if dev_constants.PROFILING_PROGRAM:
    yappi.stop()

    # retrieve thread stats by their thread id (given by yappi)
    threads = yappi.get_thread_stats()
    for thread in threads:
        print(
            "Function stats for (%s) (%d)" % (thread.name, thread.id)
        )  # it is the Thread.__class__.__name__
        yappi.get_func_stats(ctx_id=thread.id).print_all()
