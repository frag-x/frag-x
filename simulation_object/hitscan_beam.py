from dataclasses import dataclass
import pygame

import global_simulation
import helpers
import intersections

from network_object.network_object import NetworkObject
from network_object.hitscan_beam import HitscanBeamNetworkObject
from simulation_object.simulation_object import SimulationObject
import weapons.constants
import game_modes  # TODO: This should not be here


class HitscanBeam(SimulationObject):
    """A hitscan beam is a shot from a weapon"""

    def __init__(
        self,
        player,
        start_point: pygame.math.Vector2,
        end_point: pygame.math.Vector2,
        collision_force=weapons.constants.RAILGUN_COLLISION_FORCE,
        damage=weapons.constants.RAILGUN_DAMAGE,
        applies_force_to_player=False,
    ):
        """
        Set up a hitscan beam which is owned by a player
        :param player: The player which owns this beam
        :param start_point: The start point of the beam
        :param end_point: The end point of the beam
        :param collision_force: The amount of force that this beam applies to what it hits
        :param damage: The amount of damage this beam will do to what it hits
        :param applies_force_to_player: If this beam can apply a force to the owner
        """
        super().__init__()

        self.player = player
        self.delta_y = end_point[1] - start_point[1]
        self.delta_x = end_point[0] - start_point[0]

        self.applies_force_to_player = applies_force_to_player

        self.direction_vector = (end_point - start_point).normalize()

        self.start_point = start_point
        self.end_point = end_point

        self.damage = damage

        self.collision_force = collision_force

        self.slope = helpers.get_slope(start_point, end_point)

        self.quadrant_info = (
            helpers.get_sign(self.delta_x),
            helpers.get_sign(self.delta_y),
        )

    def to_network_object(self) -> NetworkObject:
        return HitscanBeamNetworkObject(
            uuid=self.uuid,
            start_point=self.start_point,
            end_point=self.end_point,
        )

    def step(self, delta_time: float):
        (
            closest_hit,
            closest_entity,
        ) = intersections.get_closest_intersecting_object_in_pmg(
            self.player,
            global_simulation.SIMULATION.map,
            self,
            self.applies_force_to_player,
        )

        if closest_hit is not None and closest_entity is not None:
            # TODO this is fucke
            self.end_point = closest_hit
            if (
                hasattr(closest_entity, "uuid")
                and closest_entity.uuid in global_simulation.SIMULATION.players
            ):  # this verifies if what it hit is a player
                hit_player = closest_entity
                if (hit_player is self.player and self.applies_force_to_player) or (
                    hit_player is not self.player
                ):
                    hit_player.velocity += self.direction_vector * self.collision_force

                if hit_player is not self.player:
                    # print(type(global_simulation.SIMULATION.game_mode), game_modes.InstakillGameMode)
                    # if isinstance(global_simulation.SIMULATION.game_mode, game_modes.InstakillGameMode):
                    #     hit_player.health = 0  
                    # else:
                    #     hit_player.health -= self.damage
                    # TODO: Implement this for different game modes (Like above)
                    hit_player.health = 0    
                    if hit_player.health <= 0:
                        hit_player.velocity = pygame.math.Vector2()
                        if hit_player.time_of_death is None:
                            hit_player.time_of_death = pygame.time.get_ticks()
                            self.player.num_frags += 1
                    
        # No need to deregister the object, hitscan beams are removed
        # before new ones are created, but after old ones are operated on
