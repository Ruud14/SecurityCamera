import cv2
import threading
import numpy as np
import urllib.request
import imutils
import json
import socket

stream_url = "http://{}:8000/stream.mjpg"


# Getting private data from 'data.json'
file = open('data.json')
stored_data = json.loads(file.read())
username = stored_data["username"]
password = stored_data["password"]
file.close()

cameras = []


class Camera:
    motion_sensitivity = 5  # Higher number = less detection
    current_frame = None
    is_connected = False
    message_port = 5006

    def __init__(self,ip,up):
        self.ip = ip
        self.url = stream_url.format(ip)
        self.is_connected = True
        self.username = up[0]
        self.password = up[1]

        if self.login():
            recv_thread = threading.Thread(target=self.recv_stream).start()
            detect_thread = threading.Thread(target=self.detect_motion).start()

    def login(self):
        try:
            # create a password manager
            password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, self.url, self.username, self.password)
            handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
            opener = urllib.request.build_opener(handler)
            opener.open(self.url)
            urllib.request.install_opener(opener)
            print("Camera login succeeded.")
            return True
        except:
            print("Camera login failed.")
            return False

    # Receives the live video feed from the camera.
    def recv_stream(self):
        # start streaming
        stream = urllib.request.urlopen(self.url)
        bytes = b''
        while True:

            bytes += stream.read(1024)
            a = bytes.find(b'\xff\xd8')
            b = bytes.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg = bytes[a:b + 2]
                bytes = bytes[b + 2:]
                i = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                self.current_frame = i
                if cv2.waitKey(1) == 27:
                    break

        print("Loop Broke")
        self.is_connected = False
        exit(0)

    def detect_motion(self):
        while True:
            try:
                self.current_frame.any()
                break
            except:
                continue

        print("Detector started.")
        f_start = imutils.resize(self.current_frame, width=50, height=50)
        gray = cv2.cvtColor(f_start, cv2.COLOR_BGR2GRAY)
        f_start = cv2.GaussianBlur(gray, (21, 21), 0)
        while True:
            f_next = imutils.resize(self.current_frame, width=50, height=50)
            gray = cv2.cvtColor(f_next, cv2.COLOR_BGR2GRAY)
            f_next = cv2.GaussianBlur(gray, (21, 21), 0)

            frameDelta = cv2.absdiff(f_next, f_start)
            thresh = cv2.threshold(frameDelta, self.motion_sensitivity, 255, cv2.THRESH_BINARY)[1]
            f_start = f_next

            if (thresh.sum() > 100):
                print("movement detected")
                self.send_detection_alert()
            else:
                pass

    def send_detection_alert(self):
        print(f"Sending record message to camera...")
        s = socket.socket()
        s.settimeout(3)
        try:
            s.connect((self.ip, self.message_port))
        except Exception as e:
            print("Sending message to camera failed.", e)
            return
        s.settimeout(None)
        s.send("record".encode())
        s.close()


def add_camera(ip):
    cameras.append(Camera(ip,[username,password]))
    print("Added Camera {}".format(ip))


add_camera("192.168.178.220")
