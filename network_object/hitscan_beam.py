from dataclasses import dataclass
from network_object.network_object import NetworkObject

import pygame


@dataclass
class HitscanBeamNetworkObject(NetworkObject):
    """Represents the server-side state of a beam."""

    start_point: pygame.math.Vector2
    end_point: pygame.math.Vector2
