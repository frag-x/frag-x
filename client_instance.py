import pygame
import game_engine_constants
from textbox import TextInputBox
import commands
from comms.message import PlayerStateMessage, PlayerTextMessage
from comms import network
import socket
import map_loading
import math
from chatbox import ChatBox

class ClientInstance:
    def __init__(self, uuid: str, socket: socket.socket, fullscreen: bool, sensitivity: bool):
        self.uuid = uuid
        self.socket = socket

        self.running = True
        self.user_typing = False
        self.user_text_box = TextInputBox(
            0, 0, game_engine_constants.WIDTH / 3, self.font
        )
        self.user_chat_box = ChatBox(
            self.screen,
            game_engine_constants.WIDTH * 0.8,
            0,
            game_engine_constants.WIDTH * 0.2,
            600,
            self.font,
        )
        self.map = map_loading.load_map('some map') # TODO this should come from server

        self.position = None # TODO this should come from server
        self.rotation = None # TODO this should come from server
        self.camera_v = game_engine_constants.SCREEN_CENTER_POINT # TODO figure out what this is

        self._setup_pygame(fullscreen)

    def _setup_pygame(self, fullscreen: bool) -> None:
        pygame.init()
        pygame.mixer.init() # sound
        pygame.font.init()

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), 30)

        if fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            (
                game_engine_constants.WIDTH,
                game_engine_constants.HEIGHT,
            ) = pygame.display.get_surface().get_size()
            game_engine_constants.SCREEN_CENTER_POINT = (
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

    def _process_pygame_events(self) -> None:
        events = pygame.event.get()
        for i, event in enumerate(events):
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    self.user_typing = True
                    # only register key presses after user typing is active
                    events = events[i+1:]
                elif event.key == pygame.K_RETURN:
                    self.user_typing = False
                    # TODO make user_text_box smarter by adding a method
                    text = self.user_text_box.text
                    self.user_text_box.text = ''

                    if commands.is_command(text):
                        pass # TODO run command
                    else:
                        text_message = PlayerTextMessage(
                            player_id=self.uuid, text=text
                        )
                        network.send(self.socket, text_message)

                elif event.key == pygame.K_ESCAPE:
                    self.is_typing = False
                    self.user_text_box.text = ''

        if self.is_typing:
            self.user_text_box.update(events)

    def send_inputs(self):
        # we only look at the x component of mouse input
        dm, _ = pygame.mouse.get_rel()
        dm *= self.sensitivity

        keys = pygame.key.get_pressed()

        if self.user_typing:
            x_movement = 0
            y_movement = 0
        else:
            # If the player isn't typing then sample their input devices for gameplay
            l, u, r, d = self.movement_keys
            x_movement = int(keys[r]) - int(keys[l])
            y_movement = -(int(keys[u]) - int(keys[d]))

        for key in self.weapon_keys:
            if keys[key]:
                if key == pygame.K_c:
                    self.weapon_selection = 0
                elif key == pygame.K_x:
                    self.weapon_selection = 1

        firing = pygame.mouse.get_pressed()[0]

        output_message = PlayerStateMessage(
            player_id=self.player_id,
            delta_position=pygame.math.Vector2(x_movement, y_movement),
            delta_mouse=dm,
            firing=firing,
            weapon_selection=self.weapon_selection,
            ready=self.ready,
            map_vote=self.map_vote,
        )

        network.send(self.socket, output_message)
        
    def _update(self) -> None:
        self._process_pygame_events()

        self.all_sprites.update() # TODO figure out how to use this

        self.send_inputs()
        
    self._draw_rockets():
        pass

    self._draw_hitscan_beams():
        pass

    def _render(self, delta_time: float) -> None:
        self.screen.fill(pygame.color.THECOLORS["black"])  # type: ignore

        for row in self.map.partitioned_map:
            for partition in row:
                pygame.draw.rect(
                    self.screen,
                    pygame.color.THECOLORS["gold"],  # type: ignore
                    partition.rect.move(self.camera_v),
                    width=1,
                )

                for wall in partition.walls:
                    pygame.draw.rect(self.screen, wall.color, wall.rect.move(self.camera_v))

                for b_wall in partition.bounding_walls:
                    pygame.draw.rect(
                        self.screen, b_wall.color, b_wall.rect.move(self.camera_v)
                    )

        self._draw_projectiles(self.camera_v)
        self._draw_beams(self.camera_v)

        # A drawing is based on a single network message from the server.
        # The reason why it looks like we have shifted tiles is that we received a message in the middle, so this needs to be locked.
        # instead of actually simulating its movement that way it seems more solid
        for sprite in self.all_sprites: # TODO
            # Add the player's camera offset to the coords of all sprites.
            self.screen.blit(sprite.image, sprite.rect.topleft + self.camera_v)

        font_color = pygame.color.THECOLORS["brown3"]  # type: ignore

        # TODO this math shouldn't happen here
        # TODO actually this whole section is utterly fucked.
        # make these objects smarter so the code doesn't live here
        pos = self.font.render(str(self.position), False, font_color)
        aim_angle_str = (
            str(9 - math.floor(self.rotation / math.tau * 10)) + "/" + str(10)
        )
        angle = self.font.render(aim_angle_str + "τ", False, font_color)

        self.screen.blit(pos, (0, 25))
        self.screen.blit(angle, (0, 50))

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

    def step(self) -> bool:
        delta_time = self.clock.tick(game_engine_constants.FPS)

        self._update()
        self._render(delta_time)

        pygame.display.flip()
        
        return self.running
