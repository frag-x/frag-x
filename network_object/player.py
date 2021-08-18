from dataclasses import dataclass
from network_object.network_object import NetworkObject
import pygame

@dataclass
class PlayerNetworkObject(NetworkObject):
    """Represents the server-side state of a client."""

    position: pygame.math.Vector2
    rotation: float
    weapon_selection: int  # TODO: should just be weapon