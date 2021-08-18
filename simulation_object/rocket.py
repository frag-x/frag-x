from abc import ABC
import math

import collisions
import global_simulation
from map_loading import BoundingWall
from network_object.rocket import RocketNetworkObject

import pygame

import helpers
from body import ConstantVelocityBody
import weapons.constants
from simulation_object.simulation_object import SimulationObject
from weapons import constants
from weapons.weapon import HitscanBeam


class Rocket(SimulationObject, ConstantVelocityBody):
    """
    A rocket is a type of projectile which moves with constant velocity, it's payload is an explosion
    """

    def __init__(
        self,
        player,
        radius: float,
        speed: int,
        direction: pygame.math.Vector2,
        num_shards: int,
    ):
        """
        Initializes a rocket

        :param player: the player which fired the rocket
        :param radius: how large the rocket is
        :param speed: the speed at which the rocket moves
        :param direction: a unit vector representing the direction the rocket will move
        """
        super().__init__()
        super(SimulationObject, self).__init__(
            start_pos=player.position,
            radius=radius,
            friction=0,
            velocity=direction * speed,
        )
        self.player = player  # TODO eventually OwnedSimulation Object
        self.num_shards = num_shards

    def explode(self, position: pygame.math.Vector2):
        angle_fraction = math.tau / self.num_shards
        for i in range(self.num_shards):
            angle = angle_fraction * i
            x, y = helpers.polar_to_cartesian(constants.ROCKET_EXPLOSION_RADIUS, angle)
            relative_shard_vec = pygame.math.Vector2(x, y)
            shard_vec = relative_shard_vec + position
            HitscanBeam(
                self.player,
                position,
                shard_vec,
                weapons.constants.ROCKET_EXPLOSION_COLLISION_FORCE,
                weapons.constants.ROCKET_EXPLOSION_DAMAGE,
            )  # note this adds it to the simulation
        global_simulation.SIMULATION.deregister_object(self)

    def to_network_object(self) -> RocketNetworkObject:
        return RocketNetworkObject(
            uuid=self.uuid,
            position=self.position,
        )

    def step(self, delta_time: float, current_time: float):  # type: ignore

        super(ABC, self).step(delta_time)

        self.partition = global_simulation.SIMULATION.get_partition(self.position)
        self.collision_partition = global_simulation.SIMULATION.get_collision_partition(
            self.position
        )

        # Right here self.partition.players.append()

        colliding_elements = global_simulation.SIMULATION.get_colliding_elements(
            self, self.partition
        )

        # TODO think about cases when hitting multiple objects at once
        for colliding_element in colliding_elements:
            if type(colliding_element) is BoundingWall:
                bounding_wall = colliding_element
                self.position = (
                    self.previous_position
                )  # move to the point where it wasn't colliding
                collision_point = collisions.get_closest_point_on_wall(
                    self, bounding_wall
                )
                self.explode(collision_point)
                break
