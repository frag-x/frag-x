import math
import random
import logging

# logging.basicConfig(level=logging.INFO)
import helpers
import pygame
import typing, enum
import game_engine_constants, dev_constants, body


class WeaponTypes(enum.Enum):
    RAIL_GUN = 0
    ROCKET_LAUNCHER = 1


class Weapon:
    def __init__(self, fire_rate: float, owner, power):
        # Measured in shots per second
        self.fire_rate = fire_rate
        self.seconds_per_shot = 1 / self.fire_rate
        self.owner = owner
        self.power = power
        # Initialize to a value where they can shoot immediatly
        self.time_since_last_shot = self.seconds_per_shot

    # TODO make a method which takes in a checking function and runs it or something only if you've waited past the rate


class HitscanBeam:
    """A hitscan beam is a line segment"""

    # TODO make sure the inputs are actually vectors
    def __init__(self, start_point, end_point):
        self.delta_y = end_point[1] - start_point[1]
        self.delta_x = end_point[0] - start_point[0]

        self.direction_vector = (end_point - start_point).normalize()

        self.start_point = start_point
        self.end_point = end_point

        self.slope = helpers.get_slope(start_point, end_point)

        self.quadrant_info = (
            helpers.get_sign(self.delta_x),
            helpers.get_sign(self.delta_y),
        )

    def __str__(self):
        return str(vars(self))


# Todo rename this to rail gun
class Hitscan(Weapon):
    def __init__(self, fire_rate: float, owner, power: float):
        super().__init__(fire_rate, owner, power)

    def fire(self):
        # TODO -implement the logic found on the server here to simplify the server code
        pass

    def get_beam(self, screen_for_debug=None):

        delta_y = math.sin(self.owner.rotation_angle)

        delta_x = math.cos(self.owner.rotation_angle)

        quadrant_info = (helpers.get_sign(delta_x), helpers.get_sign(delta_y))

        slope = helpers.get_slope_from_deltas(delta_x, delta_y)

        left_wall = 0
        right_wall = game_engine_constants.MAP_DIM_X

        top_wall = 0
        bottom_wall = game_engine_constants.MAP_DIM_Y

        left_wall_translated, right_wall_translated = (
            left_wall - self.owner.pos.x,
            right_wall - self.owner.pos.x,
        )
        top_wall_translated, bottom_wall_translated = (
            top_wall - self.owner.pos.y,
            bottom_wall - self.owner.pos.y,
        )

        # assuming the slope isn't vertical or horizontal here

        translated_locations = []
        if quadrant_info == (-1, -1):
            # Check left and top
            # print("checking left and top")
            left_wall_y_translated = slope * left_wall_translated
            top_wall_x_translated = 1 / slope * top_wall_translated
            translated_locations = [
                (left_wall_translated, left_wall_y_translated),
                (top_wall_x_translated, top_wall_translated),
            ]
        elif quadrant_info == (1, -1):
            # check right and top
            # print("checking right and top")
            right_wall_y_translated = slope * right_wall_translated
            top_wall_x_translated = 1 / slope * top_wall_translated
            translated_locations = [
                (right_wall_translated, right_wall_y_translated),
                (top_wall_x_translated, top_wall_translated),
            ]
        elif quadrant_info == (1, 1):
            # check right and bottom
            # print("checking right and bottom")
            right_wall_y_translated = slope * right_wall_translated
            bottom_wall_x_translated = 1 / slope * bottom_wall_translated
            translated_locations = [
                (right_wall_translated, right_wall_y_translated),
                (bottom_wall_x_translated, bottom_wall_translated),
            ]
        elif quadrant_info == (-1, 1):
            # check left and bottom
            # print("checking left and bottom")
            left_wall_y_translated = slope * left_wall_translated
            bottom_wall_x_translated = 1 / slope * bottom_wall_translated
            translated_locations = [
                (left_wall_translated, left_wall_y_translated),
                (bottom_wall_x_translated, bottom_wall_translated),
            ]

        locations = [
            pygame.math.Vector2(x + self.owner.pos.x, y + self.owner.pos.y)
            for x, y in translated_locations
        ]

        # print(locations)

        for location in locations:
            # This is the whole reason this whole function is locked - if this function is not locked then the players position could be updated between tranlsations making the whole thing break
            if helpers.point_within_map(location):
                if screen_for_debug:
                    pygame.draw.line(
                        screen_for_debug,
                        pygame.color.THECOLORS["purple"],
                        helpers.translate_point_for_camera(self.owner, self.owner.pos),
                        helpers.translate_point_for_camera(self.owner, location),
                    )
                # This is guarenteed to be reached
                return HitscanBeam(helpers.copy_vector(self.owner.pos), location)
        # assert 1 == 0

    def get_firing_line(self):
        fire_origin = self.owner.pos

        delta_y = math.sin(self.owner.rotation_angle)

        delta_x = math.cos(self.owner.rotation_angle)

        closest_hit = None
        closest_entity = None

        quadrant_info = (helpers.get_sign(delta_x), helpers.get_sign(delta_y))

        if delta_x == 0 or delta_y == 0:
            # Then we fired along the axis
            pass
        else:
            fire_slope = delta_y / delta_x

    def get_intersecting_partitions(
        self, partitioned_map_grid, beam: HitscanBeam, screen_for_debug=None
    ):

        intersecting_partitions = set()

        x_beam_interval = [
            min(beam.start_point.x, beam.end_point.x),
            max(beam.start_point.x, beam.end_point.x),
        ]
        y_beam_interval = [
            min(beam.start_point.y, beam.end_point.y),
            max(beam.start_point.y, beam.end_point.y),
        ]

        """
        A Quad patch is the overlap of 4 collision partitions
         ___________ ___________
        |           |           |
        |           |   QP      |
        |           |  /        |
        |        ___|_/_        |
        |       |   |   |       |
        |_______|___|___|_______|
        |       |   |   |       |
        |       |___|___|       |
        |           |           |
        |           |           |
        |           |           |
        |___________|___________|

        """

        if beam.slope != math.inf and beam.slope != 0:
            valid_x_partition_seams = [
                x
                for x in range(
                    0, partitioned_map_grid.width, partitioned_map_grid.partition_width
                )
                if x_beam_interval[0] <= x <= x_beam_interval[1]
            ]
            valid_y_partition_seams = [
                y
                for y in range(
                    0,
                    partitioned_map_grid.height,
                    partitioned_map_grid.partition_height,
                )
                if y_beam_interval[0] <= y <= y_beam_interval[1]
            ]

            valid_x_partition_seams_translated = [
                x - self.owner.pos.x for x in valid_x_partition_seams
            ]
            valid_y_partition_seams_translated = [
                y - self.owner.pos.y for y in valid_y_partition_seams
            ]

            # TODO the usage of bottom here is incorrect, it should be top
            # vxpst: valid x partition seam translated
            for vxpst in valid_x_partition_seams_translated:
                # TODO check if this is within
                y = beam.slope * vxpst
                # TODO remove hardcode on tilesize?
                untranslated_y = y + self.owner.pos.y
                untranslated_x = vxpst + self.owner.pos.x

                point = (untranslated_x, untranslated_y)

                if screen_for_debug:
                    pygame.draw.circle(
                        screen_for_debug,
                        pygame.color.THECOLORS["purple"],
                        helpers.translate_point_for_camera(self.owner, point),
                        game_engine_constants.DEBUG_RADIUS,
                    )

                intersecting_bottom_of_quad_patch = (
                    partitioned_map_grid.partition_height
                    - game_engine_constants.TILE_SIZE
                    <= untranslated_y % partitioned_map_grid.partition_height
                    <= partitioned_map_grid.partition_height
                )
                intersecting_top_of_quad_patch = (
                    0
                    <= untranslated_y % partitioned_map_grid.partition_height
                    <= game_engine_constants.TILE_SIZE
                )

                if intersecting_bottom_of_quad_patch or intersecting_top_of_quad_patch:
                    # print("At a quad_patch intersection")
                    if intersecting_bottom_of_quad_patch:
                        # Then we round up
                        quad_patch_center = (
                            untranslated_x,
                            (
                                untranslated_y // partitioned_map_grid.partition_height
                                + 1
                            )
                            * partitioned_map_grid.partition_height,
                        )
                    elif intersecting_top_of_quad_patch:
                        # Then we round down
                        quad_patch_center = (
                            untranslated_x,
                            (untranslated_y // partitioned_map_grid.partition_height)
                            * partitioned_map_grid.partition_height,
                        )

                    if screen_for_debug:
                        pygame.draw.circle(
                            screen_for_debug,
                            pygame.color.THECOLORS["red"],
                            helpers.translate_point_for_camera(
                                self.owner, pygame.math.Vector2(quad_patch_center)
                            ),
                            game_engine_constants.DEBUG_RADIUS,
                        )

                    bottom_right_partition_idx_x = (
                        quad_patch_center[0] // partitioned_map_grid.partition_width
                    )
                    bottom_right_partition_idx_y = (
                        quad_patch_center[1] // partitioned_map_grid.partition_height
                    )

                    bottom_right_partition_idx = (
                        bottom_right_partition_idx_x,
                        bottom_right_partition_idx_y,
                    )

                    collision_partition_offsets = [(-1, -1), (0, -1), (0, 0), (-1, 0)]

                    collision_partition_indices = []
                    for t0 in collision_partition_offsets:
                        new_idx = helpers.tuple_add(t0, bottom_right_partition_idx)
                        if helpers.valid_2d_index_for_partitioned_map_grid(
                            new_idx, partitioned_map_grid
                        ):
                            collision_partition_indices.append(new_idx)

                    # Uses a set for duplicate collision partitions

                    for index in collision_partition_indices:
                        x, y = index
                        # print(f"About to Index: {(x,y)} out of {partitioned_map_grid.num_x_partitions, partitioned_map_grid.num_y_partitions}")
                        intersecting_partitions.add(
                            partitioned_map_grid.partitioned_map[y][x]
                        )

                else:
                    # Then we're at a double intersection
                    # print("double intersection")

                    double_patch_upper = (
                        untranslated_x,
                        (untranslated_y // partitioned_map_grid.partition_height)
                        * partitioned_map_grid.partition_height,
                    )

                    if screen_for_debug:
                        pygame.draw.circle(
                            screen_for_debug,
                            pygame.color.THECOLORS["red"],
                            helpers.translate_point_for_camera(
                                self.owner,
                                pygame.math.Vector2(
                                    double_patch_upper[0],
                                    double_patch_upper[1]
                                    + partitioned_map_grid.partition_height / 2,
                                ),
                            ),
                            game_engine_constants.DEBUG_RADIUS,
                        )

                    double_patch_upper_partition_idx_x = (
                        double_patch_upper[0] // partitioned_map_grid.partition_width
                    )
                    double_patch_upper_partition_idx_y = (
                        double_patch_upper[1] // partitioned_map_grid.partition_height
                    )

                    double_patch_upper_partition_idx = (
                        double_patch_upper_partition_idx_x,
                        double_patch_upper_partition_idx_y,
                    )

                    collision_partition_offsets = [(0, 0), (-1, 0)]

                    collision_partition_indices = []
                    for t0 in collision_partition_offsets:
                        new_idx = helpers.tuple_add(
                            t0, double_patch_upper_partition_idx
                        )
                        if helpers.valid_2d_index_for_partitioned_map_grid(
                            new_idx, partitioned_map_grid
                        ):
                            collision_partition_indices.append(new_idx)

                    # Uses a set for duplicate collision partitions

                    for index in collision_partition_indices:
                        x, y = index
                        # print(f"About to Index: {(x,y)} out of {partitioned_map_grid.num_x_partitions, partitioned_map_grid.num_y_partitions}")
                        intersecting_partitions.add(
                            partitioned_map_grid.partitioned_map[y][x]
                        )

            ## vypst: valid y partition seam translated
            for vypst in valid_y_partition_seams_translated:
                x = 1 / beam.slope * vypst
                untranslated_x = x + self.owner.pos.x
                untranslated_y = vypst + self.owner.pos.y

                point = (untranslated_x, untranslated_y)

                if screen_for_debug:
                    pygame.draw.circle(
                        screen_for_debug,
                        pygame.color.THECOLORS["purple"],
                        helpers.translate_point_for_camera(self.owner, point),
                        game_engine_constants.DEBUG_RADIUS,
                    )

                intersecting_left_of_quad_patch = (
                    partitioned_map_grid.partition_width
                    - game_engine_constants.TILE_SIZE
                    <= untranslated_x % partitioned_map_grid.partition_width
                    <= partitioned_map_grid.partition_width
                )
                intersecting_right_of_quad_patch = (
                    0
                    <= untranslated_x % partitioned_map_grid.partition_width
                    <= game_engine_constants.TILE_SIZE
                )

                if intersecting_right_of_quad_patch or intersecting_left_of_quad_patch:
                    # print("At a quad_patch intersection")
                    if intersecting_left_of_quad_patch:
                        # Then we round up
                        quad_patch_center = (
                            (untranslated_x // partitioned_map_grid.partition_width + 1)
                            * partitioned_map_grid.partition_width,
                            untranslated_y,
                        )
                        # quad_patch_center = (x_partition_seam, (untranslated_y // partitioned_map_grid.partition_height + 1) * partitioned_map_grid.partition_height)
                    elif intersecting_right_of_quad_patch:
                        # Then we round down
                        quad_patch_center = (
                            (untranslated_x // partitioned_map_grid.partition_width)
                            * partitioned_map_grid.partition_width,
                            untranslated_y,
                        )

                    if screen_for_debug:
                        pygame.draw.circle(
                            screen_for_debug,
                            pygame.color.THECOLORS["red"],
                            helpers.translate_point_for_camera(
                                self.owner, pygame.math.Vector2(quad_patch_center)
                            ),
                            game_engine_constants.DEBUG_RADIUS,
                        )

                    bottom_right_partition_idx_x = (
                        quad_patch_center[0] // partitioned_map_grid.partition_width
                    )
                    bottom_right_partition_idx_y = (
                        quad_patch_center[1] // partitioned_map_grid.partition_height
                    )

                    bottom_right_partition_idx = (
                        bottom_right_partition_idx_x,
                        bottom_right_partition_idx_y,
                    )

                    collision_partition_offsets = [(-1, -1), (0, -1), (0, 0), (-1, 0)]

                    collision_partition_indices = []
                    for t0 in collision_partition_offsets:
                        new_idx = helpers.tuple_add(t0, bottom_right_partition_idx)
                        if helpers.valid_2d_index_for_partitioned_map_grid(
                            new_idx, partitioned_map_grid
                        ):
                            collision_partition_indices.append(new_idx)

                    # Uses a set for duplicate collision partitions

                    for index in collision_partition_indices:
                        x, y = index
                        # print(f"About to Index: {(x,y)} out of {partitioned_map_grid.num_x_partitions, partitioned_map_grid.num_y_partitions}")
                        intersecting_partitions.add(
                            partitioned_map_grid.partitioned_map[y][x]
                        )

                else:
                    # Then we're at a double intersection
                    # print("double intersection")

                    double_patch_left = (
                        (untranslated_x // partitioned_map_grid.partition_width)
                        * partitioned_map_grid.partition_height,
                        untranslated_y,
                    )

                    if screen_for_debug:
                        pygame.draw.circle(
                            screen_for_debug,
                            pygame.color.THECOLORS["red"],
                            helpers.translate_point_for_camera(
                                self.owner,
                                pygame.math.Vector2(
                                    double_patch_left[0]
                                    + partitioned_map_grid.partition_width / 2,
                                    double_patch_left[1],
                                ),
                            ),
                            game_engine_constants.DEBUG_RADIUS,
                        )

                    double_patch_left_partition_idx_x = (
                        double_patch_left[0] // partitioned_map_grid.partition_width
                    )
                    double_patch_left_partition_idx_y = (
                        double_patch_left[1] // partitioned_map_grid.partition_height
                    )

                    double_patch_left_partition_idx = (
                        double_patch_left_partition_idx_x,
                        double_patch_left_partition_idx_y,
                    )

                    collision_partition_offsets = [(0, 0), (0, -1)]

                    collision_partition_indices = []
                    for t0 in collision_partition_offsets:
                        new_idx = helpers.tuple_add(t0, double_patch_left_partition_idx)
                        if helpers.valid_2d_index_for_partitioned_map_grid(
                            new_idx, partitioned_map_grid
                        ):
                            collision_partition_indices.append(new_idx)

                    # Uses a set for duplicate collision partitions

                    for index in collision_partition_indices:
                        x, y = index
                        # print(f"About to Index: {(x,y)} out of {partitioned_map_grid.num_x_partitions, partitioned_map_grid.num_y_partitions}")
                        # intersecting_partitions.add(partitioned_map_grid.collision_partitioned_map[y][x])
                        intersecting_partitions.add(
                            partitioned_map_grid.partitioned_map[y][x]
                        )
            return intersecting_partitions
        else:
            # Vertical/Horizontal shot made
            pass

    def get_closest_intersecting_object_in_pmg(
        self, partitioned_map_grid, beam, screen_for_debug=None
    ):
        closest_hit = None
        closest_entity = None

        def update_closest(hit, entity, closest_hit, closest_entity):

            if closest_hit is None:
                closest_hit = hit
                closest_entity = entity
            else:
                if hit.magnitude() <= closest_hit.magnitude():
                    closest_hit = hit
                    closest_entity = entity
            return closest_hit, closest_entity

        intersected_partitions = self.get_intersecting_partitions(
            partitioned_map_grid, beam, screen_for_debug
        )

        for partition in intersected_partitions:
            hit, entity = self.get_closest_intersecting_object_in_partition(
                partition, screen_for_debug
            )

            if screen_for_debug and hit is not None:
                translated_hit = helpers.translate_point_for_camera(
                    self.owner, hit + self.owner.pos
                )
                pygame.draw.circle(
                    screen_for_debug,
                    pygame.color.THECOLORS["aquamarine"],
                    translated_hit,
                    game_engine_constants.DEBUG_RADIUS,
                )

            if hit is not None and entity is not None:
                closest_hit, closest_entity = update_closest(
                    hit, entity, closest_hit, closest_entity
                )
        # Reposition relative to the player
        closest_hit = closest_hit + self.owner.pos

        # Note that there will always be a closest element as the map is closed.
        if dev_constants.CLIENT_VISUAL_DEBUGGING:
            pygame.draw.circle(
                dev_constants.SCREEN_FOR_DEBUGGING,
                pygame.color.THECOLORS["gold"],
                helpers.translate_point_for_camera(self.owner, closest_hit),
                game_engine_constants.DEBUG_RADIUS,
            )

        print(f"Closest Hit {closest_entity} at {closest_hit}")
        return closest_hit, closest_entity

    def get_closest_intersecting_object_in_partition(self, pmg, screen_for_debug=None):

        fire_origin = self.owner.pos

        delta_y = math.sin(self.owner.rotation_angle)

        delta_x = math.cos(self.owner.rotation_angle)

        closest_hit = None
        closest_entity = None

        quadrant_info = (helpers.get_sign(delta_x), helpers.get_sign(delta_y))

        def update_closest(hit, entity, closest_hit, closest_entity):

            if closest_hit is None:
                closest_hit = hit
                closest_entity = entity
            else:
                if hit.magnitude() <= closest_hit.magnitude():
                    closest_hit = hit
                    closest_entity = entity
            return closest_hit, closest_entity

        if delta_x == 0 or delta_y == 0:
            # Then we fired along the axis
            pass
        else:
            fire_slope = delta_y / delta_x

            for b_wall in pmg.bounding_walls:

                if screen_for_debug is not None:
                    pygame.draw.rect(
                        screen_for_debug,
                        pygame.color.THECOLORS["purple"],
                        b_wall.rect.move(self.owner.camera_v),
                        width=1,
                    )
                top, left, bottom, right = (
                    b_wall.rect.top,
                    b_wall.rect.left,
                    b_wall.rect.bottom,
                    b_wall.rect.right,
                )
                ##print( top, left, bottom, right)
                translated_top, translated_left, translated_bottom, translated_right = (
                    top - fire_origin.y,
                    left - fire_origin.x,
                    bottom - fire_origin.y,
                    right - fire_origin.x,
                )
                ##print("translated_top", "translated_left", "translated_bottom", "translated_right" )
                ##print(translated_top, translated_left, translated_bottom, translated_right )

                # y = fire_slope x <=> y/fire_slope = x (assuming fire_slope is non-zero)

                yr = fire_slope * translated_right
                yl = fire_slope * translated_left

                if translated_top <= yr <= translated_bottom:
                    # Hit right side
                    # print(f"hit right at ({translated_right}, {yr})")
                    hit = pygame.math.Vector2((translated_right, yr))
                    if (
                        helpers.get_sign(hit.x),
                        helpers.get_sign(hit.y),
                    ) == quadrant_info:
                        closest_hit, closest_entity = update_closest(
                            hit, b_wall, closest_hit, closest_entity
                        )

                if translated_top <= yl <= translated_bottom:
                    # Hit right side
                    # print(f"hit left at ({translated_left}, {yl})")
                    hit = pygame.math.Vector2((translated_left, yl))
                    if (
                        helpers.get_sign(hit.x),
                        helpers.get_sign(hit.y),
                    ) == quadrant_info:
                        closest_hit, closest_entity = update_closest(
                            hit, b_wall, closest_hit, closest_entity
                        )

                xt = translated_top / fire_slope
                xb = translated_bottom / fire_slope

                if translated_left <= xt <= translated_right:
                    # print(f"hit top at ({xt}, {translated_top})")
                    hit = pygame.math.Vector2((xt, translated_top))
                    if (
                        helpers.get_sign(hit.x),
                        helpers.get_sign(hit.y),
                    ) == quadrant_info:
                        closest_hit, closest_entity = update_closest(
                            hit, b_wall, closest_hit, closest_entity
                        )

                if translated_left <= xb <= translated_right:
                    # print(f"hit bottom at ({xb}, {translated_bottom})")
                    hit = pygame.math.Vector2((xb, translated_bottom))
                    if (
                        helpers.get_sign(hit.x),
                        helpers.get_sign(hit.y),
                    ) == quadrant_info:
                        closest_hit, closest_entity = update_closest(
                            hit, b_wall, closest_hit, closest_entity
                        )

                # if len(hits) != 0:

            for body in pmg.players:

                if body is not self.owner:

                    """
                    Assuming p, q are written with respect to the fire origin:

                    (x - p)**2 + (y - q)**2 = r**2 & y = mx

                    =>  (x - p)**2 + (mx - q)**2 = r**2

                    <=> x**2 - 2px + p**2 + (mx)**2 - 2mqx + q**2 = r**2

                    <=> (m**2 + 1)x**2 -2(p + mq)x + p**2 + q**2 - r**2 = 0

                    Quadratic Equation with

                    a = (m**2 + 1), b = -2(p + q) c = p**2 + q**2 - r**2

                    Then it will have solutions if the descriminant is positive, that is, if:

                    b**2 - 4ac >= 0

                    """
                    p, q = body.pos
                    r = body.radius

                    # Written with respect to fire origin
                    p, q = p - fire_origin.x, q - fire_origin.y

                    m = fire_slope

                    if m == math.inf:
                        pass

                    a = (m ** 2) + 1
                    b = -2 * (p + (m * q))
                    c = (p ** 2) + (q ** 2) - (r ** 2)

                    discriminant = b ** 2 - (4 * a * c)

                    if discriminant >= 0:
                        # print("hit ball")
                        # Then we have at least one solution
                        x = (-b + (discriminant) ** (1 / 2)) / (2 * a)
                        y = m * x
                        hit = pygame.math.Vector2((x, y))
                        if (
                            helpers.get_sign(hit.x),
                            helpers.get_sign(hit.y),
                        ) == quadrant_info:
                            closest_hit, closest_entity = update_closest(
                                hit, body, closest_hit, closest_entity
                            )
                        if discriminant > 0:
                            # Second solution is negative
                            xn = (-b - (discriminant) ** (1 / 2)) / (2 * a)
                            yn = m * xn
                            hit = pygame.math.Vector2((xn, yn))
                            if (
                                helpers.get_sign(hit.x),
                                helpers.get_sign(hit.y),
                            ) == quadrant_info:
                                closest_hit, closest_entity = update_closest(
                                    hit, body, closest_hit, closest_entity
                                )

            if closest_hit is not None:
                # returns position relative to player which is good
                return closest_hit, closest_entity
            else:
                return closest_hit, closest_entity


class Projectile(body.ConstantVelocityBody):
    pass


class RocketLauncher(Weapon):
    def __init__(
        self,
        fire_rate: float,
        owner,
        power,
        speed=2000,
        rocket_radius=game_engine_constants.TILE_SIZE / 4,
    ):
        super().__init__(fire_rate, owner, power)
        self.speed = speed
        self.rocket_radius = rocket_radius
        # TODO rocket launcher should not be in charge of it's own bullets, need a weapon management system
        self.fired_projectiles = []

    def fire_projectile(self):
        velocity_v = pygame.math.Vector2(0, 0)
        # Because from polar is in deg apparently ...
        # TODO add a polar version to pygame
        deg = self.owner.rotation_angle * 360 / math.tau
        velocity_v.from_polar((self.speed, deg))

        rocket = Projectile(self.owner.pos, self.rocket_radius, 0, velocity_v)
        self.fired_projectiles.append(rocket)

    def update_projectile_positions(self, delta_time):
        for rocket in self.fired_projectiles:
            # Everything is measured per second
            rocket.previous_pos = pygame.math.Vector2(rocket.pos.x, rocket.pos.y)
            rocket.pos += rocket.velocity * delta_time


class Explosion:
    def __init__(self, pos, radius=100, power=750, num_shards=32):
        self.pos = pos
        self.radius = radius
        self.power = power
        self.num_shards = num_shards
        self.beams = []
        self.generate_beams()

    def generate_beams(self):
        angle_fraction = math.tau / self.num_shards
        for i in range(self.num_shards):
            angle = angle_fraction * i
            x = math.cos(angle) * self.radius
            y = math.sin(angle) * self.radius

            relative_shard_vec = pygame.math.Vector2(x, y)

            shard_vec = relative_shard_vec + self.pos

            self.beams.append(HitscanBeam(self.pos, shard_vec))
