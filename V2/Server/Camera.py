
import cv2
import time
import threading
import numpy as np
import datetime
import os
import urllib.request


class Camera:
    # ------------- Values you might want to change ----------------

    picture_size = (1280, 720)
    motion_sensitivity = 20  # Higher number = less detection

    video_output_folder = "./Recordings/"

    max_storage = 1.25 # In Gb

    record_seconds_after_movement = 10
    #  This is set to the value of record_seconds_after_movement when movement gets detected
    #  and stops the recording when it is equal to zero.

    # --------------------------------------------------------------

    fps = 30
    timer = 0
    current_frame = None
    video_output = None
    detected_motion = False
    is_connected = False
    safe_to_write = True
    feature_params = dict(maxCorners=100, qualityLevel=.6, minDistance=25, blockSize=9)
    fgbg = cv2.createBackgroundSubtractorMOG2()
    kernel = np.ones((motion_sensitivity, motion_sensitivity), np.uint8)
    fourcc = cv2.VideoWriter_fourcc(*'H264')
    #fourcc = cv2.VideoWriter_fourcc(*'X264')
    delay = 1 / (fps + 5)

    def __init__(self,url,id):
        self.url = url
        self.id = id
        self.is_connected = True
        recv_thread = threading.Thread(target=self.recv_stream).start()
        detect_thread = threading.Thread(target=self.detect_motion).start()
        record_thread = threading.Thread(target=self.record).start()
        #self.tim = datetime.datetime.now()
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
                #cv2.imshow('i', i)
                self.current_frame = i
                # print(1/(datetime.datetime.now()-self.tim).total_seconds())
                # self.tim = datetime.datetime.now()
                if cv2.waitKey(1) == 27:
                    break

        print("Loop Broke")
        self.is_connected = False
        exit(0)

    def detect_motion(self):
        frame = np.zeros(5)
        while True:


            try:
                if not self.current_frame.any():
                    continue
            except:
                continue
            frame = self.current_frame
            # w, h = frame.shape[::-1][1:]

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
                for detection in detections:
                    xy = int(detection[0][0]), int(detection[0][1])
                    cv2.circle(frame, (xy[0], xy[1]), 10, (255, 0, 0), 2)
            else:
                self.detected_motion = False


    def start_recording(self):
        # Checks if this is the first frame of the recording.
        current_date = str(datetime.date.today())
        # Create a folder for the specific date if there isn't one already.
        if not os.path.isdir(os.path.join(self.video_output_folder,current_date)):
            os.mkdir(os.path.join(self.video_output_folder,current_date))

        current_time = str(datetime.datetime.now())[11:13]+"-"+str(datetime.datetime.now())[14:16]+'-'+str(datetime.datetime.now())[17:19]
        output_filepath = os.path.join(self.video_output_folder, current_date, current_time+".mp4")
        self.video_output = cv2.VideoWriter(output_filepath, self.fourcc, self.fps, self.picture_size)
        threading.Thread(target=self.start_countdown, daemon=True).start()
        # Thread the making of room so recording doesn't have to wait.
        threading.Thread(target=self.make_room, daemon=True).start()

    def record(self):
        frame = np.zeros(5)
        while True:
            # start_time = datetime.datetime.now()
            try:
                if not self.current_frame.any():
                    continue
            except:
                continue
            frame = self.current_frame
            # Save the video if there is any movement.
            if self.detected_motion:
                # Reset the timer
                if self.timer == 0:
                    self.start_recording()
                self.timer = self.record_seconds_after_movement

            if self.timer is not 0:
                # while not self.safe_to_write:
                #     pass
                try:
                    self.video_output.write(frame)
                except AttributeError:
                    # The Writer has already been destroyed by the start_countdown loop.
                    pass
                self.safe_to_write = False
                time.sleep(self.delay)

            # end_time = datetime.datetime.now()
            # try:
            #     fps = 1 / (end_time - start_time).total_seconds()
            # except:
            #     fps = 1000
            # print("Fps: ", round(fps, 2))

    # Makes room for video's is there isn't enough.
    def make_room(self):
        # Convert Gb to b.
        max_folder_size = 1000000000*self.max_storage
        file_dict = {}

        # Calculates the size of a folder and populates file_dict.
        def calc_folder_size(path):
            size = 0
            for dirpath, dirs, files in os.walk(path):
                for f in files:
                    fp = os.path.join(dirpath, f)
                    size += os.path.getsize(fp)
                    file_dict[fp] = os.path.getctime(fp)
                # Remove directories if they are empty, they might get empty because of deleting files to save storage.
                for dir in dirs:
                    if not os.listdir(os.path.join(dirpath, dir)):
                        os.rmdir(os.path.join(dirpath, dir))
            return size

        folder_size = calc_folder_size(self.video_output_folder)
        print("FOLDER SIZE:", folder_size)
        # Sort the files based on the ctime.
        files = sorted(file_dict.items(), key=lambda x: x[1])

        # Delete the oldest file as long as there is too little storage left.
        while folder_size >= max_folder_size:
            deleted_size = os.path.getsize(files[0][0])
            os.remove(files[0][0])
            del files[0]
            folder_size -= deleted_size
            print("File ", files[0][0], " Deleted because there wasn't enough space.")

    # Starts counting down from record_seconds_after_movement after movement is detected.
    def start_countdown(self):
        self.timer = self.record_seconds_after_movement
        print("Started Recording")
        while self.timer > 0:
            # print(self.timer)
            time.sleep(1)
            self.timer -= 1
        self.video_output.release()
        self.video_output = None
        print("Stopped Recording")



