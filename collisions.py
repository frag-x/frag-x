import pygame
def colliding(p1: pygame.Vector2, r1: float, p2: pygame.Vector2, r2: float) -> bool:
    center_distance = (p2 - p1).magnitude()
    min_distance = r1 + r2
    return center_distance <= min_distance
    



