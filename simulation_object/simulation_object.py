from abc import ABC, abstractmethod
import uuid

from comms import message
from comms.message import ClientMessage
from network_object.network_object import NetworkObject
import global_simulation


class SimulationObject(ABC):
    def __init__(self):
        """
        Gives the simulation object a unique id and adds it to the simulation.

        Note: This means that whenever beams, or players are created they are automatically added to the simulation
        """
        self.uuid = uuid.uuid1()
        global_simulation.SIMULATION.register_object(self)

    def __repr__(self):
        return str(self.uuid)

    @abstractmethod
    def to_network_object(self) -> NetworkObject:
        pass

    @abstractmethod
    def step(self, delta_time: float, current_time: float):
        """
        Simulate a step for the current simulation object
        :return:
        """
        pass
