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

    #print("==== COLLISION SIMULATION START ====")
    print(f"top: {top}, left: {left}, bottom: {bottom}, right: {right}") 
    print(f"closest: {closest_v.x} {closest_v.y}")

    top_visible, right_visible, bottom_visible, left_visible = b_wall.visible_sides

    
    side_to_visibility = {top: top_visible, left: left_visible, bottom: bottom_visible, right: right_visible}

    # Unstick amount should be relative to the amount of velocity we have 
    #unstick_amount = 1 + body.velocity.magnitude()/1000
    collision_depth = body.radius - (closest_v - body.pos).magnitude()
    unstick_amount = collision_depth + 1

    # Note that the previous position should not be colliding - you collide once and out
    print(f"Body at {body.previous_pos.x} {body.previous_pos.y} before collision")
    print(f"Body at {body.pos.x} {body.pos.y} during collision")


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
        print("body is inside")
        prev_pos = body.previous_pos
        curr_pos = body.pos
        # Then we use the previous position, and get it's closest pos
        # Which is guarenteed to be neither half nor fully in
        # And use that to figure out what kind of it hit it is
        body.pos = prev_pos
        print(closest_v.x, closest_v.y)
        colliding,  closest_v = colliding_and_closest(body, b_wall)
        assert colliding == False
        print("corrected: ", closest_v.x, closest_v.y)
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

    print(f"fully_in: {fully_in},\n half_in: {half_in},\n case1: {case_1},\n case2: {case_2},\n case3: {case_3}")

    if any(case_1):
        if A1:
            print("top right")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, -math.tau/8)
            rotated_vel.y *= -1
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, math.tau/8)
            body.velocity = vel

            # Unstick player
            body.pos.x += unstick_amount # right
            body.pos.y -= unstick_amount # up

        elif B1:
            print("bottom right")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, math.tau/8)
            rotated_vel.y *= -1
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, -math.tau/8)
            body.velocity = vel

            # Unstick player
            body.pos.x += unstick_amount # right
            body.pos.y += unstick_amount # down
        elif C1:
            print("bottom left")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, -math.tau/8)
            rotated_vel.y *= -1
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, math.tau/8)
            body.velocity = vel

            # Unstick player TODO: use a vector which is perpendicular to the tangent
            body.pos.x -= unstick_amount # left (this doesn't make sense??? depending on the direction you come in at)
            body.pos.y -= unstick_amount # down
        elif D1:
            print("top left")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, math.tau/8)
            rotated_vel.y *= -1
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, -math.tau/8)
            body.velocity = vel

            # Unstick player
            body.pos.x -= unstick_amount
            body.pos.y += unstick_amount
    elif any(case_2):
        if A2:
            right_reflect(body, unstick_amount)
        elif B2:
            left_reflect(body, unstick_amount)
        elif C2:
            bottom_reflect(body, unstick_amount)
        elif D2:
            top_reflect(body, unstick_amount)
    elif any(case_3):
        if A3:
            right_reflect(body, unstick_amount)
        elif B3:
            left_reflect(body, unstick_amount)
        elif C3:
            top_reflect(body, unstick_amount)
        elif D3:
            bottom_reflect(body, unstick_amount)
    else:
        print("a collision was detected - but for some reason we didn't do anything! - this is bad")
        

    print(f"Body at {body.pos.x} {body.pos.y} after collision")
    print("==== COLLISION SIMULATION END ====")

def right_reflect(body, unstick_amount):
    print("right")
    body.velocity.x *= -1
    # Unstick player
    body.pos.x += unstick_amount

def left_reflect(body, unstick_amount):
    print("left")
    body.velocity.x *= -1
    # Unstick player
    body.pos.x -= unstick_amount

def top_reflect(body, unstick_amount):
    print("top")
    body.velocity.y *= -1
    # Unstick player
    body.pos.y -= unstick_amount

def bottom_reflect(body, unstick_amount):
    print("bottom")
    body.velocity.y *= -1
    # Unstick player
    body.pos.y += unstick_amount


















        
def simulate_collision(body, b_wall, closest_v):
    top, left, bottom, right = b_wall.rect.top, b_wall.rect.left, b_wall.rect.bottom, b_wall.rect.right 

    print("==== COLLISION SIMULATION START ====")
    print(f"top: {top}, left: {left}, bottom: {bottom}, right: {right}") 
    print(f"closest: {closest_v.x} {closest_v.y}")

    top_visible, right_visible, bottom_visible, left_visible = b_wall.visible_sides

    side_to_visibility = {top: top_visible, left: left_visible, bottom: bottom_visible, right: right_visible}

    # Unstick amount should be relative to the amount of velocity we have 
    #unstick_amount = 1 + body.velocity.magnitude()/1000
    collision_depth = body.radius - (closest_v - body.pos).magnitude()
    unstick_amount = collision_depth + 1

    print(f"Body at {body.previous_pos.x} {body.previous_pos.y} before collision")
    print(f"Body at {body.pos.x} {body.pos.y} during collision")

    ## If the ball has gone inside then use closest_v from previous position
    #fully_in = left < closest_v.x < right and top < closest_v.y < bottom
    #half_in = (left < closest_v.x < right and top <= closest_v.y <= bottom and () or (left <= closest_v.x <= right and top < closest_v.y < bottom)

    #if fully_in or half_in:
    #    print("body is inside")
    #    prev_pos = body.previous_pos
    #    curr_pos = body.pos
    #    # Then we use the previous position, and get it's closest pos
    #    # Which is guarenteed to be neither half nor fully in
    #    # And use that to figure out what kind of it hit it is
    #    body.pos = prev_pos
    #    print(closest_v.x, closest_v.y)
    #    _,  closest_v = colliding_and_closest(body, b_wall)
    #    print("corrected: ", closest_v.x, closest_v.y)
    #    body.pos = curr_pos

    #if closest_v.x == right:
    #    if right_visible:
    #    elif 


    if closest_v.x == right and right_visible:
        print("hit right")

        if closest_v.y == top and top_visible:
            # Corner bounce top right
            print("top right")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, -math.tau/8)
            rotated_vel.y *= -1
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, math.tau/8)
            body.velocity = vel

            # Unstick player
            body.pos.x += unstick_amount
            body.pos.y -= unstick_amount

        elif closest_v.y == bottom and bottom_visible:
            # Corner bounce bottom right
            print("bottom right")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, math.tau/8)
            rotated_vel.y *= -1
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, -math.tau/8)
            body.velocity = vel

            # Unstick player
            body.pos.x += unstick_amount
            body.pos.y += unstick_amount

        #elif top < closest_v.y < bottom:
        else:
            # Simple bounce of right wall
            print("right")
            body.velocity.x *= -1
            # Unstick player
            body.pos.x += unstick_amount



    elif closest_v.x == left and left_visible:
        print("hit left")

        if closest_v.y == top and top_visible:
            # Corner bounce top left
            print("top left")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, math.tau/8)
            rotated_vel.y *= -1
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, -math.tau/8)
            body.velocity = vel

            # Unstick player
            body.pos.x -= unstick_amount
            body.pos.y -= unstick_amount

        elif closest_v.y == bottom and bottom_visible:
            # Corner bounce bottom left
            print("bottom left")
            rotated_vel = pygame.math.Vector2.rotate_rad(body.velocity, -math.tau/8)
            rotated_vel.y *= -1
            vel = pygame.math.Vector2.rotate_rad(rotated_vel, math.tau/8)
            body.velocity = vel

            # Unstick player
            body.pos.x -= unstick_amount
            body.pos.y += unstick_amount

        #elif top < closest_v.y < bottom:
        else:
            # Simple bounce of left wall
            print("left")
            body.velocity.x *= -1
            # Unstick player
            body.pos.x -= unstick_amount

    #elif left < closest_v.x < right:

    #    print("hit between left and right")

    #    if closest_v.y == top and top_visible:
    #        # Simple top bounce
    #        print("top")
    #        body.velocity.y *= -1
    #        body.pos.y -= unstick_amount

    #    elif closest_v.y == bottom and bottom_visible:
    #        # simple bottom bounce
    #        print("bottom")
    #        body.velocity.y *= -1
    #        body.pos.y += unstick_amount

    #    elif top < closest_v.y < bottom:
    #        # Dealt with at start of function - impossible to get here
    #        print("something impossible happened")
    #        pass

    print(f"Body at {body.pos.x} {body.pos.y} after collision")
    print("==== COLLISION SIMULATION END ====")
