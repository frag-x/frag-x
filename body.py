import math, pygame
import game_engine_constants


# TODO make this a simulation object
class Body:
    """An object that moves within a map"""

    def __init__(self, start_pos, radius, friction):
        self.position = pygame.math.Vector2(start_pos)
        self.previous_position = (
            None  # This represents the position of the player of the previous frame
        )
        self.radius = radius
        # mass is equal to area
        self.mass = math.pi * (self.radius ** 2)

        self.velocity = pygame.math.Vector2(0, 0)

        self.max_speed = game_engine_constants.MAX_SPEED
        # Acceleration is constant
        self.friction = friction

        self.partition = None
        self.collision_partition = None


class ConstantVelocityBody(Body):
    def __init__(self, start_pos, radius, friction, velocity: pygame.math.Vector2):
        super().__init__(start_pos, radius, friction)
        self.velocity = velocity
        
    def step(self, delta_time: float):
        # Everything is measured per second
        delta_time /= 1000
        self.previous_position = pygame.math.Vector2(self.position.x, self.position.y)
        self.position += self.velocity * delta_time


class ConstantAccelerationBody(Body):
    def __init__(self, start_pos, radius, friction, acceleration):
        super().__init__(start_pos, radius, friction)
        self.acceleration = acceleration

    def step(self, movement_vector: pygame.math.Vector2, delta_time: float):
        delta_time /= 1000  # TODO this is arbitrary and bad

        self.previous_position = pygame.math.Vector2(self.position.x, self.position.y)

        velocity_change = self.acceleration * delta_time

        if not (movement_vector.x == 0 and movement_vector.y == 0):
            pygame.math.Vector2.normalize_ip(movement_vector)

            new_velocity_update = velocity_change * movement_vector

            self.velocity += new_velocity_update
            if self.velocity.magnitude() > self.max_speed:
                self.velocity = self.velocity.normalize() * self.max_speed

        else:
            # If no buttons are being pressed then we can apply friction to slow them down
            # We will slow them down at the same speed they would speed up by
            if self.velocity.magnitude() - self.friction > 0:
                self.velocity -= self.velocity * self.friction
            else:
                # If we can't subtract any more, just set it to zero
                self.velocity.x = 0
                self.velocity.y = 0

        # Based on our acceleration calculate what the velocity update should be
        # Change in position = velocity * change in time
        self.position += self.velocity * delta_time
