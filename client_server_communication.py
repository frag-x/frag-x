from enum import Enum
import typing

# TODO don't use the values but rather just use the enum itself?

# A message represents the minimal amount of information required to send across the network to make client and server function correctly


class ServerMessageType(Enum):
    """A message received by the server"""

    PLAYER_INPUTS = 0
    TEXT_MESSAGE = 1


class ClientMessageType(Enum):
    """A message received by the client"""

    # TODO this is going to become more high level and we will have types per game mode
    # rather than at the atomic level like this
    GAME_STATE_MESSAGE = 0
    PLAYER_POSITIONS = 1
    HITSCAN_SHOT = 2
    PROJECTILE_POSITIONS = 3
    TEXT_MESSAGE = 4


# TODO make all of these dataclasses?
class NetworkMessage:
    """A message is information that gets sent across a network"""

    def __init__(self, message_type):
        self.message_type = message_type


class InputNetworkMessage(NetworkMessage):
    def __init__(
        self,
        player_id,
        net_x_movement,
        net_y_movement,
        mouse_movement,
        time_since_last_client_frame,
        firing,
        weapon_request,
        text_message="",
    ):
        super().__init__(ServerMessageType.PLAYER_INPUTS.value)
        self.player_id = player_id
        self.net_x_movement = net_x_movement
        self.net_y_movement = net_y_movement
        self.mouse_movement = mouse_movement
        self.time_since_last_client_frame = time_since_last_client_frame
        self.firing = firing
        self.weapon_request = weapon_request
        self.text_message = text_message


class PositionNetworkMessage(NetworkMessage):
    def __init__(self, message_type, x, y):
        super().__init__(message_type)
        self.x = x
        self.y = y


class PlayerNetworkMessage(PositionNetworkMessage):
    """Represents the minimal amount of information needed for a client to draw"""

    def __init__(self, player):
        super().__init__(
            ClientMessageType.PLAYER_POSITIONS.value, player.pos.x, player.pos.y
        )
        self.player_id = player.player_id
        self.rotation_angle = player.rotation_angle
        self.text_message = player.text_message


class ProjectilePositionMessage(PositionNetworkMessage):
    def __init__(self, x, y):
        super().__init__(ClientMessageType.PROJECTILE_POSITIONS.value, x, y)


class BeamMessage:
    def __init__(self, start_point, end_point):
        self.start_point = start_point
        self.end_point = end_point


class GameStateNetworkMessage(NetworkMessage):
    def __init__(
        self,
        player_position_messages: typing.List[PlayerNetworkMessage],
        projectile_position_messages: typing.List[ProjectilePositionMessage],
        beam_messages: typing.List[BeamMessage],
    ):
        super().__init__(ClientMessageType.GAME_STATE_MESSAGE.value)
        self.player_position_messages = player_position_messages
        self.projectile_position_messages = projectile_position_messages
        self.beam_messages = beam_messages
