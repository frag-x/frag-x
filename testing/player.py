import pygame
import math

def magnitude(v):
  return math.sqrt(v.x ** 2 + v.y ** 2)

class Player(pygame.sprite.Sprite):
    def __init__(self,start_pos, width, height,color, movement_keys, s_width, s_height):
        """
        Initialize a player

        Movement Keys is a set of pygame keys in the following order:
         
        Left Up Right Down (clockwise order)
        """
        pygame.sprite.Sprite.__init__(self)
        self.pos = pygame.math.Vector2(start_pos)
        self.s_width= s_width
        self.s_height = s_height
        self.width = width
        self.radius = width/2
        self.height = height
        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        self.image = pygame.Surface([self.width, self.height], pygame.SRCALPHA, 32)
        #self.image.fill(color)
        pygame.draw.circle(self.image, pygame.color.THECOLORS['blue'], (width/2, height/2), self.radius)

        # Fetch the rectangle object that has the dimensions of the image
        # Update the position of this object by setting the values of rect.x and rect.y
        self.rect = self.image.get_rect()
        self.movement_vector = pygame.math.Vector2(0,0)
        self.movement_keys = movement_keys

        self.velocity = pygame.math.Vector2(0,0)

        #self.camera = pygame.math.Vector2d(self.pos.x, self.pos.y)
        self.camera = self.pos

        self.max_speed = 4000
        self.acceleration = 2000
        self.friction = 0.05



    def update(self, events, delta_time):
        keys = pygame.key.get_pressed()

        l, u, r, d = self.movement_keys

        self.movement_vector.x = int(keys[r]) - int(keys[l]) 
        self.movement_vector.y = -(int(keys[u]) - int(keys[d]))

        velocity_change = self.acceleration * delta_time

        if not (self.movement_vector.x == 0 and self.movement_vector.y == 0):
            pygame.math.Vector2.normalize_ip(self.movement_vector)
            self.apply_movement(velocity_change * self.movement_vector)
        else:
            # If no buttons are being pressed then we can apply friction to slow them down
            # We will slow them down at the same speed they would speed up by
            self.apply_friction()

        # Based on our acceleration calculate what the velocity update should be

        # Save the previous position for collisions

        self.previous_pos = pygame.math.Vector2(self.pos.x, self.pos.y)

        # Change in position = velocity * change in time
        self.pos += self.velocity * delta_time

        #self.pos.x %= self.s_width
        #self.pos.y %= self.s_height
        self.rect.center = self.pos
    
    def apply_friction(self):
        if magnitude(self.velocity) - self.friction > 0:
            self.velocity -= self.velocity * self.friction
        else:
            # If we can't subtract any more, just set it to zero
            self.velocity.x = 0
            self.velocity.y = 0

    def apply_movement(self, new_velocity_update):
        self.velocity += new_velocity_update
        if magnitude(self.velocity) > self.max_speed:
            self.velocity = self.velocity.normalize()  * self.max_speed
        
