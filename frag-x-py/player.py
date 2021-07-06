import pygame
import math
from game_engine_constants import WIDTH, HEIGHT
from converters import player_data_to_str


def magnitude(v):
  return math.sqrt(v.x ** 2 + v.y ** 2)

class BasePlayer:
    def __init__(self,start_pos, width, height,player_id, socket):
        pygame.sprite.Sprite.__init__(self)
        self.pos = pygame.math.Vector2(start_pos)


        # Basic Properties

        self.width = width
        self.height = height
        self.player_id = player_id

        self.socket = socket

        # Aiming

        self.rotation_angle = 0
        self.sensitivity = 0.011

        # Physics/Movement

        self.movement_vector = pygame.math.Vector2(0,0)

        self.velocity = pygame.math.Vector2(0,0)

        self.max_speed = 4000
        self.acceleration = 2000
        self.friction = 0.05


class ClientPlayer(pygame.sprite.Sprite):
    """A client player is a representation of a player which only stores enough information to draw
    it to the screen
    """

    def __init__(self,start_pos, width, height,color, movement_keys, s_width, s_height, player_id, server):
        """
        Initialize a player

        Movement Keys is a set of pygame keys in the following order:
         
        Left Up Right Down (clockwise order)
        """
        pygame.sprite.Sprite.__init__(self)
        self.pos = pygame.math.Vector2(start_pos)

        self.rotation_angle = 0
        self.sensitivity = 0.011

        self.aim_length = 100

        self.s_width= s_width
        self.s_height = s_height
        self.width = width + 2*self.aim_length
        self.height = height + 2*self.aim_length
        self.player_id = player_id
        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        self.image = pygame.Surface([self.width, self.height], pygame.SRCALPHA, 32)
        #self.image = self.image.convert_alpha()
        #self.image.fill(color)
        #pygame.draw.circle(self.image, (self.width/2, self.height/2), color, self.width)
        self.color = color
        self.server = server

        self.rotation_angle = 0

        # Fetch the rectangle object that has the dimensions of the image
        # Update the position of this object by setting the values of rect.x and rect.y
        self.rect = self.image.get_rect()

        self.movement_keys = movement_keys


    def set_pos(self, x,y):
        self.pos = pygame.math.Vector2((x,y))

    def send_inputs(self, events, delta_time):

        # we only look at the x component of mouse input
        dm, _ = pygame.mouse.get_rel()

        keys = pygame.key.get_pressed()

        l, u, r, d = self.movement_keys
        x_movement = int(keys[r]) - int(keys[l]) 
        y_movement = -(int(keys[u]) - int(keys[d]))

        inputs = (self.player_id, x_movement, y_movement, dm, delta_time)
        
        print(player_data_to_str(inputs))

        self.server.send(player_data_to_str(inputs))

    def update(self, events, delta_time):

        self.image.fill((255,255,255, 0))

        center_point = (self.width/2, self.height/2)
        pygame.draw.line(self.image, pygame.color.THECOLORS['blue'], center_point, (center_point[0] + math.cos(self.rotation_angle)* self.aim_length, center_point[1] + math.sin(self.rotation_angle) * self.aim_length))

        pygame.draw.circle(self.image, self.color, center_point, 50)
        self.rect.center = self.pos



class ServerPlayer(BasePlayer):
    # TODO Since this is on the server it doesn't need to use pygame at all to compute this
    # We should really just use the faste way to do it and then get the info back probably numpy
    def __init__(self,start_pos, width, height, player_id, socket):
        """
        Initialize a player

        Movement Keys is a set of pygame keys in the following order:
         
        Left Up Right Down (clockwise order)
        """
        super().__init__(start_pos, width, height,player_id, socket)

    def update_aim(self, dm):
      self.rotation_angle += dm * self.sensitivity

    def update_position(self, dx, dy, delta_time):
        # NOTE: You should update the movement vector before you update the position
        self.movement_vector.x = dx
        self.movement_vector.y = dy

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

    def get_sendable_state(self):
        properties = [self.player_id, self.pos.x, self.pos.y, self.rotation_angle]
        str_properties = [str(x) for x in properties]
        return '|'.join(str_properties)
    
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