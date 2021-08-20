import pygame, math, uuid, random
import collisions, global_simulation
from comms.message import PlayerStateMessage
import game_engine_constants, body
from simulation_object import constants
from weapons.railgun import RailGun
from weapons.rocket_launcher import RocketLauncher
from simulation_object.simulation_object import SimulationObject
import simulation_object.constants
from abc import ABC

from network_object.player import PlayerNetworkObject
from weapons.shotgun import ShotGun


class Player(SimulationObject, body.ConstantAccelerationBody):
    def __init__(self, start_position, socket):
        super().__init__()
        super(ABC, self).__init__(
            start_position, game_engine_constants.PLAYER_RADIUS, 0.05, 1000
        )
        self.health = 100
        self.time_of_death = None

        self.socket = socket

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

        self.beams = []

    def __str__(self):
        return f"{str(self.uuid)[:4]}: {self.num_frags}"

    def is_dead(self) -> bool:
        return self.time_of_death is not None

    def to_network_object(self):
        return PlayerNetworkObject(
            uuid=self.uuid,
            position=self.position,
            rotation=self.rotation,
            weapon_selection=self.weapon_selection,
            num_frags=self.num_frags,
        )

    def update(self, input_message: PlayerStateMessage):
        self.movement_request = pygame.math.Vector2(input_message.delta_position)
        self.rotation_request = input_message.delta_mouse
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
        global_simulation.SIMULATION.get_partition(self.position).players.append(self)
        global_simulation.SIMULATION.get_collision_partition(
            self.position
        ).players.append(self)

        super(ABC, self).step(self.movement_request, delta_time)
        self.movement_request = pygame.math.Vector2(0, 0)

        self.rotation += self.rotation_request
        self.rotation %= math.tau

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
            # TODO make this a player method
            collisions.simulate_collision_v2(self, colliding_wall)
        for colliding_player in colliding_players:
            collisions.elastic_collision_update(self, colliding_player)
