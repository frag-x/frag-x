import pygame

def elastic_collision_update(b1, b2):
    m1, m2 = b1.mass, b2.mass
    M = m1 + m2

    p1, p2 = b1.pos, b2.pos

    len_squared = (p1 - p2).length_squared()

    v1, v2 = b1.velocity, b2.velocity

    # Compute their new velocities - TODO understand this formula
    u1 = v1 - (2 * m2 / M) * (pygame.math.Vector2.dot(v1 - v2, p1 - p2) / (len_squared)) * (p1 - p2)
    u2 = v2 - (2 * m1 / M) * (pygame.math.Vector2.dot(v2 - v1, p2 - p1) / (len_squared)) * (p2 - p1)

    b1.velocity = u1
    b2.velocity = u2

