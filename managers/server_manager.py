import pygame, uuid, math, random

import game_engine_constants
import dev_constants
import collisions
import intersections
import game_modes
import weapons
import player
import helpers

from managers.manager import GameManager
from player import KillableServerPlayer
from comms import message


class ServerGameManager(GameManager):
    """This class in in charge of all server operations for a game

    #TODO make this an abstract class

    """

    def __init__(self, map_name, game_mode):
        super().__init__(map_name)
        self.game_mode = game_mode

    def construct_output_message(
        self,
    ) -> message.ServerStateMessage:
        """Collects and returns all the information about the current game state"""

        server_state_message = message.ServerStateMessage()

        # TODO: should probably lock here
        for player in self.get_players():
            # TODO: only send changed positions?
            for projectile in player.weapons[0].fired_projectiles:
                server_state_message.projectile_states.append(
                    message.ProjectileState(projectile.pos.x, projectile.pos.y)
                )

            for beam in player.beam_states:
                server_state_message.beam_states.append(
                    message.BeamState(
                        start_x=beam.start_point.x,
                        start_y=beam.start_point.y,
                        end_x=beam.end_point.x,
                        end_y=beam.end_point.y,
                    )
                )

            server_state_message.player_states.append(
                message.PlayerState(
                    player_id=player.player_id,
                    x=player.pos.x,
                    y=player.pos.y,
                    rotation=player.rotation_angle,
                    weapon_selection=player.weapon_selection,
                )
            )

        return server_state_message

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
        print(f"Player {self.id_to_player[player_id]} joined")

        return player_id

    def perform_all_server_operations(self, delta_time, input_message, output_messages):
        players = [p for p in self.get_players() if not p.dead]

        if type(input_message) == message.PlayerStateMessage:
            self.consume_player_input(input_message)
        elif type(input_message) == message.PlayerTextMessage:
            output_messages.put(input_message)
        else:
            raise message.UnknownMessageTypeError

        self.simulate_collisions(players)
        self.time_running += delta_time

        output_messages.put(self.construct_output_message())

    def consume_player_input(self, input_message: message.ClientMessage):
        """Update the players attributes based on their input and operate their weapon if required"""
        player = self.id_to_player[input_message.player_id]
        delta_x = input_message.delta_x
        delta_y = input_message.delta_y
        delta_time = input_message.delta_time
        delta_mouse = input_message.delta_mouse
        firing = input_message.firing
        weapon_selection = input_message.weapon_selection

        if type(self.game_mode) is game_modes.FirstToNFrags:
            if player.dead:
                player.time_dead += delta_time  # TODO: don't do this the first time we find that they're dead?
                if player.time_dead >= self.game_mode.respawn_time:
                    # TODO: turn this into a reset player method or something
                    player.dead = False
                    player.time_dead = 0
                    player.health = 100
                    spawn = random.choice(self.partitioned_map_grid.spawns)
                    player.pos = spawn.pos
                    player.velocity = pygame.math.Vector2(0, 0)
                return  # We don't deal with their inputs if they're dead

        self.update_player_attributes(
            player,
            delta_x,
            delta_y,
            delta_time,
            delta_mouse,
        )

        player.weapon_selection = weapon_selection

        if firing:
            self.operate_player_weapon(player)


    def update_player_attributes(
        self,
        player,
        delta_x,
        delta_y,
        delta_time,
        delta_mouse,
    ):
        player.update_position(delta_x, delta_y, delta_time)
        player.update_aim(delta_mouse)
        player.weapons[player.weapon_selection].time_since_last_shot += delta_time

        # TODO Does using the players delta time make sense? NO.
        # We should rather update this based on the server timestep?
        player.weapons[0].update_projectile_positions(delta_time)

    def operate_player_weapon(self, player):
        """Given a player, verify if the player is allowed to fire the weapon again, and if they are fire the weapon"""
        # TODO remove this once weapon switching is enabled
        weapon = player.weapons[player.weapon_selection]
        if weapon.time_since_last_shot >= weapon.seconds_per_shot:
            weapon.time_since_last_shot = 0
            # TODO have an enum with the types of weapons associated with the firing action, then use that here
            if type(weapon) is weapons.Hitscan:
                player.beam_states.append(self.analyze_hitscan_shot(player))
            elif (
                type(weapon) is weapons.RocketLauncher
            ):  # allowed because the only other weapon implemented is the rocket launcher
                weapon.fire_projectile()

    def analyze_hitscan_shot(self, firing_player):
        """Given the fact that a player is firing a hitscan weapon and has waited long enough (the shot is valid), check to see if the shot hits another player, if it does then apply a force to that player"""
        weapon = firing_player.weapons[firing_player.weapon_selection]
        beam = weapon.get_beam()

        if dev_constants.DEBUGGING_HITSCAN_WEAPON:
            dev_constants.BEAMS_FOR_DEBUGGING.append(beam)
            # pygame.draw.line(dev_constants.SCREEN_FOR_DEBUGGING, pygame.color.THECOLORS['green'], helpers.translate_point_for_camera(firing_player, beam.start_point), helpers.translate_point_for_camera(firing_player, beam.end_point))

        (
            closest_hit,
            closest_entity,
        ) = intersections.get_closest_intersecting_object_in_pmg(
            weapon, self.partitioned_map_grid, beam
        )

        # if type(closest_entity) is player.ServerPlayer:
        if type(closest_entity) is player.KillableServerPlayer:
            # Then also send a weapon message saying hit and draw a line shooting the other player
            hit_v = pygame.math.Vector2(0, 0)
            # Because from polar is in deg apparently ...
            # TODO add a polar version to pygame
            deg = firing_player.rotation_angle * 360 / math.tau
            hit_v.from_polar((weapon.power, deg))
            closest_entity.velocity += hit_v
            if (
                type(self.game_mode) is game_modes.FirstToNFrags
                and firing_player is not closest_entity
            ):  # TODO more generally if it's a game mode where players should take damage
                closest_entity.health -= 60
                if closest_entity.health <= 0:
                    closest_entity.dead = True
                    firing_player.num_frags += 1

        beam.end_point = closest_hit

        return beam

    def simulate_collisions(self, players):
        # remove players from parition - we will update the positions in the loop
        self.partitioned_map_grid.reset_players_in_partitions()

        for player in players:
            partition_idx_x, partition_idx_y = helpers.get_partition_index(
                self.partitioned_map_grid, player.pos
            )

            # TODO the below fix stops the server from crashing,
            # but we can do better because this kind causes jerkyness?
            if not helpers.valid_2d_index_for_partitioned_map_grid(
                (partition_idx_x, partition_idx_y), self.partitioned_map_grid
            ):
                player.pos = (
                    player.previous_pos
                )  # TODO making a large assumption here, what hey don't have a prev pos?
                partition_idx_x, partition_idx_y = helpers.get_partition_index(
                    self.partitioned_map_grid, player.pos
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
            curr_partition.players.append(player)

        # END UPDATE PARTITIONS

        for i, p1 in enumerate(players):
            # Checks for collisions with other bodies
            for j in range(
                i + 1, len(players)
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

                            player.beam_states.append(beam)

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
                                player.weapons[player.weapon_selection],
                                self.partitioned_map_grid,
                                beam,
                            )

                            player.beam_states.append(beam)

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
        self, time_since_last_iteration, input_message, output_messages=None
    ):  # None for if client is running this
        players = self.get_players()
        for player in players:
            player.beam_states = []

        if type(input_message) == message.PlayerStateMessage:
            self.consume_player_input(input_message)
        elif type(input_message) == message.PlayerTextMessage:
            output_messages.put(input_message)
        else:
            raise message.UnknownMessageTypeError

        self.simulate_collisions(players)
        game_over, winner = self.is_game_over()
        if game_over:  # TODO figure this out with a type of switch or something
            print(
                f"GAME OVER, winner is {winner.player_id}"
            )  # and stop everything. kill this thread?
            quit()

        output_messages.put(self.construct_output_message())

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
        player_to_frag_count = {p: p.num_frags for p in self.get_players()}
        for player, frag_count in player_to_frag_count.items():
            if (
                frag_count >= self.game_mode.frags_to_win
            ):  # TODO what if multiple people die in the same tick making many winners - this only returns the first winner based on the list ordering
                return (True, player)
        return (False, None)
