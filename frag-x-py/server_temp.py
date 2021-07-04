import socket
import _thread
import sys 

SERVER_ADDRESS = "172.27.137.248"
PORT = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


try: 
    s.bind((SERVER_ADDRESS, PORT))

except socket.error as e:
    str(e)

s.listen(2)

print("Server started")

def threaded_client(conn):
    conn.send(str.encode("Connected"))
    reply = ""
    while True:
        try: 
            data = conn.recv(2**11)
            reply = data.decode("utf-8")

            if not data:
                # Likely means we've disconnected
                print("Disconnected")
                break
            else:
                print(f"Received: {reply}")
                print(f"Sending: {reply}")

            conn.sendall(str.encode(reply))
        except:
            break

    print("Lost connection")
    conn.close()

while True:
    conn, addr = s.accept()
    print(f"Accept connection from {addr}")

    _thread.start_new_thread(threaded_client, (conn,))

