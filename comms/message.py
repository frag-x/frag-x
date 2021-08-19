from dataclasses import dataclass, field
from typing import Dict
from uuid import UUID

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

    player_id: UUID
    delta_position: pygame.math.Vector2
    delta_mouse: float
    firing: bool
    weapon_selection: int
    ready: bool
    map_vote: str


@dataclass
class PlayerTextMessage(ClientMessage):
    """Represents client text messages sent to server."""

    player_id: UUID
    text: str


@dataclass
class ServerJoinMessage(ServerMessage):
    player_id: UUID
    map_name: str


@dataclass
class ServerStatusMessage(ServerMessage):
    status: str


@dataclass
class ServerMapChangeMessage(ServerMessage):
    map_name: str


@dataclass
class SimulationStateMessage(ServerMessage):
    """Represents simulation state sent to a client."""

    players: Dict[UUID, PlayerNetworkObject] = field(default_factory=dict)
    rockets: Dict[UUID, RocketNetworkObject] = field(default_factory=dict)
    hitscan_beams: Dict[UUID, HitscanBeamNetworkObject] = field(default_factory=dict)
