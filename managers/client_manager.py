import pygame, threading

from typing import List

import chatbox
import game_engine_constants, dev_constants, player, intersections, map_loading, collisions, helpers, weapons, game_modes, textbox
import commands

from managers.manager import GameManager
from comms import message


class ClientGameManager(GameManager):
    """A game manager which may be instantiated for the server or the client"""

    def __init__(self, screen, font, map_name, player_id, player, network):
        super().__init__(map_name)
        self.screen = screen
        self.font = font
        self.player = player  # the player controlling this client
        # This takes the messages from the server and changes the clients information,
        # for example it updates all the players positions when a new game state comes in
        # it may be depcricated because i thought I would be sending multiple message types but so far
        # we are only sending one message type
        self.player_data_lock = threading.Lock()
        self.network = network
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
            pos = pygame.math.Vector2(projectile_message.x, projectile_message.y)
            radius = (
                game_engine_constants.TILE_SIZE / 4
            )  # TODO use shared variable with server
            pygame.draw.circle(
                self.screen,
                pygame.color.THECOLORS["chartreuse4"],
                pos + camera_v,
                radius,
            )

    def draw_beams(self, camera_v):
        for beam_message in self.beam_messages:
            pygame.draw.line(
                self.screen,
                pygame.color.THECOLORS["chartreuse4"],
                (beam_message.start_x, beam_message.start_y) + camera_v,
                (beam_message.end_x, beam_message.end_y) + camera_v,
            )

    def parse_input_message(
        self,
        input_message: message.ServerMessage,
    ):
        if type(input_message) == message.ServerStateMessage:
            self.parse_player_network_message(input_message.player_states)
            self.projectiles = input_message.projectile_states
            self.beam_messages.extend(input_message.beam_states)
        else:
            raise "unknown message"

    def parse_player_network_message(self, player_states: List[message.PlayerState]):
        """The message in this case is a list of elements of the form

        player_data.player_id|player_data.x|y|player_data.rotation_angle

        """
        for player_state in player_states:
            if player_state.player_id not in self.get_ids():
                # TODO remove the network from a curr_player the game manager will do that
                self.id_to_player[player_state.player_id] = player.ClientPlayer(
                    (player_state.x, player_state.y),
                    50,
                    50,
                    (50, 255, 5),
                    game_engine_constants.ARROW_MOVEMENT_KEYS,
                    game_engine_constants.WEAPON_KEYS,
                    player_state.player_id,
                    None,  # TODO this is also really bad
                    -1,  # TODO this is really bad
                )
                self.all_sprites.add(self.id_to_player[player_state.player_id])
            else:
                # this needs to be locked because if we are doing collisions or hitscan which depends on the position of the player then we can have issues where their position is updated after translating a point with respect to it's original position and then there are no valid
                self.player_data_lock.acquire()
                curr_player = self.id_to_player[player_state.player_id]
                curr_player.set_pos(player_state.x, player_state.y)
                # In real life we can't change their view or they will freak - do it for now
                curr_player.rotation_angle = player_state.rotation
                curr_player.camera_v = (
                    game_engine_constants.SCREEN_CENTER_POINT - curr_player.pos
                )
                curr_player.update()
                self.player_data_lock.release()
