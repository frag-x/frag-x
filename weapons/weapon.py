from abc import ABC, abstractmethod
from typing import List

import pygame.math

import math

from weapons import helpers
from simulation_object.hitscan_beam import HitscanBeam


class Weapon(ABC):
    def __init__(self, fire_rate_hz: float):
        """
        :param fire_rate_hz: the rate at which the weapon may be fired
        """
        self.fire_rate_hz = fire_rate_hz
        self.seconds_per_shot = 1 / self.fire_rate_hz
        # Initialize to a value where they can shoot immediatly
        self.time_of_last_shot: float = 0

    @abstractmethod
    def fire(self, firing_player, aim_angle: float):
        pass

    def try_fire(self, firing_player, aim_angle: float, current_time: float):
        if (current_time - self.time_of_last_shot) / 1000 >= self.seconds_per_shot:
            self.fire(firing_player, aim_angle)
            self.time_of_last_shot = current_time


class HitscanWeapon(Weapon, ABC):
    """
    A hitscan weapon is a weapon that fires instantly
    """

    def __init__(self, fire_rate: float, damage: int):
        """
        Set up a hitscan weapon

        :param damage: the amount of damage that a successful hit will do
        """
        super().__init__(fire_rate_hz=fire_rate)
        self.damage = damage

    @abstractmethod
    def fire(
        self, firing_player, aim_angle: float
    ) -> List[HitscanBeam]:
        """
        :param firing_position: the position that the weapon is fired at
        :param aim_angle: the angle that the weapon is fired at
        :return: List[HitscanBeam]
        """
        pass
