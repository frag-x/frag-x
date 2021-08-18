from dataclasses import dataclass
from uuid import UUID

@dataclass
class NetworkObject:
    """
    A NetworkObject is a minimal set of information for an object, it will be sent from the server to the client
    """
    uuid: UUID

