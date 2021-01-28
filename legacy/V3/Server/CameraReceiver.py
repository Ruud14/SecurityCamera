import json
import time
import threading
import urllib.request
from detector import Camera

stream_url = "http://{}:8000/stream.mjpg"


# Getting private data from 'data.json'
file = open('data.json')
stored_data = json.loads(file.read())
username = stored_data["username"]
password = stored_data["password"]
file.close()


class CameraReceiver:
    cameras = []
    camera_count = 0

    def __init__(self,ips):
        self.ips = ips
        print("Starting receiver...")
        # Start accepting client connections.
        accept_connections_thread = threading.Thread(target=self.accept_connections)
        accept_connections_thread.start()
        print("Receiver started.")

    # Deals with clients trying to connect.
    def accept_connections(self):
        while True:
            while len(self.cameras) < len(self.ips):
                active_ips = []
                [active_ips.append(cam.ip) for cam in self.cameras]
                for ip in self.ips:
                    if not ip in active_ips:
                        self.attempt_connection(ip)

            # Check for disconnected clients
            for cam in self.cameras:
                if not cam.is_connected:
                    self.cameras.remove(cam)
            time.sleep(10)

    def attempt_connection(self, ip):
        try:
            url = stream_url.format(ip)

            # create a password manager
            password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, url, username, password)
            handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
            opener = urllib.request.build_opener(handler)
            opener.open(url)
            urllib.request.install_opener(opener)

            self.cameras.append(Camera(ip,[username,password]))
            print("Added Camera")
        except Exception as e:
            print("Adding camera failed:",e)
