from client_instance import ClientInstance


def load_config_file(client_instance: ClientInstance):

    with open("config.cfg", "r") as file:
        for line in file:
            command = '/' + line

            client_instance.command_runner.try_command(command)
