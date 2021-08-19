import pygame, math
import collisions, global_simulation
from comms.message import PlayerStateMessage
import game_engine_constants, body
from map_loading import BoundingWall
from weapons.railgun import RailGun
from weapons.rocket_launcher import RocketLauncher
from simulation_object.simulation_object import SimulationObject
import simulation_object.constants

from comms import network
from network_object.player import PlayerNetworkObject


class Player(body.ConstantAccelerationBody):
    def __init__(self, start_position, width, height, socket):
        pygame.sprite.Sprite.__init__(self)
        self.position = pygame.math.Vector2(start_position)

        super().__init__(
            start_position, game_engine_constants.PLAYER_RADIUS, 0.05, 1000
        )

        # Basic Properties

        self.width = width

        self.aim_length = 100

        self.width = width + 2 * self.aim_length
        self.height = height + 2 * self.aim_length

        self.socket = socket

        # Aiming

        self.rotation_angle = 0
        self.sensitivity = 0.5 * game_engine_constants.SENSITIVITY_SCALE

        # Guns

        self.weapons = [
            # weapons.RocketLauncher(2, self, 1000),
            RocketLauncher(),
            RailGun(),
        ]
        self.weapon_selection = 0

        # Physics/Movement

        # A movement vector drives the player
        self.movement_vector = pygame.math.Vector2(0, 0)

        self.text_message = ""

        self.beams = []

        self.ready = False
        self.map_vote = None

        self.num_frags = 0


class ServerPlayer(SimulationObject, Player):
    def __init__(self, start_pos, width, height, socket):
        """
        Initialize a player

        Movement Keys is a set of pygame keys in the following order:

        Left Up Right Down (clockwise order)
        """
        super().__init__()
        super(SimulationObject, self).__init__(start_pos, width, height, socket)
        self.health = 100
        self.time_of_death = None

        self.movement_request = pygame.math.Vector2(0, 0)
        self.rotation_request = 0
        self.firing_request = False

    def to_network_object(self):
        return PlayerNetworkObject(
            uuid=self.uuid,
            position=self.position,
            rotation=self.rotation_angle,
            weapon_selection=self.weapon_selection,
            num_frags=self.num_frags,
        )

    def update(self, input_message: PlayerStateMessage):
        self.movement_request = pygame.math.Vector2(input_message.delta_position)
        self.rotation_request = input_message.delta_mouse
        self.weapon_selection = input_message.weapon_selection
        self.firing_request = input_message.firing
        self.ready = input_message.ready
        self.map_vote = input_message.map_vote

    def step(self, delta_time: float, current_time: float):  # type: ignore

        global_simulation.SIMULATION.get_partition(self.position).players.append(self)
        global_simulation.SIMULATION.get_collision_partition(
            self.position
        ).players.append(self)

        if self.time_of_death is not None:
            if (
                self.time_of_death - current_time
            ) / 1000 < simulation_object.constants.PLAYER_DEATH_SECONDS:
                return  # still dead
            self.time_of_death = None  # alive again

        super(Player, self).step(self.movement_request, delta_time)
        self.movement_request = pygame.math.Vector2(0, 0)

        self.rotation_angle += self.rotation_request
        self.rotation_angle %= math.tau

        if self.firing_request:
            self.weapons[self.weapon_selection].try_fire(
                self, self.rotation_angle, current_time
            )

        colliding_walls, colliding_players = global_simulation.SIMULATION.get_colliding_elements(
            self, self.collision_partition
        )

        for colliding_wall in colliding_walls:
            # TODO make this a player method
            collisions.simulate_collision_v2(self, colliding_wall)
        for colliding_player in colliding_players:
            collisions.elastic_collision_update(self, colliding_player)


class ClientPlayer(Player, pygame.sprite.Sprite):  # TODO remove dependency on sprite
    """A client player is a representation of a player which only stores enough information to draw
    it to the screen
    """

    def __init__(
        self,
        start_pos,
        width,
        height,
        color,
        movement_keys,
        weapon_keys,
        player_id,
        socket,
        sensitivity,
    ):
        """
        Initialize a player

        Movement Keys is a set of pygame keys in the following order:

        Left Up Right Down (clockwise order)
        """
        super().__init__(start_pos, width, height, socket)
        pygame.sprite.Sprite.__init__(self)

        self.color = color

        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        self.image = pygame.Surface([self.width, self.height], pygame.SRCALPHA, 32)

        self.camera_v = game_engine_constants.SCREEN_CENTER_POINT - self.position
        # Fetch the rectangle object that has the dimensions of the image
        # Update the position of this object by setting the values of rect.x and rect.y
        self.rect = self.image.get_rect()

        self.movement_keys = movement_keys
        self.weapon_keys = weapon_keys

        self.sensitivity = sensitivity * game_engine_constants.SENSITIVITY_SCALE

        self.player_id = player_id

    def set_position(self, position):
        """Set the players position and also fixes the camera to stay centered on the player"""
        self.position = position
        self.rect.center = (
            self.position
        )  # update the image to be at the correct location

    def update(self):
        self.image.fill((255, 255, 255, 0))

        center_point = (self.width / 2, self.height / 2)
        pygame.draw.line(
            self.image,
            pygame.color.THECOLORS["orange"],
            center_point,
            (
                center_point[0] + math.cos(self.rotation_angle) * self.aim_length,
                center_point[1] + math.sin(self.rotation_angle) * self.aim_length,
            ),
        )

        pygame.draw.circle(
            self.image, pygame.color.THECOLORS["blue"], center_point, self.radius
        )
