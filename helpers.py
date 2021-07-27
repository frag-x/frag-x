import game_engine_constants
import math
import pygame

def clamp(val, min_val, max_val):
    return min(max(val, min_val), max_val)

def get_sign(num):
    if num >= 0:
        return 1
    elif num < 0:
        return -1
    #else:
    #    return 0


def tuple_add(t0, t1):
    return (int(t0[0] + t1[0]), int(t0[1] + t1[1])) 

def point_within_map(point) -> bool:
    print(f"checking point {point} within x: {game_engine_constants.MAP_DIM_X}, and within y: {game_engine_constants.MAP_BASE_DIM_Y}")
    x_valid = 0 <= point[0] <= game_engine_constants.MAP_DIM_X 
    y_valid = 0 <= point[1] <= game_engine_constants.MAP_DIM_Y
    return x_valid and y_valid


def part_of_beam(point, beam):
    """Given a point on the line defined by the beams line segment,
    check if the point is part of the line segment"""
    x,y = point[0], point[1]
    if beam.slope == math.inf: # check if it's between y values then
        value = y
        lower_bound = min(0, beam.end_point.y - beam.start_point.y)
        upper_bound = max(0, beam.end_point.y - beam.start_point.y)
    else: # then we can use x values
        value = x
        lower_bound = min(0, beam.end_point.x - beam.start_point.x)
        upper_bound = max(0, beam.end_point.x - beam.start_point.x)
    #return min_x < x < max_x # excluding endpoints so that explosions can spawn at corners of squares
    return lower_bound < value < upper_bound

def copy_vector(v):
    return pygame.math.Vector2(v.x, v.y)

def valid_2d_index_for_partitioned_map_grid(idx, pmg):
    x, y = idx
    return 0 <= x <= pmg.num_x_partitions - 1 and 0 <= y <= pmg.num_y_partitions -1

def get_slope(point_1, point_2):
    delta_y = point_2[1] - point_1[1]
    delta_x = point_2[0] - point_1[0]

    return get_slope_from_deltas(delta_x, delta_y)


def get_slope_from_deltas(delta_x, delta_y):
    try:
        slope = delta_y/delta_x
    except ZeroDivisionError:
        slope = math.inf

    return slope

def translate_point_for_camera(player, point: pygame.math.Vector2):
    offset = game_engine_constants.SCREEN_CENTER_POINT - player.pos
    return point + offset

def get_partition_index(partitioned_map_grid, position):
    partition_idx_x = int(position[0] // partitioned_map_grid.partition_width)
    partition_idx_y = int(position[1] // partitioned_map_grid.partition_height)

    return (partition_idx_x, partition_idx_y)



#def get_quadrant_info(point_1, point_2):
#    """Considering point_1 as the origin, this function returns which quadrant point_2 is in"""

