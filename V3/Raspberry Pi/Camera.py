
import cv2
import time
import threading
import numpy as np
import datetime
import os
import urllib.request
import subprocess
import socket


class Camera:
    # ------------- Values you might want to change ----------------

    picture_size = (1920, 1080)
    motion_sensitivity = 20  # Higher number = less detection
    video_output_folder = "/home/pi/recordings/"
    record_seconds_after_movement = 10
    max_recording_time = 300    # in seconds
    server_ip = '192.168.178.129'
    server_port = 5000
    #  This is set to the value of record_seconds_after_movement when movement gets detected
    #  and stops the recording when it is equal to zero.

    # --------------------------------------------------------------

    timer = 0
    current_frame = None
    detected_motion = False
    is_connected = False
    feature_params = dict(maxCorners=100, qualityLevel=.6, minDistance=25, blockSize=9)
    fgbg = cv2.createBackgroundSubtractorMOG2()
    kernel = np.ones((motion_sensitivity, motion_sensitivity), np.uint8)

    delay = 0.05

    def __init__(self,url,id,up):
        self.url = url
        self.id = id
        self.is_connected = True
        self.username = up[0]
        self.password = up[1]
        recv_thread = threading.Thread(target=self.recv_stream).start()
        detect_thread = threading.Thread(target=self.detect_motion).start()
        record_thread = threading.Thread(target=self.record).start()

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

    # Detects motion in the current frame
    def detect_motion(self):
        frame = np.zeros(5)
        while True:
            try:
                if not self.current_frame.any():
                    continue
            except:
                continue
            frame = self.current_frame

            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            img3 = self.fgbg.apply(frame)
            img3 = cv2.morphologyEx(img3, cv2.MORPH_OPEN, self.kernel)
            detections = cv2.goodFeaturesToTrack(img3, **self.feature_params)

            rows, cols = img3.shape
            roi = frame[0:rows, 0:cols]
            img3 = cv2.cvtColor(img3, cv2.COLOR_GRAY2BGR)
            imag2gray = cv2.cvtColor(img3, cv2.COLOR_BGR2GRAY)

            ret, mask_inv = cv2.threshold(imag2gray, 220, 255, cv2.THRESH_BINARY_INV)

            img1_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
            img3_fg = cv2.bitwise_and(img3, img3, mask=mask_inv)

            img3_fg = cv2.cvtColor(img3_fg, cv2.COLOR_BGR2GRAY)

            dst = cv2.add(img1_bg, img3_fg)
            frame[0:rows, 0:cols] = dst

            if detections is not None:
                self.detected_motion = True
            else:
                self.detected_motion = False

    # Starts the recording
    def start_recording(self):
        current_time = str(datetime.datetime.now())[11:13]+"-"+str(datetime.datetime.now())[14:16]+'-'+str(datetime.datetime.now())[17:19]
        output_filepath = os.path.join(self.video_output_folder, current_time+".mp4")

        proc = subprocess.Popen(['ffmpeg', '-i', f'http://{self.username}:{self.password}@192.168.178.206:8000/stream.mjpg', '-an', '-vcodec', 'copy', f"{output_filepath}"], stdin=subprocess.PIPE)
        threading.Thread(target=self.start_countdown, args=(proc,output_filepath,), daemon=True).start()

    # Always checks if the recording should be stared and resets the timer whenever there is movement while recording.
    def record(self):
        while True:
            if self.detected_motion:
                # Reset the timer
                if self.timer == 0:
                    self.start_recording()
                self.timer = self.record_seconds_after_movement
            if self.timer is not 0:
                time.sleep(self.delay)

    # Starts counting down from record_seconds_after_movement after movement is detected.
    def start_countdown(self, proc, filepath):
        self.timer = self.record_seconds_after_movement
        print("Started Recording")
        recorded_time = 0
        while self.timer > 0 and not recorded_time > self.max_recording_time:
            time.sleep(1)
            recorded_time += 1
            self.timer -= 1
        proc.communicate(b'q')
        time.sleep(1)
        proc.terminate()
        proc.kill()
        print("Stopped Recording")
        self.send_recording(filepath)

    # Sends the recorded file to server and deletes the file.
    def send_recording(self, filepath):
        if os.path.isfile(filepath):
            print(f"Sending Recording {filepath} to server.")
            s = socket.socket()
            s.settimeout(5)
            try:
                s.connect((self.server_ip, self.server_port))
            except:
                print("Sending recording failed, Still removing the recording to prevent storage from getting full.")
                os.remove(filepath)
                return
            s.settimeout(None)
            s.send(("EXISTS" + str(os.path.getsize(filepath))).encode())
            print("FileSize: ",str(os.path.getsize(filepath)).encode())
            userResponse = s.recv(1024)
            userResponse = userResponse.decode()
            if userResponse.startswith('OK'):
                with open(filepath, 'rb') as f:
                    bytesToSend = f.read(4096)
                    s.send(bytesToSend)
                    while bytesToSend != b"":
                        bytesToSend = f.read(4096)
                        s.send(bytesToSend)
            s.close()
            os.remove(filepath)
            print("File Removed")




