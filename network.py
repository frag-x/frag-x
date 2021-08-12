import socket
from typing import Tuple


class Network:
    def __init__(self, ip, port, buffer_size):
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self) -> str:
        """Attempt to connect to server"""
        server_address = (self.ip, self.port)
        try:
            self.socket.connect(server_address)
            return self.socket.recv(self.buffer_size).decode()

        except socket.error as e:
            print(e)

    def send_and_receive(self, data) -> str:
        """Attempt to send data to the server, then get a responce"""
        try:
            self.socket.send(str.encode(data))
            return self.socket.recv(self.buffer_size).decode()

        except socket.error as e:
            print(e)

    def send(self, data) -> str:
        """Attempt to send data to the server, also appends ~ to the end of the message"""
        try:
            data += "~"
            self.socket.send(str.encode(data))

        except socket.error as e:
            print(e)

    def sendall(self, data) -> str:
        """Attempt to send data to the server"""
        try:
            self.socket.sendall(str.encode(data))

        except socket.error as e:
            print(e)
