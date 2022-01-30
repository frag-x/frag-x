import math

import pygame

import game_engine_constants
from weapons import constants, helpers
from weapons.weapon import HitscanWeapon, HitscanBeam
from typing import Any


class RailGun(HitscanWeapon):
    def __init__(self) -> None:
        super().__init__(
            fire_rate=constants.RAILGUN_FIRE_RATE_HZ, damage=constants.RAILGUN_DAMAGE
        )

    # NOTE: we can't type firing player more strictly without a dependency cycle
    def fire(self, firing_player: Any, aim_angle: float) -> None:
        """
        Return the fired HitscanBeam from the railgun
        :param firing_player: the player that shot this weapon
        :param aim_angle: the angle that the weapon is fired at
        :return: List[HitscanBeam]
        """
        delta_y = math.sin(aim_angle)
        delta_x = math.cos(aim_angle)

        # TODO y is flipped here
        quadrant_info = (helpers.get_sign(delta_x), helpers.get_sign(delta_y))

        """
        Given the player is at the point (p, q), 
        and slope (m) is not 0 or infinity, then we have:

        y - q = m (x - p) <=> y = mx + (-pm + q)  (A)

        OR

        y - q = m (x - p) <=> (y - q)/m = (x - p) <=> (y - q)/m + p = x (B)

        We'll use A when evaluating at an x position, and B when evaluating at a y position in the below functions
        """

        def get_y_from_point_slope_form(
            x: float,
        ) -> float:
            return slope * x + (
                -1 * firing_player.position.x * slope + firing_player.position.y
            )

        def get_x_from_point_slope_form(
            y: float,
        ) -> float:
            return (y - firing_player.position.y) / slope + firing_player.position.x

        slope = helpers.get_slope_from_deltas(delta_x, delta_y)

        if slope == 0 or slope == math.inf:

            """
            If m is zero, then the shot is horizontal, this means that when evaluating at an x position
            the y value associated with it is the y value of the shot location, it doesn't make sense to evaluate
            at a y position.

            If m is infinity, then the shot is vertical, this means that when evaluating at an y position
            the x value associated with it is the x value of the shot location, it doesn't make sense to evaluate
            at a x position.
            """
            # special case
            pass
        else:
            left_wall = 0
            right_wall = game_engine_constants.MAP_DIM_X
            top_wall = 0
            bottom_wall = game_engine_constants.MAP_DIM_Y

            quadrant_info_to_walls = {
                (-1, 1): [left_wall, bottom_wall],
                (1, -1): [right_wall, top_wall],
                (1, 1): [right_wall, bottom_wall],
                (-1, -1): [left_wall, top_wall],
            }

            wall_x, wall_y = quadrant_info_to_walls[quadrant_info]

            point_1 = pygame.math.Vector2(wall_x, get_y_from_point_slope_form(wall_x))
            point_2 = pygame.math.Vector2(get_x_from_point_slope_form(wall_y), wall_y)

            # it is guarenteed that one of these points is valid.
            for point in [point_1, point_2]:
                if helpers.point_within_map(point):
                    HitscanBeam(
                        firing_player,
                        firing_player.position,
                        point,
                        constants.RAILGUN_COLLISION_FORCE,
                        constants.RAILGUN_DAMAGE,
                    )
                    return

            assert False
