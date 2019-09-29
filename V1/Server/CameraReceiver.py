import socket
import cv2
import json
import threading
import numpy as np
from Camera import Camera


class CameraReceiver:
    camera_count = 2
    s = socket.socket()
    secret_key = None
    cameras = []

    def __init__(self):
        print("Starting receiver...")
        # Getting private data from 'data.json'
        file = open('data.json')
        stored_data = json.loads(file.read())
        # Setting up the socket.
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((stored_data["server_ip"],stored_data["server_port"]))
        self.s.listen(2)
        self.secret_key = stored_data["secret_key"]
        file.close()
        # Start accepting client connections.
        accept_connections_thread = threading.Thread(target=self.accept_connections)
        accept_connections_thread.start()
        # populate the list so items can be accessed by index.
        print("Receiver started.")

    # Deals with clients trying to connect.
    def accept_connections(self):
        # 'pass' = permission to enter the secret key.
        # 'True' = the secret key was correct, connection established.
        # 'False' = the secret key was incorrect.
        while True:
            while len(self.cameras) < self.camera_count:
                conn, addr = self.s.accept()
                # remove the client if it isn't a local one.
                if not addr[0].startswith("192.168."):
                    print("Non-local client!")
                    conn.close()
                    continue
                # Asks the client for a password.
                conn.send("pass".encode("utf-8"))
                password = conn.recv(1024).decode("utf-8")
                # Checks if the password is correct.
                if password == self.secret_key:
                    conn.send("True".encode("utf-8"))
                    print(f"{addr} connected.")
                else:
                    conn.send("False".encode("utf-8"))
                    conn.close()

                client_camera = Camera(conn,len(self.cameras))
                self.cameras.append(client_camera)

            # Check for disconnected clients
            for cl in self.cameras:
                if not cl.is_connected:
                    self.cameras.remove(cl)

    def get_camera_frame_in_bytes(self,cam_number):
        i = cam_number-1
        try:
            return self.cameras[i].get_current_frame_in_bytes()
        except IndexError:
            pass