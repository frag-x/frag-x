from enum import Enum
import typing

# TODO don't use the values but rather just use the enum itself?

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
class Message:
    """A message is information that gets sent across a network"""
    def __init__(self, message_type):
        self.message_type = message_type

class InputMessage(Message):
    def __init__(self, player_id, net_x_movement, net_y_movement, mouse_movement, time_since_last_client_frame, firing, weapon_request):
        super().__init__(ServerMessageType.PLAYER_INPUTS.value)
        self.player_id = player_id
        self.net_x_movement = net_x_movement
        self.net_y_movement = net_y_movement
        self.mouse_movement = mouse_movement
        self.time_since_last_client_frame = time_since_last_client_frame
        self.firing = firing
        self.weapon_request = weapon_request

class PositionMessage(Message):
    def __init__(self, message_type, x, y):
        super().__init__(message_type)
        self.x = x
        self.y = y

class PlayerPositionMessage(PositionMessage):
    def __init__(self, player):
        super().__init__(ClientMessageType.PLAYER_POSITIONS.value, player.pos.x, player.pos.y)
        self.player_id = player.player_id
        self.rotation_angle = player.rotation_angle 


class ProjectilePositionMessage(PositionMessage):
    def __init__(self, x, y):
        super().__init__(ClientMessageType.PROJECTILE_POSITIONS.value, x, y)

class GameStateMessage(Message):
    def __init__(self, player_position_messages: typing.List[PlayerPositionMessage], projectile_position_messages: typing.List[ProjectilePositionMessage]):
        super().__init__(ClientMessageType.GAME_STATE_MESSAGE.value)
        self.player_position_messages = player_position_messages
        self.projectile_position_messages = projectile_position_messages

