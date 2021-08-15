import math, pygame
import game_engine_constants


class Body:
    """An object that moves in the game, it has constant acceleration"""

    def __init__(self, start_pos, radius, friction):
        self.pos = pygame.math.Vector2(start_pos)
        self.previous_pos = (
            None  # This represents the position of the player of the previous frame
        )
        self.radius = radius
        # mass is equal to area
        self.mass = math.pi * (self.radius ** 2)

        self.velocity = pygame.math.Vector2(0, 0)

        self.max_speed = game_engine_constants.MAX_SPEED
        # Acceleration is constant
        self.friction = friction


class ConstantVelocityBody(Body):
    def __init__(self, start_pos, radius, friction, velocity):
        super().__init__(start_pos, radius, friction)
        self.velocity = velocity


class ConstantAccelerationBody(Body):
    def __init__(self, start_pos, radius, friction, acceleration):
        super().__init__(start_pos, radius, friction)
        self.acceleration = acceleration
