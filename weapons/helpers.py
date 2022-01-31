import math

import pygame.math

import game_engine_constants


def polar_to_cartesian(radius: float, angle: float) -> tuple[float, float]:
    return math.cos(angle) * radius, math.sin(angle) * radius


def get_sign(num: float) -> int:
    return 1 if num >= 0 else -1


def point_within_map(point: tuple[float, float]) -> bool:
    x_valid = 0 <= point[0] <= game_engine_constants.MAP_DIM_X
    y_valid = 0 <= point[1] <= game_engine_constants.MAP_DIM_Y
    return x_valid and y_valid


def get_slope(point_1: pygame.math.Vector2, point_2: pygame.math.Vector2) -> float:
    delta_y = point_2[1] - point_1[1]
    delta_x = point_2[0] - point_1[0]

    return get_slope_from_deltas(delta_x, delta_y)


def get_slope_from_deltas(delta_x: float, delta_y: float) -> float:
    try:
        slope = delta_y / delta_x
    except ZeroDivisionError:
        slope = math.inf

    return slope
