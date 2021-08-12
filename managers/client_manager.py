import pygame, threading

import chatbox
import client_server_communication, network, game_engine_constants, dev_constants, player, intersections, map_loading, collisions, helpers, weapons, game_modes, textbox
import commands
from managers.manager import GameManager


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
        self.client_message_parser = ClientMessageParser(
            self
        )  # TODO maybe change naming to not confuse?
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

        # TODO make a perform all client_operations

    def set_player_positions(self):
        pass

    def set_projectile_positions(self):
        pass

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
                beam_message.start_point + camera_v,
                beam_message.end_point + camera_v,
            )

    def consume_message(self, message):
        pass

    def send_message(self, message):
        # TODO replace the send_inputs with this function as it solves it more generally
        pass


class MessageParser:
    def __init__(self, message_type_to_command, client_game_manager):
        self.message_type_to_command = message_type_to_command
        self.client_game_manager = client_game_manager

    def run_command_from_message(self, message):
        # This is the command pattern
        # print(f"got {message_list} and about to run {self.message_type_to_command[message_list[0].message_type]}")

        self.message_type_to_command[message.message_type](
            message, self.client_game_manager
        )


class ClientMessageParser(MessageParser):
    def __init__(self, client_game_manager):
        super().__init__(message_type_to_command_client, client_game_manager)


def parse_player_network_message(message_list, client_game_manager):
    """The message in this case is a list of elements of the form

    player_data.player_id|player_data.x|y|player_data.rotation_angle

    """
    for player_data in message_list:
        if player_data.player_id not in client_game_manager.get_ids():
            # TODO remove the network from a curr_player the game manager will do that
            client_game_manager.id_to_player[
                player_data.player_id
            ] = player.ClientPlayer(
                (player_data.x, player_data.y),
                50,
                50,
                (50, 255, 5),
                game_engine_constants.ARROW_MOVEMENT_KEYS,
                game_engine_constants.WEAPON_KEYS,
                player_data.player_id,
                client_game_manager.network,
                -1, # TODO this is really bad
            )
            client_game_manager.all_sprites.add(
                client_game_manager.id_to_player[player_data.player_id]
            )
        else:
            # this needs to be locked because if we are doing collisions or hitscan which depends on the position of the player then we can have issues where their position is updated after translating a point with respect to it's original position and then there are no valid
            client_game_manager.player_data_lock.acquire()
            curr_player = client_game_manager.id_to_player[player_data.player_id]
            curr_player.set_pos(player_data.x, player_data.y)
            # In real life we can't change their view or they will freak - do it for now
            curr_player.rotation_angle = player_data.rotation_angle
            curr_player.camera_v = (
                game_engine_constants.SCREEN_CENTER_POINT - curr_player.pos
            )
            curr_player.update()
            if player_data.text_message != "":
                print(player_data.text_message)
                client_game_manager.user_chat_box.add_message(player_data.text_message)

            client_game_manager.player_data_lock.release()


def parse_game_state_message(
    game_state_message: client_server_communication.GameStateNetworkMessage,
    client_game_manager: ClientGameManager,
):
    parse_player_network_message(
        game_state_message.player_network_messages, client_game_manager
    )
    parse_projectile_position_message(
        game_state_message.projectile_position_messages, client_game_manager
    )
    parse_beam_messages(game_state_message.beam_messages, client_game_manager)


def parse_projectile_position_message(message_list, client_game_manager):
    client_game_manager.projectiles = message_list


def parse_beam_messages(message_list, client_game_manager):
    client_game_manager.beam_messages.extend(message_list)


message_type_to_command_client = {
    client_server_communication.ClientMessageType.GAME_STATE_MESSAGE.value: parse_game_state_message
}
