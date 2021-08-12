import pygame, uuid, math, random

import client_server_communication, game_engine_constants, dev_constants, player, intersections, collisions, helpers, weapons, game_modes, textbox
from managers.manager import GameManager
from player import KillableServerPlayer


class ServerGameManager(GameManager):
    """This class in in charge of all server operations for a game

    #TODO make this an abstract class

    """

    def __init__(self, map_name, game_mode):
        super().__init__(map_name)
        self.game_mode = game_mode

    # TODO: Delete this and use the one from the manager class
    def construct_game_state_message(
        self,
    ) -> client_server_communication.GameStateNetworkMessage:
        """Collects and returns all the information about the current game state"""

        projectile_position_messages = []
        player_position_messages = []

        # Note: I was considering having a player lock here in case a player joined midway through and is added to the id_to_player list
        # but it's not an issue because if that's the case then their position won't be sent out to everyone until the next server tick which is fine
        players = self.id_to_player.values()

        for p in players:
            # TODO check if their position has changed since last time otherwise don't append it
            for projectile in p.weapons[0].fired_projectiles:
                projectile_position_messages.append(
                    client_server_communication.ProjectileNetworkMessage(
                        projectile.pos.x, projectile.pos.y
                    )
                )

            player_position_messages.append(
                client_server_communication.PlayerNetworkMessage(p)
            )

        game_state_message = client_server_communication.GameStateNetworkMessage(
            player_position_messages, projectile_position_messages, self.beam_messages
        )

        return game_state_message

    def add_player(self, client_socket):
        # Could this not being locked cause a problem?
        player_id = str(uuid.uuid1())
        spawn = random.choice(self.partitioned_map_grid.spawns)
        if type(self.game_mode) is game_modes.FirstToNFrags:
            self.id_to_player[player_id] = player.KillableServerPlayer(
                spawn.pos,
                game_engine_constants.TILE_SIZE,
                game_engine_constants.TILE_SIZE,
                player_id,
                client_socket,
            )
        else:
            self.id_to_player[player_id] = player.ServerPlayer(
                spawn.pos,
                game_engine_constants.TILE_SIZE,
                game_engine_constants.TILE_SIZE,
                player_id,
                client_socket,
            )
        print(f"added player {self.id_to_player}")

        # TODO this will probably be removed
        return player_id

    def perform_all_server_operations(
        self, time_since_last_iteration, input_message, game_state_queue=None
    ):  # None for if client is running this
        self.beam_messages = []  # reset beam messages
        players = [p for p in self.id_to_player.values() if not p.dead]
        self.consume_player_inputs(input_message)
        self.simulate_collisions(players)
        self.time_running += time_since_last_iteration  # measured in seconds

        if game_state_queue is not None:
            game_state_queue.put(self.construct_game_state_message())

    def consume_player_inputs(
        self, input_message: client_server_communication.InputNetworkMessage
    ):
        """Update the players attributes based on their input and operate their weapon if required"""
        player = self.id_to_player[input_message.player_id]
        net_x_movement = input_message.net_x_movement
        net_y_movement = input_message.net_y_movement
        time_since_last_client_frame = input_message.time_since_last_client_frame
        mouse_movement = input_message.mouse_movement
        firing = input_message.firing
        weapon_request = input_message.weapon_request
        text_message = input_message.text_message

        if type(self.game_mode) is game_modes.FirstToNFrags:
            if player.dead:
                player.time_dead += time_since_last_client_frame  # TODO don't do this the first time we find that they're dead?
                if player.time_dead >= self.game_mode.respawn_time:
                    # TODO turn this into a reset player method or something
                    player.dead = False
                    player.time_dead = 0
                    player.health = 100
                    spawn = random.choice(self.partitioned_map_grid.spawns)
                    player.pos = spawn.pos
                    player.velocity = pygame.math.Vector2(0, 0)
                return  # We don't deal with their inputs if they're dead

        self.update_player_attributes(
            player,
            net_x_movement,
            net_y_movement,
            time_since_last_client_frame,
            mouse_movement,
            text_message,
        )
        if (
            weapon_request != -1
        ):  # this means they haven't done a request # TODO add this to u_p_a above
            player.weapon = player.weapons[weapon_request]

        if firing:
            self.operate_player_weapon(player)

    def update_player_attributes(
        self,
        player,
        net_x_movement,
        net_y_movement,
        time_since_last_client_frame,
        mouse_movement,
        text_message,
    ):
        player.update_position(
            net_x_movement, net_y_movement, time_since_last_client_frame
        )
        player.update_aim(mouse_movement)
        player.weapon.time_since_last_shot += time_since_last_client_frame

        player.text_message = text_message

        # TODO Does using the players delta time make sense?
        # We should rather update this based on the server timestep?
        player.weapons[0].update_projectile_positions(time_since_last_client_frame)

    def operate_player_weapon(self, player):
        """Given a player, verify if the player is allowed to fire the weapon again, and if they are fire the weapon"""
        # TODO remove this once weapon switching is enabled
        if player.weapon.time_since_last_shot >= player.weapon.seconds_per_shot:
            player.weapon.time_since_last_shot = 0
            # TODO have an enum with the types of weapons associated with the firing action, then use that here
            if type(player.weapon) is weapons.Hitscan:
                self.analyze_hitscan_shot(player)
            elif (
                type(player.weapon) is weapons.RocketLauncher
            ):  # allowed because the only other weapon implemented is the rocket launcher
                player.weapon.fire_projectile()

    def analyze_hitscan_shot(self, firing_player):
        """Given the fact that a player is firing a hitscan weapon and has waited long enough (the shot is valid), check to see if the shot hits another player, if it does then apply a force to that player"""
        beam = firing_player.weapon.get_beam()

        if dev_constants.DEBUGGING_HITSCAN_WEAPON:
            dev_constants.BEAMS_FOR_DEBUGGING.append(beam)
            # pygame.draw.line(dev_constants.SCREEN_FOR_DEBUGGING, pygame.color.THECOLORS['green'], helpers.translate_point_for_camera(firing_player, beam.start_point), helpers.translate_point_for_camera(firing_player, beam.end_point))

        (
            closest_hit,
            closest_entity,
        ) = intersections.get_closest_intersecting_object_in_pmg(
            firing_player.weapon, self.partitioned_map_grid, beam
        )

        # if closest_hit is not None: # this is guranteed because it's bounded by the map extents
        self.beam_messages.append(
            client_server_communication.BeamMessage(beam.start_point, closest_hit)
        )

        # if type(closest_entity) is player.ServerPlayer:
        if type(closest_entity) is player.KillableServerPlayer:
            # Then also send a weapon message saying hit and draw a line shooting the other player
            hit_v = pygame.math.Vector2(0, 0)
            # Because from polar is in deg apparently ...
            # TODO add a polar version to pygame
            deg = firing_player.rotation_angle * 360 / math.tau
            hit_v.from_polar((firing_player.weapon.power, deg))
            closest_entity.velocity += hit_v
            if (
                type(self.game_mode) is game_modes.FirstToNFrags
                and firing_player is not closest_entity
            ):  # TODO more generally if it's a game mode where players should take damage
                closest_entity.health -= 60
                if closest_entity.health <= 0:
                    closest_entity.dead = True
                    firing_player.num_frags += 1

    def simulate_collisions(self, players):
        # remove players from parition - we will update the positions in the loop
        self.partitioned_map_grid.reset_players_in_partitions()

        n = len(players)

        # START UPDATE PARTITIONS
        for i in range(n):
            p1 = players[i]

            partition_idx_x, partition_idx_y = helpers.get_partition_index(
                self.partitioned_map_grid, p1.pos
            )

            # TODO the below fix stops the server from crashing,
            # but we can do better because this kind causes jerkyness?
            if not helpers.valid_2d_index_for_partitioned_map_grid(
                (partition_idx_x, partition_idx_y), self.partitioned_map_grid
            ):
                p1.pos = (
                    p1.previous_pos
                )  # TODO making a large assumption here, what hey don't have a prev pos?
                partition_idx_x, partition_idx_y = helpers.get_partition_index(
                    self.partitioned_map_grid, p1.pos
                )

            curr_partition = self.partitioned_map_grid.partitioned_map[partition_idx_y][
                partition_idx_x
            ]
            curr_collision_partition = (
                self.partitioned_map_grid.collision_partitioned_map[partition_idx_y][
                    partition_idx_x
                ]
            )
            # Put the player in the corresponding partition
            curr_partition.players.append(p1)

        # END UPDATE PARTITIONS

        for i in range(n):
            p1 = players[i]
            # Checks for collisions with other bodies
            for j in range(
                i + 1, n
            ):  # Note that in combination with the outer for loop this iterates through each pair of players only once
                # TODO only have to check within the collision partitions
                # TODO need a way to generate collision partitions given a point
                p2 = players[j]
                if collisions.bodies_colliding(p1.pos, p1.radius, p2.pos, p2.radius):
                    collisions.elastic_collision_update(p1, p2)

            partition_idx_x, partition_idx_y = helpers.get_partition_index(
                self.partitioned_map_grid, p1.pos
            )
            curr_collision_partition = (
                self.partitioned_map_grid.collision_partitioned_map[partition_idx_y][
                    partition_idx_x
                ]
            )

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
        collided = False
        for rocket in player.weapons[0].fired_projectiles:
            projectile_idx_x, projectile_idx_y = helpers.get_partition_index(
                self.partitioned_map_grid, rocket.pos
            )
            # TODO protect this incase a projectile gets out of the map, if outside map then delete it?:
            projectile_partition = self.partitioned_map_grid.collision_partitioned_map[
                projectile_idx_y
            ][projectile_idx_x]
            temp_projectile_partition = self.partitioned_map_grid.partitioned_map[
                projectile_idx_y
            ][
                projectile_idx_x
            ]  # TODO we need to actually use collision partitions for this

            for partition_player in temp_projectile_partition.players:
                if (
                    partition_player is not player
                ):  # you don't collide with your own rockets
                    if collisions.bodies_colliding(
                        rocket.pos,
                        rocket.radius,
                        partition_player.pos,
                        partition_player.radius,
                    ):
                        collided = True
                        projectiles_to_explode.add(rocket)
                        if rocket.previous_pos is not None:
                            rocket_explosion = weapons.Explosion(rocket.previous_pos)
                        else:
                            rocket_explosion = weapons.Explosion(rocket.pos)
                        for (
                            beam
                        ) in (
                            rocket_explosion.beams
                        ):  # TODO move all this code to a function do_explosion or something
                            (
                                closest_hit,
                                closest_entity,
                            ) = intersections.get_closest_intersecting_object_in_pmg(
                                player.weapon, self.partitioned_map_grid, beam
                            )
                            if closest_hit is not None:
                                self.beam_messages.append(
                                    client_server_communication.BeamMessage(
                                        beam.start_point, closest_hit
                                    )
                                )
                            else:
                                self.beam_messages.append(
                                    client_server_communication.BeamMessage(
                                        beam.start_point, beam.end_point
                                    )
                                )
                            if closest_hit is not None:
                                if dev_constants.DEBUGGING_INTERSECTIONS:
                                    dev_constants.INTERSECTIONS_FOR_DEBUGGING.append(
                                        closest_hit
                                    )

                            # Have to import this because player.ServerPlayer wouldn't work as the variable is also being used
                            # if type(closest_entity) is ServerPlayer:
                            if type(closest_entity) is KillableServerPlayer:
                                closest_entity.velocity = closest_entity.velocity + (
                                    beam.direction_vector * rocket_explosion.power
                                )
                                if (
                                    type(self.game_mode) is game_modes.FirstToNFrags
                                    and player is not closest_entity
                                ):  # TODO more generally if it's a game mode where players should take damage
                                    closest_entity.health -= 10
                                    if closest_entity.health <= 0:
                                        closest_entity.dead = True
                                        player.num_frags += 1

            if not collided:
                for p_wall in projectile_partition.bounding_walls:

                    colliding, closest_v = collisions.colliding_and_closest(
                        rocket, p_wall
                    )
                    if colliding:

                        # TODO don't change the position of the rocket
                        # Means we have to change all isntances of the call to colliding_and_closest
                        if rocket.previous_pos is not None:
                            rocket.pos = helpers.copy_vector(
                                rocket.previous_pos
                            )  # this isn't colliding
                        else:
                            rocket.pos = helpers.copy_vector(player.pos)

                        colliding, closest_v = collisions.colliding_and_closest(
                            rocket, p_wall
                        )

                        projectiles_to_explode.add(rocket)

                        rocket_explosion = weapons.Explosion(closest_v)

                        if dev_constants.CLIENT_VISUAL_DEBUGGING:
                            dev_constants.EXPLOSIONS_FOR_DEBUGGING.append(
                                rocket_explosion
                            )
                        for beam in rocket_explosion.beams:
                            (
                                closest_hit,
                                closest_entity,
                            ) = intersections.get_closest_intersecting_object_in_pmg(
                                player.weapon, self.partitioned_map_grid, beam
                            )
                            if closest_hit is not None:
                                self.beam_messages.append(
                                    client_server_communication.BeamMessage(
                                        beam.start_point, closest_hit
                                    )
                                )
                            else:
                                self.beam_messages.append(
                                    client_server_communication.BeamMessage(
                                        beam.start_point, beam.end_point
                                    )
                                )
                            if closest_hit is not None:
                                if dev_constants.DEBUGGING_INTERSECTIONS:
                                    dev_constants.INTERSECTIONS_FOR_DEBUGGING.append(
                                        closest_hit
                                    )

                            # Have to import this because player.ServerPlayer wouldn't work as the variable is also being used
                            # if type(closest_entity) is ServerPlayer:
                            if type(closest_entity) is KillableServerPlayer:
                                closest_entity.velocity = closest_entity.velocity + (
                                    beam.direction_vector * rocket_explosion.power
                                )
                                if (
                                    type(self.game_mode) is game_modes.FirstToNFrags
                                    and player is not closest_entity
                                ):  # TODO more generally if it's a game mode where players should take damage
                                    closest_entity.health -= 10
                                    if closest_entity.health <= 0:
                                        closest_entity.dead = True
                                        player.num_frags += 1

        # clean up exploded projectiles
        for projectile in projectiles_to_explode:
            player.weapons[0].fired_projectiles.remove(projectile)


class WinnableServerGameManager(ServerGameManager):  # TODO abstract class
    def perform_all_server_operations(
        self, time_since_last_iteration, input_message, game_state_queue=None
    ):  # None for if client is running this
        self.beam_messages = []  # reset beam messages
        players = list(self.id_to_player.values())
        self.consume_player_inputs(input_message)
        self.simulate_collisions(players)
        game_over, winner = self.is_game_over()
        if game_over:  # TODO figure this out with a type of switch or something
            print(
                f"GAME OVER, winner is {winner.player_id}"
            )  # and stop everything. kill this thread?
            quit()

        if game_state_queue is not None:
            game_state_queue.put(self.construct_game_state_message())

        self.time_running += time_since_last_iteration  # measured in seconds

    def is_game_over(self):  # abstract method
        raise NotImplementedError


class TimedDMServerGameManager(WinnableServerGameManager):
    def is_game_over(self):
        pass  # check if time running is past a certain cut off


class FirstToNFragsDMServerGameManager(WinnableServerGameManager):
    def __init__(self, map_name):
        super().__init__(map_name, game_modes.FirstToNFrags(10))

    def is_game_over(self):
        """Figures out if the game is over and if it is then return who the winner is"""
        player_to_frag_count = {p: p.num_frags for p in self.id_to_player.values()}
        for player, frag_count in player_to_frag_count.items():
            if (
                frag_count >= self.game_mode.frags_to_win
            ):  # TODO what if multiple people die in the same tick making many winners - this only returns the first winner based on the list ordering
                return (True, player)
        return (False, None)
