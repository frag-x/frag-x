import weapons, game_engine_constants, helpers, dev_constants
import pygame, math

# TODO REMOVE DEPENDENCY ON THE WEAPON

def get_intersecting_partitions(weapon, partitioned_map_grid, beam: weapons.HitscanBeam, screen_for_debug=None):
    
    fired_idx_x, fired_idx_y = helpers.get_partition_index(partitioned_map_grid, beam.start_point)

    partition_fired_from = partitioned_map_grid.partitioned_map[fired_idx_y][fired_idx_x]

    intersecting_partitions = {partition_fired_from}

    x_beam_interval = [min(beam.start_point.x, beam.end_point.x), max(beam.start_point.x, beam.end_point.x)]
    y_beam_interval = [min(beam.start_point.y, beam.end_point.y), max(beam.start_point.y, beam.end_point.y)]

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
    
    valid_x_partition_seams = [x for x in range(0, partitioned_map_grid.width, partitioned_map_grid.partition_width) if x_beam_interval[0] <= x <= x_beam_interval[1]]
    valid_y_partition_seams = [y for y in range(0, partitioned_map_grid.height, partitioned_map_grid.partition_height) if y_beam_interval[0] <= y <= y_beam_interval[1]]

    valid_x_partition_seams_translated = [x - beam.start_point.x for x in valid_x_partition_seams]
    valid_y_partition_seams_translated = [y - beam.start_point.y for y in valid_y_partition_seams]

    if beam.slope != math.inf:
        # TODO the usage of bottom here is incorrect, it should be top
        # vxpst: valid x partition seam translated 
        for vxpst in valid_x_partition_seams_translated:
            # TODO check if this is within 
            if beam.slope == 0:
                print("zero slope")
                y = 0 # because it's relative to the beams start point
            else:
                y = beam.slope * vxpst
            # TODO remove hardcode on tilesize?
            untranslated_y = y + beam.start_point.y
            untranslated_x = vxpst + beam.start_point.x

            point = pygame.math.Vector2(untranslated_x, untranslated_y)

            if dev_constants.DEBUGGING_INTERSECTIONS:
                dev_constants.INTERSECTED_PARTITION_SEAMS_FOR_DEBUGGING.append(point)

            intersecting_bottom_of_quad_patch = (partitioned_map_grid.partition_height - game_engine_constants.TILE_SIZE <= untranslated_y % partitioned_map_grid.partition_height <= partitioned_map_grid.partition_height)
            intersecting_top_of_quad_patch = (0 <= untranslated_y % partitioned_map_grid.partition_height  <= game_engine_constants.TILE_SIZE)

            if intersecting_bottom_of_quad_patch or intersecting_top_of_quad_patch:
                #print("At a quad_patch intersection")
                if intersecting_bottom_of_quad_patch:
                    # Then we round up
                    quad_patch_center = (untranslated_x, (untranslated_y // partitioned_map_grid.partition_height + 1) * partitioned_map_grid.partition_height)
                elif intersecting_top_of_quad_patch:
                    # Then we round down
                    quad_patch_center = (untranslated_x, (untranslated_y // partitioned_map_grid.partition_height ) * partitioned_map_grid.partition_height)


                if dev_constants.DEBUGGING_INTERSECTIONS:
                    dev_constants.INTERSECTED_PARTITION_PATCH_MARKERS.append(quad_patch_center)
                    #pygame.draw.circle(screen_for_debug, pygame.color.THECOLORS['red'], helpers.translate_point_for_camera(weapon.owner, pygame.math.Vector2(quad_patch_center)), game_engine_constants.DEBUG_RADIUS)

                bottom_right_partition_idx_x = quad_patch_center[0] // partitioned_map_grid.partition_width
                bottom_right_partition_idx_y = quad_patch_center[1] // partitioned_map_grid.partition_height

                bottom_right_partition_idx = (bottom_right_partition_idx_x, bottom_right_partition_idx_y)

                collision_partition_offsets = [(-1, -1), (0, -1), (0, 0), (-1, 0)]


                collision_partition_indices  = []
                for t0 in collision_partition_offsets:
                    new_idx = helpers.tuple_add(t0, bottom_right_partition_idx)
                    if helpers.valid_2d_index_for_partitioned_map_grid(new_idx, partitioned_map_grid):
                        collision_partition_indices.append(new_idx)

                # Uses a set for duplicate collision partitions

                for index in collision_partition_indices:
                    x, y = index
                    #print(f"About to Index: {(x,y)} out of {partitioned_map_grid.num_x_partitions, partitioned_map_grid.num_y_partitions}")
                    intersecting_partitions.add(partitioned_map_grid.partitioned_map[y][x])

            else:
                # Then we're at a double intersection
                #print("double intersection")

                double_patch_upper = (untranslated_x, (untranslated_y // partitioned_map_grid.partition_height ) * partitioned_map_grid.partition_height)

                if dev_constants.DEBUGGING_INTERSECTIONS:
                    dev_constants.INTERSECTED_PARTITION_PATCH_MARKERS.append(pygame.math.Vector2(double_patch_upper[0], double_patch_upper[1] + partitioned_map_grid.partition_height/2))
                    #pygame.draw.circle(screen_for_debug, pygame.color.THECOLORS['red'], helpers.translate_point_for_camera(weapon.owner, pygame.math.Vector2(double_patch_upper[0], double_patch_upper[1] + partitioned_map_grid.partition_height/2)), game_engine_constants.DEBUG_RADIUS)

                double_patch_upper_partition_idx_x = double_patch_upper[0] // partitioned_map_grid.partition_width
                double_patch_upper_partition_idx_y = double_patch_upper[1] // partitioned_map_grid.partition_height

                double_patch_upper_partition_idx = (double_patch_upper_partition_idx_x, double_patch_upper_partition_idx_y)

                collision_partition_offsets = [(0, 0), (-1, 0)]


                collision_partition_indices  = []
                for t0 in collision_partition_offsets:
                    new_idx = helpers.tuple_add(t0, double_patch_upper_partition_idx)
                    if helpers.valid_2d_index_for_partitioned_map_grid(new_idx, partitioned_map_grid):
                        collision_partition_indices.append(new_idx)

                # Uses a set for duplicate collision partitions

                for index in collision_partition_indices:
                    x, y = index
                    #print(f"About to Index: {(x,y)} out of {partitioned_map_grid.num_x_partitions, partitioned_map_grid.num_y_partitions}")
                    intersecting_partitions.add(partitioned_map_grid.partitioned_map[y][x])

    ## vypst: valid y partition seam translated 
    if beam.slope != 0:
        for vypst in valid_y_partition_seams_translated:
            if beam.slope == math.inf:
                x = 0
            else:
                x = 1/beam.slope * vypst
            untranslated_x = x + beam.start_point.x
            untranslated_y = vypst + beam.start_point.y

            point = pygame.math.Vector2(untranslated_x, untranslated_y)

            if dev_constants.DEBUGGING_INTERSECTIONS:
                dev_constants.INTERSECTED_PARTITION_SEAMS_FOR_DEBUGGING.append(point)
                #pygame.draw.circle(screen_for_debug, pygame.color.THECOLORS['purple'], helpers.translate_point_for_camera(weapon.owner, point), game_engine_constants.DEBUG_RADIUS)

            intersecting_left_of_quad_patch = (partitioned_map_grid.partition_width - game_engine_constants.TILE_SIZE <= untranslated_x % partitioned_map_grid.partition_width <= partitioned_map_grid.partition_width)
            intersecting_right_of_quad_patch = (0 <= untranslated_x % partitioned_map_grid.partition_width  <= game_engine_constants.TILE_SIZE)

            if intersecting_right_of_quad_patch or intersecting_left_of_quad_patch:
                #print("At a quad_patch intersection")
                if intersecting_left_of_quad_patch:
                    # Then we round up
                    quad_patch_center = ((untranslated_x // partitioned_map_grid.partition_width + 1) * partitioned_map_grid.partition_width, untranslated_y)
                    #quad_patch_center = (x_partition_seam, (untranslated_y // partitioned_map_grid.partition_height + 1) * partitioned_map_grid.partition_height)
                elif intersecting_right_of_quad_patch:
                    # Then we round down
                    quad_patch_center = ((untranslated_x // partitioned_map_grid.partition_width) * partitioned_map_grid.partition_width, untranslated_y)


                if dev_constants.DEBUGGING_INTERSECTIONS:
                    dev_constants.INTERSECTED_PARTITION_PATCH_MARKERS.append(quad_patch_center)
                    #pygame.draw.circle(screen_for_debug, pygame.color.THECOLORS['red'], helpers.translate_point_for_camera(weapon.owner, pygame.math.Vector2(quad_patch_center)), game_engine_constants.DEBUG_RADIUS)

                bottom_right_partition_idx_x = quad_patch_center[0] // partitioned_map_grid.partition_width
                bottom_right_partition_idx_y = quad_patch_center[1] // partitioned_map_grid.partition_height

                bottom_right_partition_idx = (bottom_right_partition_idx_x, bottom_right_partition_idx_y)

                collision_partition_offsets = [(-1, -1), (0, -1), (0, 0), (-1, 0)]


                collision_partition_indices  = []
                for t0 in collision_partition_offsets:
                    new_idx = helpers.tuple_add(t0, bottom_right_partition_idx)
                    if helpers.valid_2d_index_for_partitioned_map_grid(new_idx, partitioned_map_grid):
                        collision_partition_indices.append(new_idx)

                # Uses a set for duplicate collision partitions

                for index in collision_partition_indices:
                    x, y = index
                    #print(f"About to Index: {(x,y)} out of {partitioned_map_grid.num_x_partitions, partitioned_map_grid.num_y_partitions}")
                    intersecting_partitions.add(partitioned_map_grid.partitioned_map[y][x])

            else:
                # Then we're at a double intersection
                #print("double intersection")

                double_patch_left = ((untranslated_x // partitioned_map_grid.partition_width) * partitioned_map_grid.partition_height, untranslated_y)

                if screen_for_debug:
                    pygame.draw.circle(screen_for_debug, pygame.color.THECOLORS['red'], helpers.translate_point_for_camera(weapon.owner, pygame.math.Vector2(double_patch_left[0] + partitioned_map_grid.partition_width/2, double_patch_left[1])), game_engine_constants.DEBUG_RADIUS)

                double_patch_left_partition_idx_x = double_patch_left[0] // partitioned_map_grid.partition_width
                double_patch_left_partition_idx_y = double_patch_left[1] // partitioned_map_grid.partition_height

                double_patch_left_partition_idx = (double_patch_left_partition_idx_x, double_patch_left_partition_idx_y)

                collision_partition_offsets = [(0, 0), (0, -1)]


                collision_partition_indices  = []
                for t0 in collision_partition_offsets:
                    new_idx = helpers.tuple_add(t0, double_patch_left_partition_idx)
                    if helpers.valid_2d_index_for_partitioned_map_grid(new_idx, partitioned_map_grid):
                        collision_partition_indices.append(new_idx)

                # Uses a set for duplicate collision partitions

                for index in collision_partition_indices:
                    x, y = index
                    #print(f"About to Index: {(x,y)} out of {partitioned_map_grid.num_x_partitions, partitioned_map_grid.num_y_partitions}")
                    #intersecting_partitions.add(partitioned_map_grid.collision_partitioned_map[y][x])
                    intersecting_partitions.add(partitioned_map_grid.partitioned_map[y][x])
    return intersecting_partitions


def get_closest_intersecting_object_in_pmg(weapon, partitioned_map_grid, beam, screen_for_debug=None):
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

    intersected_partitions = get_intersecting_partitions(weapon, partitioned_map_grid, beam, screen_for_debug)
    if dev_constants.DEBUGGING_INTERSECTIONS:
        dev_constants.INTERSECTED_PARTITIONS_FOR_DEBUGGING = intersected_partitions


    for partition in intersected_partitions:
        hit, entity = get_closest_intersecting_object_in_partition(weapon, beam, partition, screen_for_debug)

        if screen_for_debug and hit is not None:
            translated_hit = helpers.translate_point_for_camera(weapon.owner, hit + beam.start_point)
            pygame.draw.circle(screen_for_debug, pygame.color.THECOLORS['aquamarine'], translated_hit, game_engine_constants.DEBUG_RADIUS)

        if hit is not None and entity is not None:
            closest_hit, closest_entity = update_closest(hit, entity, closest_hit, closest_entity)
    # Reposition relative to the player
    if closest_hit is not None:
        closest_hit = closest_hit + beam.start_point

    # Note that there will always be a closest element as the map is closed.
#    if dev_constants.CLIENT_VISUAL_DEBUGGING:
#        pygame.draw.circle(dev_constants.SCREEN_FOR_DEBUGGING, pygame.color.THECOLORS['gold'], helpers.translate_point_for_camera(weapon.owner, closest_hit), game_engine_constants.DEBUG_RADIUS)
#
    print(f"Closest Hit {closest_entity} at {closest_hit}")
    return closest_hit, closest_entity


def get_closest_intersecting_object_in_partition(weapon, beam, pmg, screen_for_debug=None):

    fire_origin = beam.start_point


    closest_hit = None
    closest_entity = None

    quadrant_info = beam.quadrant_info

    def update_closest(hit, entity, closest_hit, closest_entity):

        if closest_hit is None:
            closest_hit = hit
            closest_entity = entity
        else:
            if hit.magnitude() <= closest_hit.magnitude():
                closest_hit = hit
                closest_entity = entity
        return closest_hit, closest_entity

    fire_slope = beam.slope

    for b_wall in pmg.bounding_walls:

        if screen_for_debug is not None:
            pygame.draw.rect(screen_for_debug,pygame.color.THECOLORS['purple']  , b_wall.rect.move(weapon.owner.camera_v), width=1)
        top, left, bottom, right = b_wall.rect.top, b_wall.rect.left, b_wall.rect.bottom, b_wall.rect.right 
        ##print( top, left, bottom, right)
        translated_top, translated_left, translated_bottom, translated_right = top - fire_origin.y, left - fire_origin.x, bottom - fire_origin.y, right - fire_origin.x
        ##print("translated_top", "translated_left", "translated_bottom", "translated_right" )
        ##print(translated_top, translated_left, translated_bottom, translated_right )

        # y = fire_slope x <=> y/fire_slope = x (assuming fire_slope is non-zero)

        if beam.slope != math.inf:
            xr = translated_right
            if beam.slope == 0:
                yr = 0
            else:
                yr = fire_slope * xr
            xl = translated_left
            if beam.slope == 0:
                yl = 0
            else:
                yl = fire_slope * xl

            if translated_top <= yr <= translated_bottom and helpers.part_of_beam((xr, yr), beam):
                # Hit right side
                #print(f"hit right at ({translated_right}, {yr})")
                hit = pygame.math.Vector2((translated_right, yr))
                if (helpers.get_sign(hit.x), helpers.get_sign(hit.y)) == quadrant_info:
                    closest_hit, closest_entity = update_closest(hit, b_wall, closest_hit, closest_entity)

            if translated_top <= yl <= translated_bottom and helpers.part_of_beam((xl, yl), beam):
                # Hit right side
                #print(f"hit left at ({translated_left}, {yl})")
                hit = pygame.math.Vector2((translated_left, yl))
                if (helpers.get_sign(hit.x), helpers.get_sign(hit.y)) == quadrant_info:
                    closest_hit, closest_entity = update_closest(hit, b_wall, closest_hit, closest_entity)

        if beam.slope != 0: 
            yt = translated_top
            if beam.slope == math.inf:
                xt = 0
            else:
                xt = yt / fire_slope
            yb = translated_bottom
            if beam.slope == math.inf:
                xb = 0
            else:
                xb = yb / fire_slope

            if translated_left <= xt <= translated_right and helpers.part_of_beam((xt, yt), beam):
                #print(f"hit top at ({xt}, {translated_top})")
                hit = pygame.math.Vector2((xt, translated_top))
                if (helpers.get_sign(hit.x), helpers.get_sign(hit.y)) == quadrant_info:
                    closest_hit, closest_entity = update_closest(hit, b_wall, closest_hit, closest_entity)

            if translated_left <= xb <= translated_right and helpers.part_of_beam((xb, yb), beam):
                #print(f"hit bottom at ({xb}, {translated_bottom})")
                hit = pygame.math.Vector2((xb, translated_bottom))
                if (helpers.get_sign(hit.x), helpers.get_sign(hit.y)) == quadrant_info:
                    closest_hit, closest_entity = update_closest(hit, b_wall, closest_hit, closest_entity)

            #if len(hits) != 0:

    print(f"players in partition {pmg.players}")
    for body in pmg.players:

        #if body is not weapon.owner: # can't shoot self
        if type(weapon) is weapons.Hitscan and body is not weapon.owner: # can't shoot self TODO remove dependence on weapon, probably move this logic elsewhere

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

            m = beam.slope

            if m == math.inf:
                print("============================================= dealing with vertical explosion")
                # In this case then we are setting x = 0 in the equation and getting solutions
                """
                (x - p)**2 + (y - q)**2 = r**2 & x = 0

                <=> y**2 -2qy + q**2 + p**2 = r**2

                <=> y**2 -2qy + (q**2 + p**2 - r**2) = 0

                """
                a = 1
                b = -2 * q
                c = (p**2) + (q**2) - (r**2)
            else:
                # From initial derivation
                a = (m**2) + 1
                b = -2 * (p + (m * q)) 
                c = (p**2) + (q**2) - (r**2)

            discriminant = b**2 - (4 * a * c)

            if discriminant >= 0:
                #print("hit ball")
                # Then we have at least one solution
                if m == math.inf:
                    y = (-b + (discriminant)**(1/2) ) / (2 * a) 
                    x = 0
                else:
                    x = (-b + (discriminant)**(1/2) ) / (2 * a) 
                    y = m * x
                hit = pygame.math.Vector2((x,y))
                print(f"ball check - hit at {x, y}")
                if (helpers.get_sign(hit.x), helpers.get_sign(hit.y)) == quadrant_info and helpers.part_of_beam(hit, beam):
                    closest_hit, closest_entity = update_closest(hit, body, closest_hit, closest_entity)
                if discriminant > 0:
                    # Second solution is negative
                    if m == math.inf:
                        yn = (-b - (discriminant)**(1/2) ) / (2 * a) 
                        xn = 0
                    else:
                        xn = (-b - (discriminant)**(1/2) ) / (2 * a) 
                        yn = m * xn
                    hit = pygame.math.Vector2((xn,yn))
                    print(f"ball check 2 - hit at {xn, yn}")
                    print((helpers.get_sign(hit.x), helpers.get_sign(hit.y)),  quadrant_info, (helpers.get_sign(hit.x), helpers.get_sign(hit.y)) == quadrant_info,   helpers.part_of_beam(hit, beam))
            
                    if (helpers.get_sign(hit.x), helpers.get_sign(hit.y)) == quadrant_info and helpers.part_of_beam(hit, beam): # notice how we have to use the translated hit for part of beam
                        closest_hit, closest_entity = update_closest(hit, body, closest_hit, closest_entity)

    if closest_hit is not None:
        print(f"closest hit at {closest_hit + beam.start_point}, it is {closest_entity}")
        # returns position relative to player which is good
        return closest_hit, closest_entity
    else: 
        return closest_hit, closest_entity
