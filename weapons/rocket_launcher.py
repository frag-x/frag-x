import math

import pygame

from body import ConstantVelocityBody
from weapons import constants
from weapons.weapon import Projectile, RadialExplosives, Launcher


class Rocket(Projectile, ConstantVelocityBody):
    """
    A rocket is a type of projectile which moves with constant velocity, it's payload is an explosion
    """

    def __init__(
        self,
        *,
        start_pos: pygame.math.Vector2,
        radius: float,
        speed: int,
        direction: pygame.math.Vector2,
        explosives: RadialExplosives,
    ):
        """
        Initializes a rocket

        :param start_pos: where the rocket is spawned
        :param radius: how large the rocket is
        :param speed: the speed at which the rocket moves
        :param direction: a unit vector representing the direction the rocket will move
        :param explosives: the payload for thr rocket
        """
        super().__init__(explosives)
        super(Projectile).__init__(
            start_pos=start_pos,
            radius=radius,
            friction=0,
            velocity=direction * speed,
        )


class RocketLauncher(Launcher):
    """
    A rocket launcher is a weapon which shoots rockets
    """

    def fire(
        self, firing_position: pygame.math.Vector2, aim_angle: float
    ) -> Projectile:
        """
        Return a fired rocket
        :param firing_position: the position that the rocket launcher is fired
        :param aim_angle: the angle that the rocket should be shot at
        :return: the fired rocket
        """
        aim_vector = pygame.math.Vector2(0, 0)
        aim_angle_deg = aim_angle * 360 / math.tau
        aim_vector.from_polar((1, aim_angle_deg))  # unit vector
        return Rocket(
            start_pos=firing_position,
            radius=constants.ROCKET_RADIUS,
            speed=constants.ROCKET_SPEED,
            direction=aim_vector,
            explosives=RadialExplosives(),
        )
