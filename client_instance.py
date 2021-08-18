import pygame
import game_engine_constants
from textbox import TextInputBox
import commands
from comms import message, network
import socket

class ClientInstance:
    def __init__(self, uuid: str, socket: socket.socket, fullscreen: bool, sensitivity: bool):
        self.uuid = uuid
        self.socket = socket

        self.running = True
        self.user_typing = False
        self.user_text_box = TextInputBox(
            0, 0, game_engine_constants.WIDTH / 3, self.font
        )

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
                        # TODO run command
                        pass
                    else:
                        text_message = message.PlayerTextMessage(
                            player_id=self.uuid, text=text
                        )
                        network.send(self.socket, text_message)

                elif event.key == pygame.K_ESCAPE:
                    self.is_typing = False
                    self.user_text_box.text = ''

        
        
    def update(events) -> None:
        just_started = False

        if not self.is_typing:
            if helpers.started_typing(events):  # only check if they pressd when not typing
                client_game_manager.is_typing = True
                just_started = True
        else:
            if helpers.ended_typing_and_do_action(
                events
            ):  # they are typing and then press return
                client_game_manager.is_typing = False
                # DO ACTION
                text = client_game_manager.user_text_box.text
                if commands.is_command(text):
                    client_game_manager.client_command_runner.attempt_run_command(text)
                else:
                    # then we're dealing with a normal chat message
                    text_message = message.PlayerTextMessage(
                        player_id=player.player_id, text=text
                    )
                    network.send(player.socket, text_message)

                # print(f"sending {client_game_manager.user_text_box.text}")
                client_game_manager.user_text_box.text = ""
            elif helpers.ended_typing_and_do_nothing(events):
                client_game_manager.is_typing = False
                client_game_manager.user_text_box.text = ""

        if client_game_manager.is_typing and not just_started:
            client_game_manager.user_text_box.update(events)

        # Note: This sends the users inputs to the server
        client_game_manager.all_sprites.update()

        player.send_inputs(client_game_manager.is_typing)

    def step(self) -> bool:
        delta_time = self.clock.tick(game_engine_constants.FPS)

        self._process_pygame_events()
        
        update(client_game_manager, player, events)

        render(client_game_manager, delta_time, player, screen, font)

        pygame.display.flip()
        
        return self.running