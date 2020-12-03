import cv2
import threading
import numpy as np
import urllib.request
import json

stream_url = "http://{}:8000/stream.mjpg"


# Class that handles logging into the camera.
class Authentication:
    def __init__(self, ip):
        self.ip = ip
        self.password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        self.url = stream_url.format(ip)

    # Log into the camera.
    def authenticate(self, username, password):
        try:
            self.password_mgr.add_password(None, self.url, username, password)
            handler = urllib.request.HTTPBasicAuthHandler(self.password_mgr)
            opener = urllib.request.build_opener(handler)
            opener.open(self.url)
            urllib.request.install_opener(opener)
            print(f"{self.ip} login succeeded.")
            return True
        except Exception: #todo: Get right exception.
            print("Camera login failed.")
            return False


# Class that handles the detection of motion in the live camera feed.
class Detector:
    def __init__(self, ip, username, password, sensitivity, detection_resolution=(640, 480)):
        self.ip = ip
        self.credentials = (username, password)
        # The sensitivity. Higher number = less detection.
        self.motion_sensitivity = sensitivity
        # Determines the resolution on which the motion is detected.
        # Lower requires less processing power, but might be less precise.
        self.detection_resolution = detection_resolution
        # Create the current frame variables.
        self._current_frame = None
        self._current_low_res_frame = None

    # Starts the detector.
    def start(self):
        # Log into the camera.
        authenticated = Authentication(self.ip).authenticate(*self.credentials)
        # Start the detection of motion if the authentication succeeded.
        if authenticated:
            receive_thread = threading.Thread(target=self.receive_steam)
            detect_thread = threading.Thread(target=self.detect_motion)
            receive_thread.start()
            detect_thread.start()

    # Receives the live video feed from the camera.
    def receive_steam(self):
        # start streaming
        stream = urllib.request.urlopen(stream_url.format(self.ip))
        bytes = b''
        while True:
            bytes += stream.read(1024)
            frame_start = bytes.find(b'\xff\xd8')
            frame_end = bytes.find(b'\xff\xd9')
            if frame_start != -1 and frame_end != -1:
                jpg = bytes[frame_start:frame_end + 2]
                bytes = bytes[frame_end + 2:]
                frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                # Resize the low-res image for faster detection.
                #TODO: make low res resolution changable.
                low_res_frame = cv2.resize(frame, self.detection_resolution, interpolation=cv2.INTER_AREA)
                self._current_low_res_frame = low_res_frame
                self._current_frame = frame

    def detect_motion(self):
        # Wait until the first frame is found. Start detecting afterwards.
        while True:
            try:
                self._current_low_res_frame.any()
                break
            except Exception:
                continue

        print(f"Motion detection on {self.ip} started.")
        # get the previous frame.
        start_frame = cv2.cvtColor(self._current_low_res_frame, cv2.COLOR_BGR2GRAY)
        while True:
            # get the current frame.
            next_frame = cv2.cvtColor(self._current_low_res_frame, cv2.COLOR_BGR2GRAY)

            #TODO: Show frames for testing.
            # cv2.imshow("Resized image", next_frame)
            # cv2.waitKey(1)

            # Calculate the difference between the current and previous frame.
            frame_difference = cv2.absdiff(next_frame, start_frame)
            thresh = cv2.threshold(frame_difference, self.motion_sensitivity, 255, cv2.THRESH_BINARY)[1]
            start_frame = next_frame

            # Start recording when the difference between the frames is too big.
            if thresh.sum() > 100:
                print(f"Movement detected on {self.ip}.")


if __name__ == "__main__":
    with open('config.json') as file:
        stored_data = json.loads(file.read())
        for camera in stored_data:
            Detector(*list(camera.values())).start()
