import enum, re, typing

import player


class CommandType(enum.Enum):
    CLIENT_COMMAND = enum.auto()
    SERVER_COMMAND = enum.auto()


def is_command(message) -> bool:
    return bool(re.match(r"-[cs]", message))


def get_command_type(message):
    command_prefix = message[:3]
    if command_prefix == "-c ":
        return CommandType.CLIENT_COMMAND
    elif command_prefix == "-s ":
        return CommandType.SERVER_COMMAND


class CommandRunner:
    def __init__(self, command_to_action: typing.Dict[str, typing.Callable]):
        self.command_to_action = command_to_action


class ClientCommandRunner(CommandRunner):
    def __init__(self, curr_player: player.ClientPlayer):
        command_to_action = {"sens": curr_player.set_sens}  # (sens)
        super().__init__(command_to_action)

    def parse_command(self, full_command) -> typing.Optional[typing.Tuple[str, float]]:
        """
        Attempt to parse the full_command, if it's invalid then return None,
        otherwise return the command's name and it's associated value as a tuple
        """
        command = full_command[3:].strip()
        try:
            command_name, value = command.split("=")
        except ValueError:
            print("you are using the wrong syntax")
            return None
        try:
            value = float(value)
        except ValueError:
            print("Your commands value is not a number")
            return None
        if command_name not in self.command_to_action:
            print("Your command is not known")
            return None
        return command_name, float(value)

    def attempt_run_command(self, full_command) -> bool:
        """Given a command attempt to run it, if it success return True, otherwise False"""
        parsed_command = self.parse_command(full_command)
        if parsed_command is not None:
            command_name, value = parsed_command
            self.command_to_action[command_name](value)
            return True
        return False

        # TODO this only works for single argument commands will change in future
