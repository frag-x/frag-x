from typing import Tuple, Any

import game_engine_constants
import math
import pygame

import math

import pygame.math

import game_engine_constants


def polar_to_cartesian(radius: int, angle: float) -> Tuple[float, float]:
    return math.cos(angle) * radius, math.sin(angle) * radius


def get_sign(num: float) -> int:
    return 1 if num >= 0 else -1


def point_within_map(point: pygame.math.Vector2) -> bool:
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


def clamp(val: float, min_val: float, max_val: float) -> float:
    return min(max(val, min_val), max_val)


def tuple_add(t0: Tuple[int, int], t1: Tuple[int, int]) -> Tuple[int, int]:
    return (int(t0[0] + t1[0]), int(t0[1] + t1[1]))


# NOTE: beam can't be more strongly typed without an import cycle
def part_of_beam(point: Tuple[float, float], beam: Any) -> bool:
    """Given a point on the line defined by the beams line segment,
    check if the point is part of the line segment"""
    x, y = point[0], point[1]
    if beam.slope == math.inf:  # check if it's between y values then
        value = y
        lower_bound = min(0, beam.end_point.y - beam.start_point.y)
        upper_bound = max(0, beam.end_point.y - beam.start_point.y)
    else:  # then we can use x values
        value = x
        lower_bound = min(0, beam.end_point.x - beam.start_point.x)
        upper_bound = max(0, beam.end_point.x - beam.start_point.x)
    # return min_x < x < max_x # excluding endpoints so that explosions can spawn at corners of squares
    return lower_bound < value < upper_bound


def copy_vector(v: pygame.math.Vector2) -> pygame.math.Vector2:
    return pygame.math.Vector2(v.x, v.y)


# NOTE: pmg can't be typed more strictly than Any because it would lead to a dependency cycle
def valid_2d_index_for_partitioned_map_grid(idx: Tuple[int, int], pmg: Any) -> bool:
    x, y = idx
    return 0 <= x <= pmg.num_x_partitions - 1 and 0 <= y <= pmg.num_y_partitions - 1


# NOTE: player can't be typed more strictly without creating a dependency cycle
def translate_point_for_camera(
    player: Any, point: pygame.math.Vector2
) -> pygame.math.Vector2:
    offset = game_engine_constants.SCREEN_CENTER_POINT - player.position
    return point + offset


def get_partition_index(
    partition_width: int, partition_height: int, position: pygame.math.Vector2
) -> Tuple[int, int]:
    partition_idx_x = int(position[0] // partition_width)
    partition_idx_y = int(position[1] // partition_height)
    return partition_idx_x, partition_idx_y


def magnitude(v: pygame.math.Vector2) -> float:
    return math.sqrt(v.x**2 + v.y**2)
