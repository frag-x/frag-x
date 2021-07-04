import socket

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = ("172.27.137.248", 5555)
        #self.id = self.connect()
        self.initialization_data = self.connect()

    def connect(self):
        try:
            self.client.connect(self.server_address)
            return self.client.recv(2**11).decode()
        except:
            pass

    def send(self, data):
        try:
            self.client.send(str.encode(data))
            return self.client.recv(2**12).decode()
        except socket.error as e:
            print(e)

