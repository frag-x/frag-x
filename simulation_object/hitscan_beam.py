from dataclasses import dataclass
import pygame
import helpers

from network_object.network_object import NetworkObject
from network_object.hitscan_beam import HitscanBeamNetworkObject
from simulation_object.simulation_object import SimulationObject
import weapons.constants


class HitscanBeam(SimulationObject):
    """A hitscan beam is a shot from a weapon"""

    def __init__(
        self,
        player,
        start_point: pygame.math.Vector2,
        end_point: pygame.math.Vector2,
        collision_force=weapons.constants.RAILGUN_COLLISION_FORCE,
        damage=weapons.constants.RAILGUN_DAMAGE,
    ):
        super().__init__()

        self.delta_y = end_point[1] - start_point[1]
        self.delta_x = end_point[0] - start_point[0]

        self.direction_vector = (end_point - start_point).normalize()

        self.start_point = start_point
        self.end_point = end_point

        self.damage = damage

        self.collision_force = collision_force

        self.slope = helpers.get_slope(start_point, end_point)

        self.quadrant_info = (
            helpers.get_sign(self.delta_x),
            helpers.get_sign(self.delta_y),
        )

    def to_network_object(self) -> NetworkObject:
        return HitscanBeamNetworkObject(
            uuid=self.uuid,
            start_point=self.start_point,
            end_point=self.end_point,
        )

    def step(self, delta_time: float, current_time: float):
        pass
