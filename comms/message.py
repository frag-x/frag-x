from dataclasses import dataclass, field
from typing import List, Tuple

from weapons import Weapon

@dataclass
class Message:
    pass

@dataclass
class ClientMessage(Message):
    pass

@dataclass
class ServerMessage(Message):
    pass

@dataclass
class PlayerStateMessage(ClientMessage):
    """Represents client state sent to server."""
    player_id: str
    delta_x: float
    delta_y: float
    delta_mouse: float
    firing: bool
    weapon_selection: int # TODO: should just be weapon
    delta_time: float

@dataclass
class PlayerTextMessage(ClientMessage):
    """Represents client text messages sent to server."""
    player_id: str
    text: str

@dataclass
class ServerJoinMessage(ServerMessage):
    player_id: str

@dataclass
class PlayerState:
    """Represents the server-side state of a client."""
    player_id: str
    x: float
    y: float
    rotation: float
    weapon_selection: int # TODO: should just be weapon

@dataclass
class ProjectileState:
    """Represents the server-side state of a projectile."""
    x: float
    y: float

@dataclass
class BeamState:
    """Represents the server-side state of a beam."""
    start_x: float
    start_y: float
    end_x: float
    end_y: float

@dataclass
class ServerStateMessage(ServerMessage):
    """Represents server state sent to a client."""
    player_states: list[PlayerStateMessage] = field(default_factory=list)
    projectiles: list[ProjectileState] = field(default_factory=list)
    beams: list[BeamState] = field(default_factory=list)
