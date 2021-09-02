from network_object.player import PlayerNetworkObject
import pygame
import game_engine_constants
from textbox import TextInputBox
from leaderboard import Leaderboard
import commands
from comms.message import (
    PlayerStateMessage,
    PlayerTextMessage,
    ServerJoinMessage,
    ServerMessage,
    SimulationStateMessage,
    ServerMapChangeMessage,
    ServerStatusMessage,
    UnknownMessageTypeError,
)
from comms import network
import socket
import map_loading
import math
from chatbox import ChatBox
from typing import Optional, cast
import simulation_object.constants


class ClientInstance:
    def __init__(
        self,
        socket: socket.socket,
        server_join_message: ServerJoinMessage,
        fullscreen: bool,
        frame_rate: int,
        sensitivity: float,
    ):
        self._setup_pygame(fullscreen)

        self.socket = socket
        self.player_id = server_join_message.player_id
        self.map_name = server_join_message.map_name
        self.frame_rate = frame_rate
        self.set_sensitivity(sensitivity)

        self.running = True
        self.user_typing = False
        # TODO the way UI elements work and especially text input box is messed af
        self.user_text_box = TextInputBox(
            0, 0, game_engine_constants.WIDTH / 3, self.font
        )
        self.user_chat_box = ChatBox(
            self.screen,
            game_engine_constants.WIDTH * 2 / 3,
            0,
            game_engine_constants.WIDTH * 0.2,
            game_engine_constants.HEIGHT * 0.9,
            self.font,
        )
        self.leaderboard = Leaderboard(
            self.screen,
            0,
            0,
            100,
            100,
            self.font,
        )
        self.command_runner = commands.CommandRunner(self)

        self.ready = False
        self.map_vote: Optional[str] = None

        self.simulation_state: Optional[SimulationStateMessage] = None

        self.map = map_loading.load_map(self.map_name)

        self.rotation: float = 0

    def _setup_pygame(self, fullscreen: bool) -> None:
        pygame.init()
        pygame.mixer.init()  # sound
        pygame.font.init()

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), 30)

        if fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            (
                game_engine_constants.WIDTH,
                game_engine_constants.HEIGHT,
            ) = pygame.display.get_surface().get_size()
            # TODO don't do this, overriding constants is an antipattern
            game_engine_constants.SCREEN_CENTER_POINT = pygame.math.Vector2(
                game_engine_constants.WIDTH / 2,
                game_engine_constants.HEIGHT / 2,
            )
        else:
            self.screen = pygame.display.set_mode(
                (game_engine_constants.WIDTH, game_engine_constants.HEIGHT)
            )

        pygame.display.set_caption(game_engine_constants.GAME_TITLE)

        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

    def set_sensitivity(self, sensitivity: float) -> None:
        self.sensitivity = sensitivity * game_engine_constants.SENSITIVITY_SCALE

    def quit(self):
        self.running = False

    def _this_player(self) -> PlayerNetworkObject:
        return cast(SimulationStateMessage, self.simulation_state).players[self.player_id]

    def _process_pygame_events(self) -> None:
        events = pygame.event.get()
        for i, event in enumerate(events):
            if event.type == pygame.QUIT:
                self.quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t and not self.user_typing:
                    self.user_typing = True
                    # Only register key presses after user typing is active
                    events = events[i + 1 :]
                elif event.key == pygame.K_RETURN and self.user_typing:
                    self.user_typing = False
                    # TODO make user_text_box smarter by adding a method
                    text = self.user_text_box.text
                    self.user_text_box.text = ""

                    if commands.is_command(text):
                        self.command_runner.try_command(text)
                    else:
                        text_message = PlayerTextMessage(
                            player_id=self.player_id, text=text
                        )
                        network.send(self.socket, text_message)

                elif event.key == pygame.K_ESCAPE and self.user_typing:
                    self.user_typing = False
                    self.user_text_box.text = ""

        if self.user_typing:
            self.user_text_box.update(events)

    def send_inputs(self):
        # we only look at the x component of mouse input
        delta_mouse, _ = pygame.mouse.get_rel()
        delta_mouse *= self.sensitivity

        self.rotation += delta_mouse
        self.rotation %= math.tau

        keys = pygame.key.get_pressed()

        if self.user_typing:
            x_movement = 0
            y_movement = 0
        else:
            # If the player isn't typing then sample their input devices for gameplay
            l, u, r, d = game_engine_constants.WASD_MOVEMENT_KEYS
            x_movement = int(keys[r]) - int(keys[l])
            y_movement = -(int(keys[u]) - int(keys[d]))

        for i, key in enumerate(game_engine_constants.WEAPON_KEYS):
            if keys[key]:
                self._this_player().weapon_selection = i

        firing = pygame.mouse.get_pressed()[0]

        output_message = PlayerStateMessage(
            player_id=self.player_id,
            delta_position=pygame.math.Vector2(x_movement, y_movement),
            rotation=self.rotation,
            firing=firing,
            weapon_selection=self._this_player().weapon_selection,
            ready=self.ready,
            map_vote=self.map_vote,
        )

        network.send(self.socket, output_message)

    def process_input_message(self, input_message: ServerMessage):
        if type(input_message) == SimulationStateMessage:
            self.simulation_state = input_message
            if self.player_id in self.simulation_state.players:
                self._this_player().rotation = self.rotation

        elif type(input_message) == PlayerTextMessage:
            self.user_chat_box.add_message(
                f"{str(input_message.player_id)[:4]}: {input_message.text}"
            )

        elif type(input_message) == ServerStatusMessage:
            self.user_chat_box.add_message(f"Server status {input_message.status}")

        elif type(input_message) == ServerMapChangeMessage:
            self.map_name = input_message.map_name
            self.map = map_loading.load_map(self.map_name)
            self.ready = False
            self.map_vote = None
            self.user_chat_box.add_message(f"Map changed to {input_message.map_name}")

        else:
            raise UnknownMessageTypeError

    def _update(self) -> None:
        self._process_pygame_events()
        self.send_inputs()

    def _camera_view(self) -> pygame.math.Vector2:
        our_position = cast(SimulationStateMessage, self.simulation_state).players[self.player_id].position
        return game_engine_constants.SCREEN_CENTER_POINT - our_position

    def _draw_players(self):
        for player in self.simulation_state.players.values():
            player_relative_position = player.position + self._camera_view()

            pygame.draw.line(
                self.screen,
                pygame.color.THECOLORS["orange"],
                player_relative_position,
                (
                    player_relative_position[0]
                    + math.cos(player.rotation)
                    * simulation_object.constants.PLAYER_AIM_LENGTH,
                    player_relative_position[1]
                    + math.sin(player.rotation)
                    * simulation_object.constants.PLAYER_AIM_LENGTH,
                ),
            )

            pygame.draw.circle(
                self.screen,
                player.color if player.health > 0 else simulation_object.constants.PLAYER_DEATH_COLOR,
                player_relative_position,
                game_engine_constants.PLAYER_RADIUS,
            )

    def _draw_rockets(self):
        for projectile in self.simulation_state.rockets.values():
            # TODO use shared variable with server
            radius = game_engine_constants.TILE_SIZE / 4
            pygame.draw.circle(
                self.screen,
                pygame.color.THECOLORS["chartreuse4"],
                projectile.position + self._camera_view(),
                radius,
            )

    def _draw_hitscan_beams(self):
        for hitscan_beam in self.simulation_state.hitscan_beams.values():
            pygame.draw.line(
                self.screen,
                pygame.color.THECOLORS["chartreuse4"],
                hitscan_beam.start_point + self._camera_view(),
                hitscan_beam.end_point + self._camera_view(),
            )

    def _render(self, delta_time: float) -> None:
        self.screen.fill(pygame.color.THECOLORS["black"])  # type: ignore

        for row in self.map.partitioned_map:
            for partition in row:
                for wall in partition.walls:
                    pygame.draw.rect(
                        self.screen, wall.color, wall.rect.move(self._camera_view())
                    )

                for b_wall in partition.bounding_walls:
                    pygame.draw.rect(
                        self.screen, b_wall.color, b_wall.rect.move(self._camera_view())
                    )

        self._draw_players()
        self._draw_rockets()
        self._draw_hitscan_beams()
        self.leaderboard.render(self.player_id, list(cast(SimulationStateMessage, self.simulation_state).players.values()))

        self.user_chat_box.update_message_times(delta_time)
        self.user_chat_box.draw_messages()

        self.user_text_box.render_text()
        utb_width, utb_height = self.user_text_box.image.get_size()

        self.screen.blit(
            self.user_text_box.image,
            (
                game_engine_constants.WIDTH
                - (utb_width + 2 * self.user_text_box.border_thickness),
                game_engine_constants.HEIGHT
                - (utb_height + 2 * self.user_text_box.border_thickness),
            ),
        )

        health_surface = self.font.render(f'Health: {self._this_player().health}', False, pygame.Color("white"))
        self.screen.blit(health_surface, (0, game_engine_constants.HEIGHT - health_surface.get_height()))

    def step(self) -> bool:
        delta_time = self.clock.tick(self.frame_rate)

        if self.simulation_state and self.player_id in self.simulation_state.players:
            self._update()
            self._render(delta_time)

        pygame.display.flip()

        return self.running
