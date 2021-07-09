import math
import pygame

class Weapon:
    def __init__(self, fire_rate: float, owner, power):
        self.fire_rate = fire_rate
        self.owner = owner
        self.power = power

class Hitscan(Weapon):
    def __init__(self, fire_rate: float, owner, power: float):
        super().__init__(fire_rate, owner, power)


    def get_all_intersecting_objects(self, bounding_walls, bodies = []):

        fire_origin = self.owner.pos

        delta_y = math.sin(self.owner.rotation_angle)

        delta_x = math.cos(self.owner.rotation_angle)

        closest_hit = None
        closest_entity = None

        def get_sign(num):
            if num > 0:
                return 1
            elif num < 0:
                return -1
            else:
                return 0

        quadrant_info = (get_sign(delta_x), get_sign(delta_y))

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
            fire_slope = delta_y/delta_x

            for b_wall in bounding_walls:
                top, left, bottom, right = b_wall.rect.top, b_wall.rect.left, b_wall.rect.bottom, b_wall.rect.right 
                ##print( top, left, bottom, right)
                translated_top, translated_left, translated_bottom, translated_right = top - fire_origin.y, left - fire_origin.x, bottom - fire_origin.y, right - fire_origin.x
                ##print("translated_top", "translated_left", "translated_bottom", "translated_right" )
                ##print(translated_top, translated_left, translated_bottom, translated_right )

                # y = fire_slope x <=> y/fire_slope = x (assuming fire_slope is non-zero)

                yr = fire_slope * translated_right
                yl = fire_slope * translated_left

                if translated_top <= yr <= translated_bottom:
                    # Hit right side
                    #print(f"hit right at ({translated_right}, {yr})")
                    hit = pygame.math.Vector2((translated_right, yr))
                    if (get_sign(hit.x), get_sign(hit.y)) == quadrant_info:
                        closest_hit, closest_entity = update_closest(hit, b_wall, closest_hit, closest_entity)

                if translated_top <= yl <= translated_bottom:
                    # Hit right side
                    #print(f"hit left at ({translated_left}, {yl})")
                    hit = pygame.math.Vector2((translated_left, yl))
                    if (get_sign(hit.x), get_sign(hit.y)) == quadrant_info:
                        closest_hit, closest_entity = update_closest(hit, b_wall, closest_hit, closest_entity)

                xt = translated_top / fire_slope
                xb = translated_bottom / fire_slope

                if translated_left <= xt <= translated_right:
                    #print(f"hit top at ({xt}, {translated_top})")
                    hit = pygame.math.Vector2((xt, translated_top))
                    if (get_sign(hit.x), get_sign(hit.y)) == quadrant_info:
                        closest_hit, closest_entity = update_closest(hit, b_wall, closest_hit, closest_entity)

                if translated_left <= xb <= translated_right:
                    #print(f"hit bottom at ({xb}, {translated_bottom})")
                    hit = pygame.math.Vector2((xb, translated_bottom))
                    if (get_sign(hit.x), get_sign(hit.y)) == quadrant_info:
                        closest_hit, closest_entity = update_closest(hit, b_wall, closest_hit, closest_entity)

                #if len(hits) != 0:

            for body in bodies:

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

                a = (m**2) + 1
                b = -2 * (p + (m * q)) 
                c = (p**2) + (q**2) - (r**2)

                discriminant = b**2 - (4 * a * c)

                if discriminant >= 0:
                    #print("hit ball")
                    # Then we have at least one solution
                    x = (-b + (discriminant)**(1/2) ) / (2 * a) 
                    y = m * x
                    hit = pygame.math.Vector2((x,y))
                    if (get_sign(hit.x), get_sign(hit.y)) == quadrant_info:
                        closest_hit, closest_entity = update_closest(hit, body, closest_hit, closest_entity)
                    if discriminant > 0:
                        # Second solution is negative
                        xn = (-b - (discriminant)**(1/2) ) / (2 * a) 
                        yn = m * xn
                        hit = pygame.math.Vector2((xn,yn))
                        if (get_sign(hit.x), get_sign(hit.y)) == quadrant_info:
                            closest_hit, closest_entity = update_closest(hit, body, closest_hit, closest_entity)
                    
            return closest_hit, closest_entity

