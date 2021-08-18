from dataclasses import dataclass, field

import pygame
from network_object.player import PlayerNetworkObject
from network_object.rocket import RocketNetworkObject
from network_object.hitscan_beam import HitscanBeamNetworkObject


class UnknownMessageTypeError(NotImplementedError):
    pass


@dataclass
class Message:
    pass


@dataclass
class ClientMessage(Message):
    pass


@dataclass
class ServerMessage(Message):
    """
    A server message is a minimal set of information for a client to draw the game.

    It's composed of a set of NetworkObjects
    """

    pass


@dataclass
class PlayerStateMessage(ClientMessage):
    """Represents client state sent to server."""

    player_id: str
    delta_position: pygame.math.Vector2
    delta_mouse: float
    firing: bool
    weapon_selection: int  # TODO: should just be weapon
    ready: bool
    map_vote: str


@dataclass
class PlayerTextMessage(ClientMessage):
    """Represents client text messages sent to server."""

    player_id: str
    text: str


@dataclass
class ServerJoinMessage(ServerMessage):
    player_id: str


@dataclass
class ServerStatusMessage(ServerMessage):
    status: str


@dataclass
class SimulationStateMessage(ServerMessage):
    """Represents simulation state sent to a client."""

    players: list[PlayerNetworkObject] = field(default_factory=list)
    rockets: list[RocketNetworkObject] = field(default_factory=list)
    hitscan_beams: list[HitscanBeamNetworkObject] = field(default_factory=list)

