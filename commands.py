from typing import Callable, Any
from dataclasses import dataclass
from comms.message import PlayerTextMessage
from comms import network


def is_command(message: str | Any) -> bool:
    return bool(message) and message[0] == "/"


@dataclass
class Command:
    callable: Callable
    arg_types: list[Any]


class CommandRunner:
    # NOTE: client_instance cannot be typed without creating a dependency cycle
    def __init__(self, client_instance: Any) -> None:
        self.client_instance = client_instance
        self.command_to_action = {
            "sens": Command(callable=self.set_sensitivity, arg_types=[float]),
            "ready": Command(callable=self.ready, arg_types=[]),
            "map_vote": Command(callable=self.map_vote, arg_types=[str]),
            "quit": Command(callable=self.quit, arg_types=[]),
        }

    def parse_command(self, command: str) -> tuple[str, list[Any]]:
        """
        Attempt to parse the full_command
        """
        command = command[1:]  # strip /
        try:
            command_name, arg_str = command.split(" ", 1)
            args = arg_str.split(" ")
        except ValueError:
            command_name = command
            args = []  # okay if the command takes no args

        if command_name not in self.command_to_action:
            raise ValueError("Command does not exist")

        expected_arg_types = self.command_to_action[command_name].arg_types
        assert len(args) == len(expected_arg_types)  # type: ignore

        arg_list: list[Any] = []
        for expected_arg_type, arg in list(zip(expected_arg_types, args)):  # type: ignore
            arg_list.append(expected_arg_type(arg))  # type: ignore

        return command_name, arg_list

    def try_command(self, command: str | Any) -> None:
        """Given a command attempt to run it"""
        try:
            command_name, args = self.parse_command(command)
            self.command_to_action[command_name].callable(args)  # type: ignore

        except Exception:
            self.client_instance.user_chat_box.add_message(f"Command {command} failed!")

    def set_sensitivity(self, args: list[float]) -> None:
        sensitivity = args[0]
        self.client_instance.set_sensitivity(sensitivity)
        self.client_instance.user_chat_box.add_message(
            f"Sensitivity set to {sensitivity}"
        )

    def ready(self, _: Any) -> None:
        self.client_instance.ready = True
        # TODO this is bad
        text_message = PlayerTextMessage(
            player_id=self.client_instance.player_id, text=f"readied up"
        )
        network.send(self.client_instance.socket, text_message)

    def map_vote(self, args: list[str]) -> None:
        map_vote = args[0]
        self.client_instance.map_vote = map_vote
        # TODO this is bad
        text_message = PlayerTextMessage(
            player_id=self.client_instance.player_id, text=f"voted for map {map_vote}"
        )
        network.send(self.client_instance.socket, text_message)

    def quit(self, _: Any) -> None:
        self.client_instance.quit()
        # TODO this is bad
        text_message = PlayerTextMessage(
            player_id=self.client_instance.player_id, text=f"quit the game"
        )
        network.send(self.client_instance.socket, text_message)
