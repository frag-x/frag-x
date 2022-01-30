import math

import pygame

import weapons.constants
from weapons.weapon import Weapon
from simulation_object.rocket import Rocket
from typing import Any


class RocketLauncher(Weapon):
    """
    A rocket launcher is a weapon which shoots rockets
    """

    def __init__(self) -> None:
        super().__init__(fire_rate_hz=weapons.constants.ROCKET_LAUNCHER_FIRE_RATE_HZ)

    # NOTE: firing player can't be more strictly typed without creating a dependancy cycle
    def fire(self, firing_player: Any, aim_angle: float) -> Rocket:
        """
        Return a fired rocket
        :param firing_player: the player that fired the rocket launcher
        :param aim_angle: the angle that the rocket should be shot at
        :return: the fired rocket
        """
        aim_vector = pygame.math.Vector2(0, 0)
        aim_angle_deg = aim_angle * 360 / math.tau
        aim_vector.from_polar((1, aim_angle_deg))  # unit vector
        return Rocket(
            firing_player,
            radius=weapons.constants.ROCKET_RADIUS,
            speed=weapons.constants.ROCKET_SPEED,
            direction=aim_vector,
            num_shards=weapons.constants.ROCKET_EXPLOSION_SHARDS,
        )
