import datetime
import subprocess
import threading
import time
import os
from buffers import RecordingBuffer
from picamera import PiCamera, PiCameraCircularIO

stored_data = None


# Class that handles the recording.
class Recorder:
    def __init__(self, camera, fps, sender, video_output_folder="./recordings/", record_seconds_after_movement=12, max_recording_seconds=300, storage_option='local', delayed_seconds=5):
        self.camera = camera
        self.video_output_folder = video_output_folder
        self.record_seconds_after_movement = record_seconds_after_movement
        self.max_recording_seconds = max_recording_seconds
        self.storage_option = storage_option
        self.timer = 0
        self.sender = sender
        self.delayed_seconds = delayed_seconds
        self.delayed_recording_stream = PiCameraCircularIO(self.camera, seconds=20)
        self.camera.start_recording(self.delayed_recording_stream, format='h264', splitter_port=2)

    # Method to call when there is motion.
    # This will start the recording if it hadn't already been started.
    # Extend the recording if the recording has already started.
    def report_motion(self):
        if self.timer == 0:
            self.timer = self.record_seconds_after_movement
            self._start_recording()
        else:
            self.timer = self.record_seconds_after_movement

    # Starts the recording.
    def _start_recording(self):
        current_time_string = str(datetime.datetime.now())[11:13] + "-" + str(datetime.datetime.now())[14:16] + '-' + str(
            datetime.datetime.now())[17:19]
        output_file_path = os.path.join(self.video_output_folder, current_time_string + ".mp4")
        print('Started recording '+output_file_path)

        # record the frames "after" motion
        self.camera.split_recording('after.h264', splitter_port=2)
        # Write the 10 seconds "before" motion to disk as well
        self.delayed_recording_stream.copy_to('before.h264', seconds=self.delayed_seconds)
        self.delayed_recording_stream.clear()

        threading.Thread(target=self._start_countdown, daemon=True).start()

    # Starts counting down from record_seconds_after_movement after movement is detected.
    # Stop recording if the timer gets to 0.
    def _start_countdown(self):
        self.timer = self.record_seconds_after_movement
        recorded_time = 0
        while self.timer > 0 and not recorded_time > self.max_recording_seconds:
            time.sleep(1)
            recorded_time += 1
            self.timer -= 1
        self.camera.split_recording(self.delayed_recording_stream, splitter_port=2)
        if self.storage_option != "local":
            print("Sending recording to {}".format(self.storage_option))
            #threading.Thread(target=self.sender.send_recording, args=(file_path,)).start()