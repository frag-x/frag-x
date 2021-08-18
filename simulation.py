from collections import defaultdict
from typing import Optional, Tuple, List

import pygame

import collisions
import game_engine_constants
import helpers
import map_loading
import random

from body import Body
from comms import message
from simulation_object.simulation_object import SimulationObject
from simulation_object.player import ServerPlayer
from simulation_object.rocket import Rocket
from simulation_object.hitscan_beam import HitscanBeam


class Simulation:
    def __init__(self, map_name, input_messages, output_messages):
        self.map = self._load_map(map_name)
        self.input_messages = input_messages
        self.output_messages = output_messages
        self.clock = pygame.time.Clock()

        self.players = {}
        self.rockets = {}
        self.hitscan_beams = {}

        self.type_to_dict = {
            ServerPlayer: self.players,
            Rocket: self.rockets,
            HitscanBeam: self.hitscan_beams,
        }

    def _load_map(self, map_name):
        map_fullpath = f"{game_engine_constants.MAP_PREFIX}{map_name}"
        return map_loading.PartitionedMapGrid(
            map_loading.get_pixels(map_fullpath), 10, 10
        )

    def _process_input_message(self, input_message: message.ServerMessage) -> None:
        if type(input_message) == message.PlayerStateMessage:
            player = self.players[input_message.player_id]
            player.update(input_message)
        elif type(input_message) == message.PlayerTextMessage:
            self.output_messages.put(input_message)
        else:
            raise message.UnknownMessageTypeError(type(input_message))

    def _make_output_message(self) -> message.SimulationStateMessage:
        return message.SimulationStateMessage(
            players=[player.to_network_object() for player in self.players.values()],
            rockets=[rocket.to_network_object() for rocket in self.rockets.values()],
            hitscan_beams=[
                hitscan_beam.to_network_object()
                for hitscan_beam in self.hitscan_beams.values()
            ],
        )

    def register_object(self, object: SimulationObject) -> None:
        target_dict = self.type_to_dict[type(object)]
        if object.uuid in target_dict:
            raise Exception("Object {object} registered twice!")
        target_dict[object.uuid] = object

    def deregister_object(self, object: SimulationObject) -> None:
        target_dict = self.type_to_dict[type(object)]
        if object.uuid not in target_dict:
            raise Exception("Object {object} not found while deregistering!")
        del target_dict[object.uuid]

    def add_player(self, client_socket):
        spawn = random.choice(self.map.spawns)
        player = ServerPlayer(
            spawn.position,
            game_engine_constants.TILE_SIZE,
            game_engine_constants.TILE_SIZE,
            client_socket,
        )
        return player.uuid

    def remove_player(self, player):
        self.deregister_object(player)

    def get_players(self):
        return list(self.players.values())

    def get_partition(
        self, position: pygame.math.Vector2
    ) -> map_loading.MapGridPartition:
        """
        Precondition: The position must be inside the map, or else this function will fail

        return the partition that the player is within

        :param position:
        :return:
        """

        partition_idx_x, partition_idx_y = helpers.get_partition_index(
            self.map.partition_width, self.map.partition_height, position
        )

        return self.map.partitioned_map[partition_idx_y][partition_idx_x]

    def get_collision_partition(
        self, position: pygame.math.Vector2
    ) -> map_loading.MapGridPartition:
        """
        Precondition: The position must be inside the map, or else this function will fail

        return the collision partition that the player is within

        :param position:
        :return:
        """

        partition_idx_x, partition_idx_y = helpers.get_partition_index(
            self.map.partition_width, self.map.partition_height, position
        )

        return self.map.collision_partitioned_map[partition_idx_y][partition_idx_x]

    def get_colliding_elements(
        self, body: Body, partition: map_loading.MapGridPartition
    ) -> List[SimulationObject]:
        """
        Check if the given body is colliding with anything in this partition, if the player is colliding
        then return what they are colliding with

        :param body:
        :param partition:
        :return:
        """
        colliding_objects = []
        for b_wall in partition.bounding_walls:
            if collisions.is_colliding_with_wall(body, b_wall):
                colliding_objects.append(b_wall)
        return colliding_objects

    def _update_bodies_in_partitions(self):
        bodies: List[Body] = [*self.players.values(), *self.rockets.values()]
        for body in bodies:
            body.partition = self.get_partition(body.position)
            body.collision_partition = self.get_collision_partition(body.position)

    def step(self):
        delta_time = self.clock.tick(game_engine_constants.SERVER_TICK_RATE_HZ)
        current_time = pygame.time.get_ticks()
        self.hitscan_beams.clear()

        while not self.input_messages.empty():
            self._process_input_message(self.input_messages.get())

        self._update_bodies_in_partitions()

        # it's possible for an object to deregister itself during step,
        # so these could change size during iteration
        players = list(self.players.values())
        for player in players:
            player.step(delta_time, current_time)

        rockets = list(self.rockets.values())
        for rocket in rockets:
            rocket.step(delta_time, current_time)

        hitscan_beams = list(self.hitscan_beams.values())
        for hitscan_beam in hitscan_beams:
            hitscan_beam.step(delta_time, current_time)

        output_message = self._make_output_message()

        self.output_messages.put(output_message)