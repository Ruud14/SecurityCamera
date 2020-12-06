import cv2
import threading
import numpy as np
import urllib.request
import json
import subprocess
import os
import datetime
import time
import socket

stream_url = "http://{}:8000/stream.mjpg"
config_file_path = '/home/pi/scripts/V4/config.json'


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
            print("{} login succeeded.".format(self.ip))
            return True
        except urllib.error.URLError:
            print("Camera login failed.")
            return False


# Class that handles the detection of motion in the live camera feed.
class Detector:
    def __init__(self, ip, username, password, sensitivity, detection_resolution=(80, 45)):
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
        # Create the recorder
        self.recorder = Recorder(self.ip, self.credentials)

    # Starts the detector.
    def start(self):
        # Log into the camera.
        authenticated = Authentication(self.ip).authenticate(*self.credentials)
        # Start the detection of motion if the authentication succeeded.
        if authenticated:
            receive_thread = threading.Thread(target=self._receive_steam)
            detect_thread = threading.Thread(target=self._detect_motion)
            receive_thread.start()
            detect_thread.start()

    # Receives the live video feed from the camera.
    def _receive_steam(self):
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

    def _detect_motion(self):
        blur = (5, 5)
        # Wait until the first frame is found. Start detecting afterwards.
        while True:
            try:
                self._current_low_res_frame.any()
                break
            except Exception:
                continue

        print("Motion detection on {} started.".format(self.ip))
        # get the previous frame.
        start_frame = cv2.cvtColor(self._current_low_res_frame, cv2.COLOR_BGR2GRAY)
        start_frame = cv2.GaussianBlur(start_frame, blur, 0)
        while True:
            # get the current frame.
            next_frame = cv2.cvtColor(self._current_low_res_frame, cv2.COLOR_BGR2GRAY)
            next_frame = cv2.GaussianBlur(next_frame, blur, 0)
            # TODO: Show frames for testing.
            # cv2.imshow("Resized image", next_frame)
            # cv2.waitKey(1)

            # Calculate the difference between the current and previous frame.
            frame_difference = cv2.absdiff(next_frame, start_frame)
            thresh = cv2.threshold(frame_difference, self.motion_sensitivity, 255, cv2.THRESH_BINARY)[1]
            start_frame = next_frame

            # Start recording when the difference between the frames is too big.
            if thresh.sum() > 100:
                print("Movement detected on {}.".format(self.ip))
                self.recorder.report_motion()


# Class that handles the recording.
class Recorder:
    def __init__(self, ip, credentials):
        self.ip = ip
        self.credentials = credentials
        self.video_output_folder = stored_data['local_video_output_folder']
        self.record_seconds_after_movement = stored_data['record_seconds_after_movement']
        self.max_recording_seconds = stored_data['max_recording_seconds']
        self.storage_option = stored_data['storage_option']
        self.timer = 0
        self.sender = Sender(self.storage_option)

    # Method to call when there is motion.
    # This will start the recording if it hadn't already been started.
    # Extend the recording if the recording has already started.
    def report_motion(self):
        if self.timer == 0:
            self.timer = self.record_seconds_after_movement
            self._start_recording()
        else:
            self.timer = self.record_seconds_after_movement

    # Starts the recording
    def _start_recording(self):
        current_time_string = str(datetime.datetime.now())[11:13] + "-" + str(datetime.datetime.now())[14:16] + '-' + str(
            datetime.datetime.now())[17:19]
        output_file_path = os.path.join(self.video_output_folder, current_time_string + ".mp4")

        process = subprocess.Popen(
            ['ffmpeg', '-use_wallclock_as_timestamps', '1', '-i', 'http://{}:{}@localhost:8000/delayed_stream.mjpg'.format(*self.credentials), '-an',
             '-vcodec', 'copy', "{}".format(output_file_path)], stdin=subprocess.PIPE)

        threading.Thread(target=self._start_countdown, args=(process, output_file_path,), daemon=True).start()

    # Starts counting down from record_seconds_after_movement after movement is detected.
    def _start_countdown(self, process, file_path):
        self.timer = self.record_seconds_after_movement
        print("Started Recording {}".format(file_path))
        recorded_time = 0
        while self.timer > 0 and not recorded_time > self.max_recording_seconds:
            time.sleep(1)
            recorded_time += 1
            self.timer -= 1
        process.communicate(b'q')
        time.sleep(1)
        process.terminate()
        process.kill()
        print("Stopped Recording {}".format(file_path))
        if self.storage_option != "local":
            threading.Thread(target=self.sender.send_recording, args=(file_path,)).start()


class Sender:
    def __init__(self, storage_ip):
        self.storage_ip = storage_ip
        self.transfer_port = 5005

    # Sends the recorded file to server and deletes the file.
    def send_recording(self, filepath):
        if os.path.isfile(filepath):
            print("Sending Recording {} to server.".format(filepath))
            s = socket.socket()
            s.settimeout(5)
            try:
                s.connect((self.storage_ip, self.transfer_port))
            except Exception as e:
                print(
                    "Sending recording failed,"
                    " Still removing the recording to prevent local storage from getting full. \n",
                    str(e))
                os.remove(filepath)
                return
            s.settimeout(None)
            s.send(("EXISTS" + str(os.path.getsize(filepath))).encode())
            print("FileSize: ", str(os.path.getsize(filepath)).encode())
            response = s.recv(1024)
            response = response.decode()
            if response.startswith('OK'):
                with open(filepath, 'rb') as f:
                    bytes_to_send = f.read(4096)
                    s.send(bytes_to_send)
                    while bytes_to_send != b"":
                        bytes_to_send = f.read(4096)
                        s.send(bytes_to_send)
            s.close()
            os.remove(filepath)
            print("File Removed")


if __name__ == "__main__":
    with open(config_file_path) as file:
        stored_data = json.loads(file.read())
        Detector(stored_data["IP"], stored_data["username"], stored_data["password"], stored_data["sensitivity"]).start()
