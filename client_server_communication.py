from enum import Enum, auto

class ServerMessageType(Enum):
    """A message received by the server"""
    PLAYER_INPUTS = 0
    TEXT_MESSAGE = 1

class ClientMessageType(Enum):
    """A message received by the client"""
    PLAYER_POSITIONS = 0
    HITSCAN_SHOT = 1
    PROJECTILE_POSITIONS = 2
    TEXT_MESSAGE = 3

class PlayerPositionMessage:
    pass
    #def __init__(self, 



