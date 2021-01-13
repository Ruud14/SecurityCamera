import datetime
import subprocess
import threading
import time
import os

stored_data = None


# Class that handles the recording.
class Recorder:
    def __init__(self, camera, sender, video_output_folder="./recordings/", record_seconds_after_movement=12, max_recording_seconds=300, storage_option='local'):
        self.camera = camera
        self.video_output_folder = video_output_folder
        self.record_seconds_after_movement = record_seconds_after_movement
        self.max_recording_seconds = max_recording_seconds
        self.storage_option = storage_option
        self.timer = 0
        self.sender = sender

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
        # process = subprocess.Popen(
        #     ['/usr/local/bin/ffmpeg', '-use_wallclock_as_timestamps', '1', '-i', 'http://{}:{}@localhost:8000/delayed_stream.mjpg'.format(*self.credentials), '-an',
        #      '-vcodec', 'copy', "{}".format(output_file_path)], stdin=subprocess.PIPE)
        #
        # threading.Thread(target=self._start_countdown, args=(process, output_file_path,), daemon=True).start()

    # Starts counting down from record_seconds_after_movement after movement is detected.
    # Stop recording if the timer gets to 0.
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