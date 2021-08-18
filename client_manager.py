import pygame, threading

from typing import List

import chatbox
import game_engine_constants, intersections, map_loading, collisions, helpers, weapons, game_modes, textbox
import commands

from simulation_object.player import ClientPlayer
from network_object.player import PlayerNetworkObject
from network_object.rocket import RocketNetworkObject
from network_object.hitscan_beam import HitscanBeamNetworkObject
from comms import message


class ClientGameManager:
    """A game manager for the client"""

    def __init__(self, screen, font, map_fullname, player_id, player):
        self.id_to_player = {}
        # TODO make this a set eventually
        self.projectiles = []
        self.beam_messages = []
        self.partitioned_map_grid = map_loading.PartitionedMapGrid(
            map_loading.get_pixels(map_fullname), 10, 10
        )

        self.screen = screen
        self.font = font
        self.player = player  # the player controlling this client
        # This takes the messages from the server and changes the clients information,
        # for example it updates all the players positions when a new game state comes in
        # it may be depcricated because i thought I would be sending multiple message types but so far
        # we are only sending one message type
        # TODO REMOVE THIS, just for support now
        self.all_sprites = pygame.sprite.Group()

        self.is_typing = False

        self.user_text_box = textbox.TextInputBox(
            0, 0, game_engine_constants.WIDTH / 3, self.font
        )

        self.user_chat_box = chatbox.ChatBox(
            self.screen,
            game_engine_constants.WIDTH * 0.8,
            0,
            game_engine_constants.WIDTH * 0.2,
            600,
            font,
        )

        self.client_command_runner = commands.ClientCommandRunner(self.player)

        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(player)
        self.id_to_player[player_id] = player

    def draw_projectiles(self, camera_v):
        for projectile_message in self.projectiles:
            radius = (
                game_engine_constants.TILE_SIZE / 4
            )  # TODO use shared variable with server
            pygame.draw.circle(
                self.screen,
                pygame.color.THECOLORS["chartreuse4"],
                projectile_message.position + camera_v,
                radius,
            )

    def draw_beams(self, camera_v):
        for beam_message in self.beam_messages:
            pygame.draw.line(
                self.screen,
                pygame.color.THECOLORS["chartreuse4"],
                beam_message.start_point + camera_v,
                beam_message.end_point + camera_v,
            )

    def parse_input_message(
        self,
        input_message: message.ServerMessage,
    ):
        if type(input_message) == message.SimulationStateMessage:
            self.parse_player_network_message(input_message.players)
            self.projectiles = input_message.rockets
            self.beam_messages.extend(input_message.hitscan_beams)

        elif type(input_message) == message.PlayerTextMessage:
            self.user_chat_box.add_message(
                f"{str(input_message.player_id)[:4]}: {input_message.text}"
            )

        else:
            raise message.UnknownMessageTypeError

    def parse_player_network_message(self, player_states: List[PlayerNetworkObject]):
        """The message in this case is a list of elements of the form

        player_data.player_id|player_data.x|y|player_data.rotation_angle

        """
        for player_state in player_states:
            if player_state.uuid not in self.get_ids():
                # TODO remove the network from a curr_player the game manager will do that
                self.id_to_player[player_state.uuid] = ClientPlayer(
                    player_state.position,
                    50,
                    50,
                    (50, 255, 5),
                    game_engine_constants.ARROW_MOVEMENT_KEYS,
                    game_engine_constants.WEAPON_KEYS,
                    player_state.uuid,
                    None,  # TODO this is also really bad
                    -1,  # TODO this is really bad
                )
                self.all_sprites.add(self.id_to_player[player_state.uuid])
            else:
                curr_player = self.id_to_player[player_state.uuid]
                curr_player.set_position(player_state.position)
                curr_player.rotation_angle = player_state.rotation
                curr_player.camera_v = (
                    game_engine_constants.SCREEN_CENTER_POINT - curr_player.position
                )
                curr_player.update()

    def get_ids(self):
        return list(self.id_to_player.keys())

    def get_players(self):
        return list(self.id_to_player.values())
