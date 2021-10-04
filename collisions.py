import pygame, math, time
import logging

import game_engine_constants
from body import Body


def simulate_elastic_collision_between_bodies(b1, b2):
    """
    simulate an elastic collision

    proof: https://gitlab.com/cuppajoeman/knowledge-data/-/blob/master/Velocity_after_Elastic_Collision_between_two_2_Dimensional_Bodies-MjRbjnneR2XhTD5jMv2.pdf

    :param b1: the first body
    :param b2: the second body
    :return:
    """
    if b1.position != b2.position:
        m1, m2 = b1.mass, b2.mass

        p1, p2 = b1.position, b2.position

        v1, v2 = b1.velocity, b2.velocity

        u = (p1 - p2).normalize()

        v1_prime = (
            v1 + (((2 * m2) / (m1 + m2)) * pygame.math.Vector2.dot(u, v2 - v1)) * u
        )

        v2_prime = (
            v2 + (((2 * m1) / (m1 + m2)) * pygame.math.Vector2.dot(u, v1 - v2)) * u
        )

        b1.velocity = v1_prime
        b2.velocity = v2_prime

        print(v1_prime, v2_prime)


def bodies_colliding(body_1: Body, body_2: Body) -> bool:
    p1, r1 = body_1.position, body_1.radius
    p2, r2 = body_2.position, body_2.radius
    center_distance = (p2 - p1).magnitude()
    min_distance = r1 + r2
    return center_distance <= min_distance


def clamp(val, min_val, max_val):
    return min(max(val, min_val), max_val)


def is_colliding_with_wall(body, b_wall):
    """Return if the body is colliding with a wall"""
    closest_v = get_closest_point_on_wall(body, b_wall)
    return (closest_v - body.position).magnitude() <= body.radius


def get_closest_point_on_wall(body, b_wall) -> pygame.math.Vector2:
    """Return the closest point to the body on this wall"""
    top, left, bottom, right = (
        b_wall.rect.top,
        b_wall.rect.left,
        b_wall.rect.bottom,
        b_wall.rect.right,
    )
    closest_x = clamp(body.position.x, left, right)
    closest_y = clamp(body.position.y, top, bottom)

    # If the body is inside the wall this makes sure to force it to be on the edge.
    closest_x_on_wall = min([left, right], key=lambda x: abs(x - closest_x))
    closest_y_on_wall = min([bottom, top], key=lambda y: abs(y - closest_y))

    closest_point_on_wall = pygame.math.Vector2(closest_x_on_wall, closest_y_on_wall)

    return closest_point_on_wall


def simulate_body_wall_collision(body, b_wall):
    """
    Given a body that is colliding with a ball simulate a collision
    :param body:
    :param b_wall:
    :return:
    """

    start_collision_simulation_time = time.time()

    closest_point_on_wall = get_closest_point_on_wall(body, b_wall)

    top, left, bottom, right = (
        b_wall.rect.top,
        b_wall.rect.left,
        b_wall.rect.bottom,
        b_wall.rect.right,
    )

    top_visible, right_visible, bottom_visible, left_visible = b_wall.visible_sides

    # Unstick amount should be relative to the amount of velocity we have
    # unstick_amount = 1 + body.velocity.magnitude()/1000
    extra_buffer = 3
    # TODO set this to the amount we are in there
    unstick_amount = body.radius + extra_buffer

    """
     _____
    | ... |
    |.   .|
    |_..._|

    """

    fully_in = (left < closest_point_on_wall.x < right) and (
        top < closest_point_on_wall.y < bottom
    )

    """
     __A__ 
    |     |
    | ... |
    |.___.|    _____B_____
    | ... |   |    ...    |
    |     |   |   . | .   |
    |_____|   |____...____|

    """
    A = (left < closest_point_on_wall.x < right) and (
        (closest_point_on_wall.y == top and not top_visible)
        or (closest_point_on_wall.y == bottom and not bottom_visible)
    )

    B = (top < closest_point_on_wall.y < bottom) and (
        (closest_point_on_wall.x == left and not left_visible)
        or (closest_point_on_wall.x == right and not right_visible)
    )

    half_in = A or B

    # TODO context was the code which sets position to the prev one because I fixed the get closest point on wall
    if fully_in or half_in:
        prev_pos = body.previous_position
        curr_pos = body.position
        # Then we use the previous position, and get it's closest position
        # Which is guarenteed to be neither half nor fully in
        # And use that to figure out what kind of it hit it is
        body.position = prev_pos
        closest_point_on_wall = get_closest_point_on_wall(body, b_wall)
        # assert colliding == False
        # reset position and then continue
        body.position = curr_pos

    """
       A1...      B1            C1       ... D1   
     ___._  .   _____         _____     .  _.___   
    |    ...   |     |       |     |     ...    | 
    |     |    |    ...     ...    |      |     |
    |_____|    |___._| .   . |_.___|      |_____|
                    ...     ...
    """

    A1 = (closest_point_on_wall.x == right and closest_point_on_wall.y == top) and (
        right_visible and top_visible
    )
    B1 = (closest_point_on_wall.x == right and closest_point_on_wall.y == bottom) and (
        right_visible and bottom_visible
    )
    C1 = (closest_point_on_wall.x == left and closest_point_on_wall.y == bottom) and (
        left_visible and bottom_visible
    )
    D1 = (closest_point_on_wall.x == left and closest_point_on_wall.y == top) and (
        left_visible and top_visible
    )

    case_1 = [A1, B1, C1, D1]

    """
                                       D2
      A2           B2        C2        ...    
     _____        _____     _____     .___.  
    |    ...    ...    |   |     |   | ... |
    |   . | .  . | .   |   | ... |   |     |
    |____...    ...___ |   |.___.|   |_____|
                             ...      

    """
    A2 = (
        closest_point_on_wall.x == right
        and top < closest_point_on_wall.y < bottom
        and right_visible
    )
    B2 = (
        closest_point_on_wall.x == left
        and top < closest_point_on_wall.y < bottom
        and left_visible
    )
    C2 = (
        closest_point_on_wall.y == bottom
        and left < closest_point_on_wall.x < right
        and bottom_visible
    )
    D2 = (
        closest_point_on_wall.y == top
        and left < closest_point_on_wall.x < right
        and top_visible
    )

    case_2 = [A2, B2, C2, D2]

    """

     _A3__        _B3__         C3           _____ _____
    |     |      |     |                    |     |     |
    |   ...     ...    |        ...         |    ...    | 
    |__.__|.   . |_.___|    ___._ _.___     |___._|_.___|
    |   ...     ...    |   |    ...    |         ...
    |     |      |     |   |     |     |
    |_____|      |_____|   |_____|_____|         D3


    """

    A3 = (
        closest_point_on_wall.x == right
        and (closest_point_on_wall.y == top and not top_visible)
    ) or (
        closest_point_on_wall.x == right
        and (closest_point_on_wall.y == bottom and not bottom_visible)
    )
    B3 = (
        closest_point_on_wall.x == left
        and (closest_point_on_wall.y == top and not top_visible)
    ) or (
        closest_point_on_wall.x == left
        and (closest_point_on_wall.y == bottom and not bottom_visible)
    )
    C3 = (
        closest_point_on_wall.y == top
        and (closest_point_on_wall.x == left and not left_visible)
    ) or (
        closest_point_on_wall.y == top
        and (closest_point_on_wall.x == right and not right_visible)
    )
    D3 = (
        closest_point_on_wall.y == bottom
        and (closest_point_on_wall.x == left and not left_visible)
    ) or (
        closest_point_on_wall.y == bottom
        and (closest_point_on_wall.x == right and not right_visible)
    )

    case_3 = [A3, B3, C3, D3]

    logging.info(
        f"fully_in: {fully_in},\n half_in: {half_in},\n case1: {case_1},\n case2: {case_2},\n case3: {case_3}"
    )

    if any(case_1):
        if A1:
            logging.info("top right")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, -math.tau / 8)
            rotated_vel.y *= -game_engine_constants.VELOCITY_REDUCTION_MODIFIER
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, math.tau / 8)
            body.velocity = vel

            r_v = pygame.math.Vector2(unstick_amount, 0)
            r_v.rotate_ip_rad(-math.tau / 8)

            body.position = closest_point_on_wall + r_v

        elif B1:
            logging.info("bottom right")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, math.tau / 8)
            rotated_vel.y *= -game_engine_constants.VELOCITY_REDUCTION_MODIFIER
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, -math.tau / 8)
            body.velocity = vel

            r_v = pygame.math.Vector2(unstick_amount, 0)
            r_v.rotate_ip_rad(math.tau / 8)

            body.position = closest_point_on_wall + r_v
        elif C1:
            logging.info("bottom left")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, -math.tau / 8)
            rotated_vel.y *= -game_engine_constants.VELOCITY_REDUCTION_MODIFIER
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, math.tau / 8)
            body.velocity = vel

            r_v = pygame.math.Vector2(-unstick_amount, 0)
            r_v.rotate_ip_rad(-math.tau / 8)

            body.position = closest_point_on_wall + r_v

        elif D1:
            logging.info("top left")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, math.tau / 8)

            rotated_vel.y *= -game_engine_constants.VELOCITY_REDUCTION_MODIFIER
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, -math.tau / 8)
            body.velocity = vel

            r_v = pygame.math.Vector2(-unstick_amount, 0)
            r_v.rotate_ip_rad(math.tau / 8)

            body.position = closest_point_on_wall + r_v

    elif any(case_2):
        if A2:
            right_reflect(
                body,
                unstick_amount,
                closest_point_on_wall,
                game_engine_constants.VELOCITY_REDUCTION_MODIFIER,
            )
        elif B2:
            left_reflect(
                body,
                unstick_amount,
                closest_point_on_wall,
                game_engine_constants.VELOCITY_REDUCTION_MODIFIER,
            )
        elif C2:
            bottom_reflect(
                body,
                unstick_amount,
                closest_point_on_wall,
                game_engine_constants.VELOCITY_REDUCTION_MODIFIER,
            )
        elif D2:
            top_reflect(
                body,
                unstick_amount,
                closest_point_on_wall,
                game_engine_constants.VELOCITY_REDUCTION_MODIFIER,
            )
    elif any(case_3):
        if A3:
            right_reflect(
                body,
                unstick_amount,
                closest_point_on_wall,
                game_engine_constants.VELOCITY_REDUCTION_MODIFIER,
            )
        elif B3:
            left_reflect(
                body,
                unstick_amount,
                closest_point_on_wall,
                game_engine_constants.VELOCITY_REDUCTION_MODIFIER,
            )
        elif C3:
            top_reflect(
                body,
                unstick_amount,
                closest_point_on_wall,
                game_engine_constants.VELOCITY_REDUCTION_MODIFIER,
            )
        elif D3:
            bottom_reflect(
                body,
                unstick_amount,
                closest_point_on_wall,
                game_engine_constants.VELOCITY_REDUCTION_MODIFIER,
            )
    else:
        logging.info(
            "a collision was detected - but for some reason we didn't do anything! - this is bad"
        )
        pass

    logging.info(f"Body at {body.position.x} {body.position.y} after collision")

    end_collision_simulation_time = time.time()
    logging.info(
        f"==== WALL COLLISION SIMULATION END | TIME TAKEN: {end_collision_simulation_time - start_collision_simulation_time} ===="
    )


# TODO combine functionality by realizing you can always do body.velocity.[xy] *= 1
def right_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier):
    logging.info("right")
    body.velocity.x *= -1 * velocity_reduction_multiplier
    # Unstick player
    body.position = closest_v + pygame.math.Vector2(unstick_amount, 0)


def left_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier):
    logging.info("left")
    body.velocity.x *= -1 * velocity_reduction_multiplier
    # Unstick player
    body.position = closest_v + pygame.math.Vector2(-unstick_amount, 0)


def top_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier):
    logging.info("top")
    body.velocity.y *= -1 * velocity_reduction_multiplier
    # Unstick player
    body.position = closest_v + pygame.math.Vector2(0, -unstick_amount)


def bottom_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier):
    logging.info("bottom")
    body.velocity.y *= -1 * velocity_reduction_multiplier
    # Unstick player
    body.position = closest_v + pygame.math.Vector2(0, unstick_amount)
