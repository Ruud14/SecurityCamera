import socket
import cv2
import time
import threading
import struct
import numpy as np
import datetime
import os
import base64


class Camera:

    # ------------- Values you might want to change ----------------
    # 720p
    picture_size = (1280,720)

    # 1080p
    # picture_size = (1920, 1080)

    motion_sensitivity = 8  # Higher number = less detection

    video_output_folder = ".\\Recordings\\"

    max_storage = 50 # In Gb

    record_seconds_after_movement = 10
    #  This is set to the value of record_seconds_after_movement when movement gets detected
    #  and stops the recording when it is equal to zero.

    # --------------------------------------------------------------

    fps = 0
    timer = 0
    id = None
    current_frame = None
    video_output = None
    detected_motion = False
    is_connected = False
    feature_params = dict(maxCorners=100, qualityLevel=.6, minDistance=25, blockSize=9)
    fgbg = cv2.createBackgroundSubtractorMOG2()
    kernel = np.ones((motion_sensitivity, motion_sensitivity), np.uint8)
    fourcc = cv2.VideoWriter_fourcc('M','J','P','G')

    def __init__(self, connection, id):
        self.id = id
        self.connection = connection
        self.connection.settimeout(10)
        self.is_connected = True
        recv_thread = threading.Thread(target=self.recv_stream)
        recv_thread.start()

    # Receives the live video feed from the camera.
    def recv_stream(self):
        payload_size = struct.calcsize("<L")
        data = b''
        while True:
            try:
                start_time = datetime.datetime.now()
                # keep receiving data until it gets the size of the msg.
                while len(data) < payload_size:
                    data += self.connection.recv(4096)
                # Get the frame size and remove it from the data.
                frame_size = struct.unpack("<L", data[:payload_size])[0]
                data = data[payload_size:]
                # Keep receiving data until the frame size is reached.
                while len(data) < frame_size:
                    data += self.connection.recv(131072)
                # Cut the frame to the beginning of the next frame.
                frame_data = data[:frame_size]
                data = data[frame_size:]

                # using the old pickling method.
                # frame = pickle.loads(frame_data)

                # Converting the image to be sent.
                img = base64.b64decode(frame_data)
                npimg = np.fromstring(img, dtype=np.uint8)
                frame = cv2.imdecode(npimg, 1)

                frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

                end_time = datetime.datetime.now()
                fps = 1/(end_time-start_time).total_seconds()
                print("Fps: ",round(fps,2))
                self.detect_motion(frame,fps)

                self.current_frame = frame

            except (socket.error,socket.timeout) as e:
                # The timeout got reached or the client disconnected. Clean up the mess.
                print("Cleaning up: ",e)
                try:
                    self.connection.close()
                except socket.error:
                    pass
                self.is_connected = False
                break

    def detect_motion(self, frame,fps):
        original_frame = frame

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
            for detection in detections:
                xy = int(detection[0][0]), int(detection[0][1])
                cv2.circle(frame, (xy[0], xy[1]), 10, (255, 0, 0), 2)

        # Save the video if there is any movement.
        if detections is not None:
            if len(detections) > 0 or self.timer > 0:
                if len(detections) > 0 and self.timer > 0:
                    # Reset the timer when already recording and movement gets detected.
                    self.timer=self.record_seconds_after_movement
                # Checks if this is the first frame of the recording.
                if self.timer == 0:
                    current_date = str(datetime.date.today())
                    # Create a folder for the specific date if there isn't one already.
                    if not os.path.isdir(os.path.join(self.video_output_folder,current_date)):
                        os.mkdir(os.path.join(self.video_output_folder,current_date))

                    current_time = str(datetime.datetime.now())[11:13]+"-"+str(datetime.datetime.now())[14:16]+'-'+str(datetime.datetime.now())[17:19]
                    output_filepath = os.path.join(self.video_output_folder, current_date, current_time+".avi")
                    self.video_output = cv2.VideoWriter(output_filepath, self.fourcc, round(fps,2), self.picture_size)
                    threading.Thread(target=self.start_countdown).start()
                    # Thread the making of room so recording doesn't have to wait.
                    threading.Thread(target=self.make_room).start()

        if self.timer is not 0:
            self.video_output.write(original_frame)

        # You might want to enable this while testing (on a machine WITH GUI)
        # cv2.imshow(f'image{self.id}', frame)
        cv2.imshow(f'original Frame{self.id}', original_frame)
        cv2.waitKey(1)

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
            print(self.timer)
            time.sleep(1)
            self.timer -= 1
        self.video_output.release()
        print("Stopped Recording")

    # Gets the frame in bytes (I used this for displaying the frame on a webpage)
    def get_current_frame_in_bytes(self):
        try:
            ret, jpeg = cv2.imencode('.jpg', self.current_frame)
            return jpeg.tobytes()
        except cv2.error:
            # Image corrupt or empty.
            pass

