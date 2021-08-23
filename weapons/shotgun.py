import math

import pygame

from helpers import polar_to_cartesian
from weapons import constants, helpers
from weapons.weapon import HitscanWeapon, HitscanBeam


class ShotGun(HitscanWeapon):
    def __init__(self):
        super().__init__(
            fire_rate=constants.SHOTGUN_FIRE_RATE_HZ, damage=constants.RAILGUN_DAMAGE
        )

    def fire(self, firing_player, aim_angle: float):
        """
        Return the fired HitscanBeam from the railgun
        :param firing_player: the player that shot this weapon
        :param aim_angle: the angle that the weapon is fired at
        """

        angle_fraction = constants.SHOTGUN_SPRAY_ANGLE / (constants.SHOTGUN_PELLETS - 1)

        start_angle = aim_angle - constants.SHOTGUN_SPRAY_ANGLE / 2

        for i in range(constants.SHOTGUN_PELLETS):
            angle = start_angle + (angle_fraction * i)
            x, y = polar_to_cartesian(constants.SHOTGUN_SPRAY_RADIUS, angle)
            pellet_end_point = pygame.math.Vector2(x, y) + firing_player.position
            HitscanBeam(
                firing_player,
                firing_player.position,
                pellet_end_point,
                constants.SHOTGUN_COLLISION_FORCE,
                constants.SHOTGUN_PELLET_DAMAGE,
            )
