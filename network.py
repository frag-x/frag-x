import socket
from typing import Tuple
from game_engine_constants import BUF_SIZE, LOCAL_IP, PORT, REMOTE_IP, RUNNING_LOCALLY
import game_engine_constants


class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if RUNNING_LOCALLY:
           self.server_address = (LOCAL_IP, PORT)
        elif game_engine_constants.RUNNING_ON_LAN:
           self.server_address = (game_engine_constants.LAN_IP, PORT)
        else:
           self.server_address = (REMOTE_IP, PORT)

    def connect(self) -> str:
        """Attempt to connect to server"""
        try:
            print(f"attempting to connect to: {self.server_address}")
            self.client.connect(self.server_address)
            print(f"connected to {self.server_address}")
            return self.client.recv(BUF_SIZE).decode()
        except socket.error as e:
            print(e)

    def send_and_receive(self, data) -> str:
        """Attempt to send data to the server, then get a responce"""
        try:
            self.client.send(str.encode(data))
            return self.client.recv(BUF_SIZE).decode()
        except socket.error as e:
            print(e)

    def send(self, data) -> str:
        """Attempt to send data to the server, also appends \0 to the end of the message"""
        try:
            data += '~'
            self.client.send(str.encode(data))
        except socket.error as e:
            print(e)

    def sendall(self, data) -> str:
        """Attempt to send data to the server"""
        try:
            print("sending", data)
            self.client.sendall(str.encode(data))
        except socket.error as e:
            print(e)

class FragNetwork(Network):
    def get_initial_position(self) -> Tuple[int, int]:
        return self.convert_pos_str_repr_to_int_repr(self.initialization_data)

