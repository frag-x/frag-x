import pygame
import math
from game_engine_constants import WIDTH, HEIGHT
from converters import convert_player_data_to_str, convert_str_to_player_data, convert_pos_str_to_player_pos, convert_player_pos_to_pos_str

def magnitude(v):
  return math.sqrt(v.x ** 2 + v.y ** 2)


class ClientPlayer(pygame.sprite.Sprite):
    """A client player is a representation of a player which only stores enough information to draw
    it to the screen
    """

    def __init__(self,start_pos, width, height,color, movement_keys, s_width, s_height, server):
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
        self.height = height
        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.server = server

        # Fetch the rectangle object that has the dimensions of the image
        # Update the position of this object by setting the values of rect.x and rect.y
        self.rect = self.image.get_rect()

        self.movement_keys = movement_keys

    def update(self, events, delta_time):
        keys = pygame.key.get_pressed()

        l, u, r, d = self.movement_keys

        # Don't set it here just send it
        x_movement = int(keys[r]) - int(keys[l]) 
        y_movement = -(int(keys[u]) - int(keys[d]))

        # send current
        print("sending", convert_player_data_to_str(x_movement, y_movement, delta_time))
        new_pos = self.server.send(convert_player_data_to_str(x_movement, y_movement, delta_time))
        print("new_position", new_pos)
        # set new pos from the server - TODO this code will break when we implement aim stuff
        self.pos = pygame.math.Vector2(convert_pos_str_to_player_pos(new_pos))
        self.rect.center = self.pos



class ServerPlayer():
    # TODO Since this is on the server it doesn't need to use pygame at all to compute this
    # We should really just use the faste way to do it and then get the info back probably numpy
    def __init__(self,start_pos, width, height):
        """
        Initialize a player

        Movement Keys is a set of pygame keys in the following order:
         
        Left Up Right Down (clockwise order)
        """
        self.pos = pygame.math.Vector2(start_pos)
        self.width = width
        self.height = height

        self.movement_vector = pygame.math.Vector2(0,0)

        self.velocity = pygame.math.Vector2(0,0)

        self.max_speed = 4000
        self.acceleration = 2000
        self.friction = 0.05

    def update_movement_vector(self, x: int, y: int) -> None:
        self.movement_vector.x = x
        self.movement_vector.y = y

    def update_position(self, delta_time):
        # NOTE: You should update the movement vector before you update the position

        velocity_change = self.acceleration * delta_time

        if not (self.movement_vector.x == 0 and self.movement_vector.y == 0):
            pygame.math.Vector2.normalize_ip(self.movement_vector)
            self.apply_movement(velocity_change * self.movement_vector)
        else:
            # If no buttons are being pressed then we can apply friction to slow them down
            # We will slow them down at the same speed they would speed up by
            self.apply_friction()

        # Based on our acceleration calculate what the velocity update should be

        # Change in position = velocity * change in time
        self.pos += self.velocity * delta_time
        self.pos.x %= WIDTH
        self.pos.y %= HEIGHT

    
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
