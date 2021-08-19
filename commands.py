import enum, re
from typing import Callable, List, Any, Tuple
from dataclasses import dataclass
import game_engine_constants

from simulation_object import player


def is_command(message) -> bool:
    return message and message[0] == '/'

@dataclass
class Command:
    callable: Callable
    arg_types: List[Any]


class CommandRunner:
    def __init__(self, client_instance):
        self.client_instance = client_instance
        self.command_to_action = {
            "sens": Command(callable=self.set_sensitivity, arg_types=[float]),
            "ready": Command(callable=self.ready, arg_types=[]),
            "map_vote": Command(callable=self.map_vote, arg_types=[str]),
            "quit": Command(callable=self.quit, arg_types=[])
        }

    def parse_command(self, command: str) -> Tuple[str, List[Any]]:
        """
        Attempt to parse the full_command
        """
        command = command[1:] # strip /
        try:
            command_name, arg_str = command.split(' ', 1)
            args = arg_str.split(' ')
        except ValueError:
            command_name = command
            args = [] # okay if the command takes no args

        if command_name not in self.command_to_action:
            raise ValueError('Command does not exist')

        expected_arg_types = self.command_to_action[command_name].arg_types
        assert len(args) == len(expected_arg_types) # type: ignore

        arg_list: List[Any] = []
        for expected_arg_type, arg in list(zip(expected_arg_types, args)): # type: ignore
            arg_list.append(expected_arg_type(arg)) # type: ignore

        return command_name, arg_list

    def try_command(self, command) -> None:
        """Given a command attempt to run it"""
        try:
            command_name, args = self.parse_command(command)
            self.command_to_action[command_name].callable(self.client_instance, args) # type: ignore

        except Exception as e:
            print(e)
            print('Command failed!')

    def set_sensitivity(self, client_instance, args):
        sensitivity = args[0]
        client_instance.set_sensitivity(sensitivity)
        print(f'Sensitivity set to {sensitivity}')

    def ready(self, client_instance, _):
        client_instance.ready = not client_instance.ready
        print(f'Player ready state set to {client_instance.ready}')

    def map_vote(self, client_instance, args):
        map_vote = args[0]
        client_instance.map_vote = map_vote
        print(f'Voted for map {map_vote}')

    def quit(self, client_instance, _):
        client_instance.quit()
        print('Player quit')
    