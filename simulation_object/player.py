from weapons.weapon import HitscanBeam
import pygame
import random
import socket
import collisions
import global_simulation
from comms.message import PlayerStateMessage
import game_engine_constants
import body
from simulation_object import constants
from weapons.railgun import RailGun
from weapons.rocket_launcher import RocketLauncher
from simulation_object.simulation_object import SimulationObject
import simulation_object.constants
from abc import ABC
from typing import Any

from network_object.player import PlayerNetworkObject
from weapons.shotgun import ShotGun


class Player(SimulationObject, body.ConstantAccelerationBody):
    def __init__(
        self,
        start_position: pygame.math.Vector2,
        socket: socket.socket,
        client_addr: tuple[Any, Any],
    ):
        super().__init__()
        super(ABC, self).__init__(
            start_position, game_engine_constants.PLAYER_RADIUS, 0.05, 1500
        )
        self.health = 100
        self.time_of_death = None

        self.socket = socket
        self.tcp_addr = client_addr
        self.udp_addr: tuple[Any, Any] | None = None

        self.rotation = 0

        self.movement_request = pygame.math.Vector2(0, 0)
        self.rotation_request = 0
        self.firing_request = False

        self.ready = False
        self.map_vote = None
        self.num_frags = 0

        self.weapons = [
            RocketLauncher(),
            RailGun(),
            ShotGun(),
        ]
        self.weapon_selection = 0

        self.beams: list[HitscanBeam] = []

        self.color = random.choice(simulation_object.constants.PLAYER_COLORS)

    def reset(self, spawn_position: pygame.math.Vector2) -> None:
        # TODO should this get called as part of init?
        self.position = spawn_position
        self.health = 100
        self.time_of_death = None
        self.rotation = 0
        self.ready = False
        self.map_vote = None
        self.num_frags = 0

    def is_dead(self) -> bool:
        return self.time_of_death is not None

    def to_network_object(self) -> PlayerNetworkObject:
        return PlayerNetworkObject(
            uuid=self.uuid,
            position=self.position,
            rotation=self.rotation,
            weapon_selection=self.weapon_selection,
            health=self.health,
            num_frags=self.num_frags,
            color=self.color,
        )

    def set_udp(self, udp_addr: tuple[Any, Any]) -> None:
        if self.udp_addr is None:
            self.udp_addr = udp_addr

    def update(self, input_message: PlayerStateMessage) -> None:
        self.movement_request = pygame.math.Vector2(input_message.delta_position)
        self.rotation = input_message.rotation
        self.weapon_selection = input_message.weapon_selection
        self.firing_request = input_message.firing
        self.ready = input_message.ready
        self.map_vote = input_message.map_vote

        if self.time_of_death is not None:
            if (
                pygame.time.get_ticks() - self.time_of_death
            ) / 1000 >= simulation_object.constants.PLAYER_DEATH_SECONDS:
                self.time_of_death = None  # alive again
                self.position = random.choice(
                    global_simulation.SIMULATION.map.spawns
                ).position
                self.health = constants.PLAYER_HEALTH

    def step(self, delta_time: float):  # type: ignore
        partition = global_simulation.SIMULATION.get_partition(self.position)

        if partition:
            partition.players.append(self)
        else:
            self.position = random.choice(
                global_simulation.SIMULATION.map.spawns
            ).position
            global_simulation.SIMULATION.get_partition(self.position).append(self)

        collision_partition = global_simulation.SIMULATION.get_collision_partition(
            self.position
        )

        collision_partition.players.append(self)

        # if collision_partition:
        #    collision_partition.players.append(self)
        # else:
        #    self.position = random.choice(
        #        global_simulation.SIMULATION.map.spawns
        #    ).position
        #    global_simulation.SIMULATION.get_collision_partition(self.position).append(
        #        self
        #    )

        super(ABC, self).step(self.movement_request, delta_time)
        self.movement_request = pygame.math.Vector2(0, 0)

        if self.firing_request:
            self.weapons[self.weapon_selection].try_fire(
                self,
                self.rotation,
            )

        (
            colliding_walls,
            colliding_players,
        ) = global_simulation.SIMULATION.get_colliding_elements(
            self, self.collision_partition
        )

        for colliding_wall in colliding_walls:
            collisions.simulate_collision(self, colliding_wall)
        for colliding_player in colliding_players:
            collisions.elastic_collision_update(self, colliding_player)
