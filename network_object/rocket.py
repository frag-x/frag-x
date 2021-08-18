from dataclasses import dataclass
from network_object.network_object import NetworkObject
import pygame

@dataclass
class RocketNetworkObject(NetworkObject):
    """Represents the server-side state of a rocket."""

    position: pygame.math.Vector2
