import pygame, threading, uuid, math
import client_server_communication, network, game_engine_constants, dev_constants, player, intersections, map_loading, collisions, helpers, weapons
from player import ServerPlayer

class GameManager:
    def __init__(self, map_name):
        self.id_to_player = {}
        # TODO make this a set eventually
        self.projectiles = []
        self.partitioned_map_grid = map_loading.PartitionedMapGrid(map_loading.get_pixels(map_name),10, 10)

class ClientGameManager(GameManager):
    """A game manager which may be instatiated for the server or the client"""
    def __init__(self, screen, map_name):
        super().__init__(map_name)
        self.screen = screen
        self.client_message_parser = ClientMessageParser(self)
        self.player_data_lock = threading.Lock()
        self.network = network.FragNetwork()
        # TODO REMOVE THIS, just for support now
        self.all_sprites = pygame.sprite.Group()

    def set_player_positions(self):
        pass

    def set_projectile_positions(self):
        pass

    def draw_projectiles(self, camera_v):
        for projectile_message in self.projectiles:
            pos = pygame.math.Vector2(projectile_message.x, projectile_message.y)
            radius = game_engine_constants.TILE_SIZE/4
            pygame.draw.circle(self.screen, pygame.color.THECOLORS['chartreuse4'], pos + camera_v, radius)

    def consume_message(self, message):
        pass

    def send_message(self, message):
        # TODO replace the send_inputs with this function as it solves it more generally
        pass


class MessageParser:
    def __init__(self, message_type_to_command, client_game_manager):
        self.message_type_to_command = message_type_to_command
        self.client_game_manager = client_game_manager

    def run_command_from_message(self, message):
        # This is the command pattern
        #print(f"got {message_list} and about to run {self.message_type_to_command[message_list[0].message_type]}")

        self.message_type_to_command[message.message_type](message, self.client_game_manager)

class ClientMessageParser(MessageParser):
    def __init__(self, client_game_manager):
        super().__init__(message_type_to_command_client, client_game_manager)


def parse_player_position_message(message_list, client_game_manager):
    """The message in this case is a list of elements of the form

    player_data.player_id|player_data.x|y|player_data.rotation_angle

    """
    for player_data in message_list:
        if player_data.player_id not in client_game_manager.id_to_player:
            # TODO remove the network from a player the game manager will do that
            client_game_manager.id_to_player[player_data.player_id] = player.ClientPlayer((player_data.x,player_data.y), 50, 50, (50, 255, 5),game_engine_constants.ARROW_MOVEMENT_KEYS, player_data.player_id, client_game_manager.network)
            client_game_manager.all_sprites.add(client_game_manager.id_to_player[player_data.player_id])
        else:
            # this needs to be locked because if we are doing collisions or hitscan which depends on the position of the player then we can have issues where their position is updated after translating a point with respect to it's original position and then there are no valid 
            client_game_manager.player_data_lock.acquire()
            client_game_manager.id_to_player[player_data.player_id].set_pos(player_data.x,player_data.y)
            # In real life we can't change their view or they will freak - do it for now
            client_game_manager.id_to_player[player_data.player_id].rotation_angle = player_data.rotation_angle
            client_game_manager.player_data_lock.release()


def parse_game_state_message(game_state_message: client_server_communication.GameStateMessage, client_game_manager: ClientGameManager):
    parse_player_position_message(game_state_message.player_position_messages, client_game_manager)
    parse_projectile_position_message(game_state_message.projectile_position_messages, client_game_manager)

def parse_projectile_position_message(message_list, client_game_manager):
        client_game_manager.projectiles = message_list


#message_type_to_command_client = {ClientMessageType.PLAYER_POSITIONS.value: parse_player_position_message, ClientMessageType.PROJECTILE_POSITIONS.value: parse_projectile_position_message}
message_type_to_command_client = {client_server_communication.ClientMessageType.GAME_STATE_MESSAGE.value: parse_game_state_message}















class ServerGameManager(GameManager):
    """This class in in charge of all server operations"""
    def __init__(self, map_name):
        super().__init__(map_name)

    def construct_game_state_message(self) -> client_server_communication.GameStateMessage:
        """Collects and returns all the information about the current game state"""

        projectile_position_messages = []
        player_position_messages = []

        # Note: I was considering having a player lock here in case a player joined midway through and is added to the id_to_player list
        # but it's not an issue because if that's the case then their position won't be sent out to everyone until the next server tick which is fine
        players = self.id_to_player.values() 

        for p in players:
            # TODO check if their position has changed since last time otherwise don't append it
            for projectile in p.weapon.fired_projectiles:
                projectile_position_messages.append(client_server_communication.ProjectilePositionMessage(projectile.pos.x, projectile.pos.y))
                
            player_position_messages.append(client_server_communication.PlayerPositionMessage(p))

        game_state_message = client_server_communication.GameStateMessage(player_position_messages, projectile_position_messages)

        return game_state_message

    def add_player(self, client_socket):
        # Could this not being locked cause a problem?
        player_id = str(uuid.uuid1())
        self.id_to_player[player_id] = player.ServerPlayer(game_engine_constants.SCREEN_CENTER_POINT, 50, 50, player_id, client_socket)
        print(f'added player {self.id_to_player}')

        # TODO this will probably be removed
        return player_id

    def perform_all_server_operations(self, input_message):
        players = list(self.id_to_player.values())
        self.consume_player_inputs(input_message)
        self.simulate_collisions(players)

    def consume_player_inputs(self, input_message: client_server_communication.InputMessage):
        """Update the players attributes based on their input and operate their weapon if required"""
        player = self.id_to_player[input_message.player_id]
        net_x_movement = input_message.net_x_movement
        net_y_movement = input_message.net_y_movement
        time_since_last_client_frame = input_message.time_since_last_client_frame
        mouse_movement = input_message.mouse_movement
        firing = input_message.firing

        self.update_player_attributes(player, net_x_movement, net_y_movement, time_since_last_client_frame, mouse_movement)

        if firing:
            self.operate_player_weapon(player)



    def update_player_attributes(self, player, net_x_movement, net_y_movement, time_since_last_client_frame, mouse_movement):
        player.update_position(net_x_movement, net_y_movement, time_since_last_client_frame)
        player.update_aim(mouse_movement)
        player.weapon.time_since_last_shot += time_since_last_client_frame

        # TODO Does using the players delta time make sense?
        # We should rather update this based on the server timestep?
        player.weapon.update_projectile_positions(time_since_last_client_frame)

    def operate_player_weapon(self, player):
        """Given a player, verify if the player is allowed to fire the weapon again, and if they are fire the weapon"""
        # TODO remove this once weapon switching is enabled
        hitscan = False # testing projectile
        if player.weapon.time_since_last_shot >= player.weapon.seconds_per_shot:
            player.weapon.time_since_last_shot = 0
            # TODO have an enum with the types of weapons associated with the firing action, then use that here
            if hitscan:
                self.analyze_hitscan_shot(player)
            else: # allowed because the only other weapon implemented is the rocket launcher
                print("firing rl")
                player.weapon.fire_projectile()
        

    def analyze_hitscan_shot(self, firing_player):
        """Given the fact that a player is firing a hitscan weapon and has waited long enough (the shot is valid), check to see if the shot hits another player, if it does then apply a force to that player"""
        beam = firing_player.weapon.get_beam()


        closest_hit, closest_entity = intersections.get_closest_intersecting_object_in_pmg(firing_player.weapon, self.partitioned_map_grid, beam)

        if type(closest_entity) is player.ServerPlayer:
            # Then also send a weapon message saying hit and draw a line shooting the other player
            hit_v = pygame.math.Vector2(0,0)
            # Because from polar is in deg apparently ...
            # TODO add a polar version to pygame
            deg = firing_player.rotation_angle * 360/math.tau
            hit_v.from_polar((firing_player.weapon.power, deg))
            closest_entity.velocity += hit_v

    def simulate_collisions(self, players):
        # remove players from parition - we will update the positions in the loop
        self.partitioned_map_grid.reset_players_in_partitions()

        n = len(players)
        for i in range(n):
            p1 = players[i]
            # Checks for collisions with other bodies
            for j in range(i+1, n): # Note that in combination with the outer for loop this iterates through each pair of players only once
                p2 = players[j]
                if collisions.bodies_colliding(p1.pos, p1.radius, p2.pos, p2.radius):
                    collisions.elastic_collision_update(p1, p2)

            partition_idx_x, partition_idx_y = helpers.get_partition_index(self.partitioned_map_grid, p1.pos)

            curr_partition = self.partitioned_map_grid.partitioned_map[partition_idx_y][partition_idx_x]
            curr_collision_partition = self.partitioned_map_grid.collision_partitioned_map[partition_idx_y][partition_idx_x]
            # Put the player in the corresponding partition
            curr_partition.players.append(p1)

            self.simulate_wall_collision(p1, curr_collision_partition)

            self.simulate_rocket_explosions(p1)

            # END WALL COLLISIONS

    def simulate_wall_collision(self, player, players_partition):
        """Give a player and a partition that they reside within, check if they are colliding with any walls, and if they are simulate a collision"""
        for b_wall in players_partition.bounding_walls:
            colliding, closest_v = collisions.colliding_and_closest(player, b_wall)
            if colliding:
                collisions.simulate_collision_v2(player, b_wall, closest_v)

    def simulate_rocket_explosions(self, player):
        """Given a player, we consider all their actively fired rockets and if any of them are colliding with walls then we explode them"""
        # TODO also check for collisions with OTHER players as well
        projectiles_to_explode = set()
        for rocket in player.weapon.fired_projectiles:
            projectile_idx_x, projectile_idx_y = helpers.get_partition_index(self.partitioned_map_grid, rocket.pos)
            projectile_partition = self.partitioned_map_grid.collision_partitioned_map[projectile_idx_y][projectile_idx_x]

            for p_wall in projectile_partition.bounding_walls:
                colliding, closest_v = collisions.colliding_and_closest(rocket, p_wall)
                if colliding:
                    projectiles_to_explode.add(rocket)
                    # Move it out of the wall, that way the beams don't just get lodged in the wall
                    # TODO instead of exploding it right here get the closest position
                    # Use colliding and closest
                    rocket.pos = rocket.previous_pos
                    rocket_explosion = weapons.Explosion(rocket.pos)
                    if dev_constants.CLIENT_VISUAL_DEBUGGING:
                        dev_constants.EXPLOSIONS_FOR_DEBUGGING.append(rocket_explosion)
                    for beam in rocket_explosion.beams:
                        print("beam", beam)
                        closest_hit, closest_entity = intersections.get_closest_intersecting_object_in_pmg(player.weapon, self.partitioned_map_grid, beam)

                        # Have to import this because player.ServerPlayer wouldn't work as the variable is also being used
                        if type(closest_entity) is ServerPlayer:
                            print("=== Player hit ===")
                            print(f"Explosion at {rocket_explosion.pos - player.pos} hit by beam {beam.direction_vector}")
                            # Then also send a weapon message saying hit and draw a line shooting the other player
                            print(beam.direction_vector * rocket_explosion.power)
                            print(f"old vel {closest_entity.velocity}")
                            closest_entity.velocity = closest_entity.velocity + (beam.direction_vector * rocket_explosion.power)
                            print(f"new vel {closest_entity.velocity}")

        # clean up exploded projectiles
        for projectile in projectiles_to_explode:
            player.weapon.fired_projectiles.remove(projectile)

