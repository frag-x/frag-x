from typing import Any
from comms.message import Message
import pickle
import socket


def _recv_exactly(socket: socket.socket, num_bytes: int) -> bytes:
    data = b""
    while len(data) < num_bytes:
        chunk = socket.recv(num_bytes - len(data))
        if not chunk:
            raise ConnectionResetError
        data += chunk  # TODO this is quadratic, should join instead
    return data


def send(socket: socket.socket, message: Message) -> None:
    bytes = pickle.dumps(message)
    num_message_bytes = len(bytes).to_bytes(4, "little")

    socket.sendall(num_message_bytes + bytes)


def sendto(socket: socket.socket, addr: tuple[Any, Any], message: Message) -> None:
    bytes = pickle.dumps(message)
    socket.sendto(bytes, addr)


def recv(socket: socket.socket) -> Message:
    num_message_bytes_as_bytes = _recv_exactly(socket, 4)
    num_message_bytes = int.from_bytes(num_message_bytes_as_bytes, "little")

    message_as_bytes = _recv_exactly(socket, num_message_bytes)
    message = pickle.loads(message_as_bytes)
    return message


def recvfrom(socket: socket.socket) -> tuple[Message, tuple[Any, Any]]:
    bytes, addr = socket.recvfrom(65507)
    message = pickle.loads(bytes)
    return message, addr
