import pygame
import math
import weapons, converters, game_engine_constants, client_server_communication, dev_constants, body


def magnitude(v):
    return math.sqrt(v.x ** 2 + v.y ** 2)


# class Body: position, velocity, mass, etc...


class BasePlayer(body.ConstantAccelerationBody):
    def __init__(self, start_pos, width, height, player_id, socket):
        pygame.sprite.Sprite.__init__(self)
        self.pos = pygame.math.Vector2(start_pos)

        super().__init__(start_pos, game_engine_constants.PLAYER_RADIUS, 0.05, 1000)

        # Basic Properties

        self.width = width

        self.aim_length = 100

        self.width = width + 2 * self.aim_length
        self.height = height + 2 * self.aim_length
        self.player_id = player_id

        self.player_id = player_id

        self.socket = socket

        # Aiming

        self.rotation_angle = 0
        self.sensitivity_scale = 1 / 1000
        self.sensitivity = 0.5 * self.sensitivity_scale

        # Guns

        # self.weapon = weapons.Hitscan(1, self, 1000)
        self.weapons = [
            weapons.RocketLauncher(2, self, 1000),
            weapons.Hitscan(1, self, 1000),
        ]
        self.weapon = self.weapons[0]  # TODO rename to active weapon

        # Physics/Movement

        # A movement vector drives the player
        self.movement_vector = pygame.math.Vector2(0, 0)


class ClientPlayer(
    BasePlayer, pygame.sprite.Sprite
):  # TODO remove dependency on sprite
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
        server,
    ):
        """
        Initialize a player

        Movement Keys is a set of pygame keys in the following order:

        Left Up Right Down (clockwise order)
        """
        super().__init__(start_pos, width, height, player_id, server)
        pygame.sprite.Sprite.__init__(self)

        self.color = color

        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        print(self.width, self.height)
        self.image = pygame.Surface([self.width, self.height], pygame.SRCALPHA, 32)

        self.camera_v = game_engine_constants.SCREEN_CENTER_POINT - self.pos
        # Fetch the rectangle object that has the dimensions of the image
        # Update the position of this object by setting the values of rect.x and rect.y
        self.rect = self.image.get_rect()

        self.movement_keys = movement_keys
        self.weapon_keys = weapon_keys

    def set_sens(self, new_sens):
        self.sensitivity = new_sens * self.sensitivity_scale

    def set_pos(self, x, y):
        """Set the players position and also fixes the camera to stay centered on the player"""
        self.pos = pygame.math.Vector2((x, y))
        self.rect.center = self.pos  # update the image to be at the correct location
        # self.camera_v = game_engine_constants.SCREEN_CENTER_POINT - self.pos

    def send_inputs(self, events, delta_time, typing):

        # we only look at the x component of mouse input
        dm, _ = pygame.mouse.get_rel()
        dm *= self.sensitivity

        keys = pygame.key.get_pressed()

        if typing:
            x_movement = 0
            y_movement = 0
        else:
            # If the player isn't typing then sample their input devices for gameplay
            l, u, r, d = self.movement_keys
            x_movement = int(keys[r]) - int(keys[l])
            y_movement = -(int(keys[u]) - int(keys[d]))

        weapon_choice = -1
        for key in self.weapon_keys:
            if keys[key]:
                if key == pygame.K_c:
                    weapon_choice = 0
                elif key == pygame.K_x:
                    weapon_choice = 1

        firing = int(pygame.mouse.get_pressed()[0])

        inputs = (
            self.player_id,
            x_movement,
            y_movement,
            dm,
            delta_time,
            firing,
            weapon_choice,
        )

        # instead of a string use a custom class designed for this...
        message = (
            str(client_server_communication.ServerMessageType.PLAYER_INPUTS.value)
            + "|"
            + converters.player_data_to_str(inputs)
        )

        if dev_constants.DEBUGGING_NETWORK_MESSAGES:
            print(f"SENDING: {message}")

        if game_engine_constants.CLIENT_GAME_SIMULATION:
            player_data = "|".join(message.split("|")[1:])
            game_engine_constants.MOCK_SERVER_QUEUE.put(
                converters.str_to_player_data(player_data)
            )

        self.socket.send(message)

    def update(self, events=None, delta_time=0):

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


class ServerPlayer(BasePlayer):
    # TODO Since this is on the server it doesn't need to use pygame at all to compute this
    # We should really just use the faste way to do it and then get the info back probably numpy
    def __init__(self, start_pos, width, height, player_id, socket):
        """
        Initialize a player

        Movement Keys is a set of pygame keys in the following order:

        Left Up Right Down (clockwise order)
        """
        super().__init__(start_pos, width, height, player_id, socket)

    def update_aim(self, dm):
        # TODO instead of this we should have sensitivity be client side
        # self.rotation_angle = (self.rotation_angle + (dm * self.sensitivity)) % math.tau
        self.rotation_angle = (self.rotation_angle + dm) % math.tau

    def update_position(self, dx, dy, delta_time):

        # Save the previous position for collisions
        self.previous_pos = pygame.math.Vector2(self.pos.x, self.pos.y)

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

    def get_sendable_state(self):
        properties = [self.player_id, self.pos.x, self.pos.y, self.rotation_angle]
        str_properties = [str(x) for x in properties]
        return "|".join(str_properties)

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
            self.velocity = self.velocity.normalize() * self.max_speed


class KillableServerPlayer(ServerPlayer):
    def __init__(self, start_pos, width, height, player_id, socket):
        super().__init__(start_pos, width, height, player_id, socket)
        self.health = 100
        self.num_frags = 0  # A killable player can also kill others (TODO what about weird game modes)
        self.dead = False
        self.time_dead = 0
