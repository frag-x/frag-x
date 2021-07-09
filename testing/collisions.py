import pygame, math
import map_loading
import logging

def clamp(val, min_val, max_val):
    return min(max(val, min_val), max_val)

def colliding_and_closest(body, b_wall):
    """Return if the body is colliding with a wall, 
    also return the closest point to the body on this wall"""
    top, left, bottom, right = b_wall.rect.top, b_wall.rect.left, b_wall.rect.bottom, b_wall.rect.right 
    closest_x = clamp(body.pos.x, left, right)
    closest_y = clamp(body.pos.y, top, bottom)
    closest_v = pygame.math.Vector2(closest_x, closest_y)

    return (closest_v - body.pos).magnitude() <= body.radius, closest_v

def simulate_collision_v2(body, b_wall, closest_v):
    top, left, bottom, right = b_wall.rect.top, b_wall.rect.left, b_wall.rect.bottom, b_wall.rect.right 

    ##print("==== COLLISION SIMULATION START ====")
    #print(f"top: {top}, left: {left}, bottom: {bottom}, right: {right}") 
    #print(f"closest: {closest_v.x} {closest_v.y}")

    top_visible, right_visible, bottom_visible, left_visible = b_wall.visible_sides

    
    side_to_visibility = {top: top_visible, left: left_visible, bottom: bottom_visible, right: right_visible}

    # Unstick amount should be relative to the amount of velocity we have 
    #unstick_amount = 1 + body.velocity.magnitude()/1000
    collision_depth = body.radius - (closest_v - body.pos).magnitude()
    extra_buffer = 3
    # TODO ABOUT TO SET THIS TO AN EXACT POSITION SOMETHING LIKE 
    unstick_amount = body.radius + extra_buffer

    velocity_reduction_multiplier = .5

    # Note that the previous position should not be colliding - you collide once and out
    #print(f"Body at {body.previous_pos.x} {body.previous_pos.y} before collision")
    #print(f"Body at {body.pos.x} {body.pos.y} during collision")


    """
     _____
    | ... |
    |.   .|
    |_..._|

    """

    fully_in = (left < closest_v.x < right) and (top < closest_v.y < bottom)

    """
     __A__ 
    |     |
    | ... |
    |.___.|    _____B_____
    | ... |   |    ...    |
    |     |   |   . | .   |
    |_____|   |____...____|

    """
    A = (left < closest_v.x < right) and ((closest_v.y == top and not top_visible) or (closest_v.y == bottom and not bottom_visible))
    B = (top < closest_v.y < bottom) and ((closest_v.x == left and not left_visible) or (closest_v.x == right and not right_visible))

    half_in = A or B

    if fully_in or half_in:
        #print("body is inside")
        prev_pos = body.previous_pos
        curr_pos = body.pos
        # Then we use the previous position, and get it's closest pos
        # Which is guarenteed to be neither half nor fully in
        # And use that to figure out what kind of it hit it is
        body.pos = prev_pos
        #print(closest_v.x, closest_v.y)
        colliding,  closest_v = colliding_and_closest(body, b_wall)
        assert colliding == False
        #print("corrected: ", closest_v.x, closest_v.y)
        # reset position and then continue
        body.pos = curr_pos

    """
       A1...      B1            C1       ... D1   
     ___._  .   _____         _____     .  _.___   
    |    ...   |     |       |     |     ...    | 
    |     |    |    ...     ...    |      |     |
    |_____|    |___._| .   . |_.___|      |_____|
                    ...     ...
    """

    A1 = (closest_v.x == right and closest_v.y == top) and (right_visible and top_visible)
    B1 = (closest_v.x == right and closest_v.y == bottom) and (right_visible and bottom_visible)
    C1 = (closest_v.x == left and closest_v.y == bottom) and (left_visible and bottom_visible)
    D1 = (closest_v.x == left and closest_v.y == top) and (left_visible and top_visible)

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
    A2 = closest_v.x == right and top < closest_v.y < bottom and right_visible
    B2 = closest_v.x == left and top < closest_v.y < bottom and left_visible
    C2 = closest_v.y == bottom and left < closest_v.x < right and bottom_visible
    D2 = closest_v.y == top and left < closest_v.x < right and top_visible

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

    A3 = (closest_v.x == right and (closest_v.y == top and not top_visible)) or \
            (closest_v.x == right and (closest_v.y == bottom and not bottom_visible))    
    B3 = (closest_v.x == left and (closest_v.y == top and not top_visible)) or \
            (closest_v.x == left and (closest_v.y == bottom and not bottom_visible))    
    C3 = (closest_v.y == top and (closest_v.x == left and not left_visible)) or \
            (closest_v.y == top and (closest_v.x == right and not right_visible))    
    D3 = (closest_v.y == bottom and (closest_v.x == left and not left_visible)) or \
            (closest_v.y == bottom and (closest_v.x == right and not right_visible))    

    case_3 = [A3, B3, C3, D3]

    #print(f"fully_in: {fully_in},\n half_in: {half_in},\n case1: {case_1},\n case2: {case_2},\n case3: {case_3}")

    if any(case_1):
        if A1:
            #print("top right")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, -math.tau/8)
            rotated_vel.y *= -velocity_reduction_multiplier
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, math.tau/8)
            body.velocity = vel

            r_v = pygame.math.Vector2(unstick_amount, 0)
            r_v.rotate_ip_rad(-math.tau/8)

            body.pos = closest_v + r_v

        elif B1:
            #print("bottom right")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, math.tau/8)
            rotated_vel.y *= -velocity_reduction_multiplier
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, -math.tau/8)
            body.velocity = vel 

            r_v = pygame.math.Vector2(unstick_amount, 0)
            r_v.rotate_ip_rad(math.tau/8)

            body.pos = closest_v + r_v
        elif C1:
            #print("bottom left")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, -math.tau/8)
            rotated_vel.y *= -velocity_reduction_multiplier
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, math.tau/8)
            body.velocity = vel 

            r_v = pygame.math.Vector2(-unstick_amount, 0)
            r_v.rotate_ip_rad(-math.tau/8)

            body.pos = closest_v + r_v

        elif D1:
            #print("top left")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, math.tau/8)

            rotated_vel.y *= -velocity_reduction_multiplier
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, -math.tau/8)
            body.velocity = vel 

            r_v = pygame.math.Vector2(-unstick_amount, 0)
            r_v.rotate_ip_rad(math.tau/8)

            body.pos = closest_v + r_v

    elif any(case_2):
        if A2:
            right_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier)
        elif B2:
            left_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier)
        elif C2:
            bottom_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier)
        elif D2:
            top_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier)
    elif any(case_3):
        if A3:
            right_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier)
        elif B3:
            left_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier)
        elif C3:
            top_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier)
        elif D3:
            bottom_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier)
    else:
        #print("a collision was detected - but for some reason we didn't do anything! - this is bad")
        pass
        

    #print(f"Body at {body.pos.x} {body.pos.y} after collision")
    #print("==== COLLISION SIMULATION END ====")

# TODO combine functionality by realizing you can always do body.velocity.[xy] *= 1
def right_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier):
    #print("right")
    body.velocity.x *= (-1 * velocity_reduction_multiplier)
    # Unstick player
    body.pos = closest_v + pygame.math.Vector2(unstick_amount, 0)

def left_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier):
    #print("left")
    body.velocity.x *= (-1 * velocity_reduction_multiplier)
    # Unstick player
    body.pos = closest_v + pygame.math.Vector2(-unstick_amount, 0)

def top_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier):
    #print("top")
    body.velocity.y *= (-1 * velocity_reduction_multiplier)
    # Unstick player
    body.pos = closest_v + pygame.math.Vector2(0, -unstick_amount)

def bottom_reflect(body, unstick_amount, closest_v, velocity_reduction_multiplier):
    #print("bottom")
    body.velocity.y *= (-1 * velocity_reduction_multiplier)
    # Unstick player
    body.pos = closest_v + pygame.math.Vector2(0, unstick_amount)


