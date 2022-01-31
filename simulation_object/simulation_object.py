from abc import ABC, abstractmethod
import uuid
from network_object.network_object import NetworkObject
import global_simulation


class SimulationObject(ABC):
    def __init__(self) -> None:
        """
        Gives the simulation object a unique id and adds it to the simulation.

        Notes:
            This means that whenever beams, or players are created they are automatically added to the simulation

            uuid can be manually passed in, the use case for this is when you're running a client simulation
            and you want to force a uuid manually from a SimulationStateMessage (aka server output message)
        """
        self.uuid = uuid.uuid1()
        global_simulation.SIMULATION.register_object(self)

    def __repr__(self) -> str:
        return str(self.uuid)

    @abstractmethod
    def to_network_object(self) -> NetworkObject:
        pass

    @abstractmethod
    def step(self, delta_time: float) -> None:
        """
        Simulate a step for the current simulation object
        :return:
        """
        pass
