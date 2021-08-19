from collections import defaultdict, Counter
from queue import Queue
from typing import List, cast, Tuple, Dict

from comms.message import SimulationStateMessage
from map_loading import BoundingWall
from uuid import UUID
from typing import Optional

import pygame

import collisions
import game_engine_constants
import helpers
import map_loading
import random

from body import Body
from comms import message
from simulation_object.simulation_object import SimulationObject
from simulation_object.player import Player
from simulation_object.rocket import Rocket
from simulation_object.hitscan_beam import HitscanBeam
from network_object.hitscan_beam import HitscanBeamNetworkObject


class Simulation:
    def __init__(
        self, map_name: str, input_messages: Queue, output_messages: Queue, players={}
    ):
        self.map_name = map_name
        self.map = map_loading.load_map(map_name)
        self.input_messages = input_messages
        self.output_messages = output_messages
        self.clock = pygame.time.Clock()
        self.active = False

        self.players: Dict[UUID, Player] = players
        for player in players.values():
            player.position = random.choice(self.map.spawns).position

        self.rockets: Dict[UUID, Rocket] = {}
        self.hitscan_beams: Dict[UUID, HitscanBeam] = {}

        self.type_to_dict = {
            Player: self.players,
            Rocket: self.rockets,
            HitscanBeam: self.hitscan_beams,
        }

    def _process_input_message(self, input_message: message.ServerMessage) -> None:
        """
        Given a message which comes from the client, read this message and update the game accordingly

        :param input_message:
        :return:
        """
        if type(input_message) == message.PlayerStateMessage:
            player = self.players[input_message.player_id]
            player.update(input_message)
        elif type(input_message) == message.PlayerTextMessage:
            self.output_messages.put(input_message)
        else:
            raise message.UnknownMessageTypeError(type(input_message))

    def _process_output_message(self, output_message: SimulationStateMessage) -> None:
        """
        This client is used for a client side simulation, when the real server sends an output message
        we take that message and use it to update the simulation

        :param output_message:
        :return:
        """
        for player in output_message.players:
            if player.uuid not in self.players:
                Player
                self.add_player()

    def _make_output_message(self) -> message.SimulationStateMessage:
        return message.SimulationStateMessage(
            players={
                uuid: player.to_network_object()
                for uuid, player in self.players.items()
            },
            rockets={
                uuid: rocket.to_network_object()
                for uuid, rocket in self.rockets.items()
            },
            hitscan_beams={
                uuid: cast(HitscanBeamNetworkObject, hitscan_beam.to_network_object())
                for uuid, hitscan_beam in self.hitscan_beams.items()
            },
        )

    def register_object(self, object: SimulationObject) -> None:
        target_dict = self.type_to_dict[type(object)]
        if object.uuid in target_dict:  # type: ignore
            raise Exception("Object {object} registered twice!")
        target_dict[object.uuid] = object  # type: ignore

    def deregister_object(self, object: SimulationObject) -> None:
        target_dict = self.type_to_dict[type(object)]
        if object.uuid not in target_dict:  # type: ignore
            raise Exception("Object {object} not found while deregistering!")
        del target_dict[object.uuid]  # type: ignore

    def add_player(self, client_socket=None):
        """
        Add a player to the simulation, client_socket is optional for when
        you are running a simulation locally and you don't need to send out messages

        :param client_socket:
        :return:
        """
        spawn = random.choice(self.map.spawns)
        player = Player(
            spawn.position,
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

    def clear_partitions(self):
        map_partitions = [self.map.partitioned_map, self.map.collision_partitioned_map]
        for partitioned_map in map_partitions:
            for partition_row in partitioned_map:
                for partition in partition_row:
                    partition.players = []

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
    ) -> Tuple[List[BoundingWall], List[Player]]:
        """
        Check if the given body is colliding with anything in this partition, if the player is colliding
        then return what they are colliding with

        :param body:
        :param partition:
        :return:
        """

        partition = self.get_partition(body.position)
        collision_partition = self.get_collision_partition(body.position)

        colliding_b_walls = []
        for b_wall in collision_partition.bounding_walls:
            if collisions.is_colliding_with_wall(body, b_wall):
                colliding_b_walls.append(b_wall)

        colliding_players = []
        for player in partition.players:
            if collisions.bodies_colliding(body, player) and body is not player:
                colliding_players.append(player)

        return colliding_b_walls, colliding_players

    def _enact_player_requests(self, players) -> Tuple[bool, Optional[str]]:
        if players:
            if not self.active and all(player.ready for player in players):
                self.active = True
                self.output_messages.put(message.ServerStatusMessage(status="active"))

            map_votes = Counter(player.map_vote for player in players)
            top_map_vote, vote_count = map_votes.most_common(1)[0]
            if (
                top_map_vote is not None
                and top_map_vote != self.map_name
                and cast(float, vote_count) >= len(players) / 2
            ):

                return False, cast(str, top_map_vote)
        return True, None

    def step(self) -> Tuple[bool, Optional[str]]:
        delta_time = self.clock.tick(game_engine_constants.SERVER_TICK_RATE_HZ)
        self.hitscan_beams.clear()

        self.clear_partitions()

        while not self.input_messages.empty():
            self._process_input_message(self.input_messages.get())

        # it's possible for an object to deregister itself during step,
        # so these could change size during iteration
        players = list(self.players.values())
        keep_map, requested_new_map = self._enact_player_requests(players)

        if self.active:
            for player in players:
                if not player.is_dead():
                    player.step(delta_time)

            rockets = list(self.rockets.values())
            for rocket in rockets:
                rocket.step(delta_time)

            hitscan_beams = list(self.hitscan_beams.values())
            for hitscan_beam in hitscan_beams:
                hitscan_beam.step(delta_time)

        output_message = self._make_output_message()
        self.output_messages.put(output_message)

        return keep_map, requested_new_map
