#import pygame
#
#def compute_new_position_using_acceleration(movement_vector, current_velocity, delta_time): 
#    """Movement vector is the current movement that is being applied to this body
#
#    delta_time represents the amount of time in the future we would like to predict
#    our position using our physics implmentation
#
#    """
#
#    velocity_change = self.acceleration * delta_time
#
#    if not (movement_vector.x == 0 and movement_vector.y == 0):
#        pygame.math.Vector2.normalize_ip(movement_vector)
#        self.apply_movement(velocity_change * self.movement_vector)
#    else:
#        # If no buttons are being pressed then we can apply friction to slow them down
#        # We will slow them down at the same speed they would speed up by
#        self.apply_friction()
#
#    # Based on our acceleration calculate what the velocity update should be
#
#    # Change in position = velocity * change in time
#    self.pos += self.velocity * delta_time
#    self.pos.x %= self.s_width
#    self.pos.y %= self.s_height
#    self.rect.center = self.pos
#
#def apply_friction(self):
#    if magnitude(self.velocity) - self.friction > 0:
#        self.velocity -= self.velocity * self.friction
#    else:
#        # If we can't subtract any more, just set it to zero
#        self.velocity.x = 0
#        self.velocity.y = 0
#
#def apply_movement(self, velocity,  new_velocity_update):
#    """Given velocity, we apply the result of the movement
#    and return the new velocity"""
#    self.velocity += new_velocity_update
#    if magnitude(self.velocity) > self.max_speed:
#        self.velocity = self.velocity.normalize() * self.max_speed
#    
#    
#
