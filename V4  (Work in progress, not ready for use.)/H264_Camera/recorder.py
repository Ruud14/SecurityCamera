import datetime
import subprocess
import threading
import time
import os
from picamera import PiCamera, PiCameraCircularIO

stored_data = None


# Class that handles the recording.
class Recorder:
    def __init__(self, camera, sender, h264_args, video_output_folder="./recordings/", record_seconds_after_movement=12,
                 max_recording_seconds=300, storage_option='local', delayed_seconds=5):
        self.camera = camera
        self.sender = sender
        self.h264_args = h264_args
        self.video_output_folder = video_output_folder
        self.record_seconds_after_movement = record_seconds_after_movement
        self.max_recording_seconds = max_recording_seconds
        self.storage_option = storage_option
        self.timer = 0
        self.delayed_seconds = delayed_seconds

        # Make sure PiCameraCircularIO contains at least 20 seconds of footage. Since this is the minimum for it work.
        if delayed_seconds > 20:
            delayed_storage_length_seconds = delayed_seconds
        else:
            delayed_storage_length_seconds = 20
        # Create the delayed frames stream.
        self.delayed_recording_stream = PiCameraCircularIO(self.camera, seconds=delayed_storage_length_seconds)
        # For some reason the PiCameraCircularIO has to be on splitter_port 1. Splitter port 2 or 3 doesn't work.
        self.camera.start_recording(self.delayed_recording_stream, splitter_port=1, **h264_args)

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
        # Create the filename and path.
        current_time_string = str(datetime.datetime.now())[11:13] + "-" + str(datetime.datetime.now())[14:16] \
                              + '-' + str(datetime.datetime.now())[17:19]
        output_file_name = os.path.join(self.video_output_folder, current_time_string)
        print('Started recording '+output_file_name)

        # record the frames "after" motion
        self.camera.split_recording(output_file_name+'_after.h264', splitter_port=1, seconds=10)
        # Write the 10 seconds "before" motion to disk as well
        self.delayed_recording_stream.copy_to(output_file_name+'_before.h264', seconds=self.delayed_seconds)
        # Clear the delayed recording stream.
        self.delayed_recording_stream.clear()

        threading.Thread(target=self._start_countdown, args=(output_file_name,), daemon=True).start()

    # Starts counting down from record_seconds_after_movement after movement is detected.
    # Stop recording if the timer gets to 0.
    def _start_countdown(self, output_file_name):
        self.timer = self.record_seconds_after_movement
        recorded_time = 0
        while self.timer > 0 and not recorded_time > self.max_recording_seconds:
            time.sleep(1)
            recorded_time += 1
            self.timer -= 1
        # split the recording back to the delayed frames stream.
        self.camera.split_recording(self.delayed_recording_stream, splitter_port=1)
        # Merge the two recordings.
        self._merge_recordings(output_file_name)
        # Put the h264 recording into an mp4 container.
        self._put_in_mp4_container(output_file_name)

        if self.storage_option != "local":
            print("Sending {} to {}".format(output_file_name, self.storage_option))
            # threading.Thread(target=self.sender.send_recording, args=(file_path,)).start()

    # Merge the two h264 recordings and delete the old h264 files.
    def _merge_recordings(self, output_file_name):
        with open(output_file_name+"_before.h264", 'rb') as before:
            with open(output_file_name+"_after.h264", 'rb') as after:
                with open(output_file_name+".h264", 'ab') as new:
                    new.write(before.read())
                    new.write(after.read())
        # Remove the separate files.
        try:
            os.remove(output_file_name+"_before.h264")
            os.remove(output_file_name+"_after.h264")
        except Exception as e:
            print(e)

    # Put the h264 recording into an mp4 container.
    def _put_in_mp4_container(self, output_file_name):
        # ffmpeg -i "before.h264" -c:v copy -f mp4 "myOutputFile.mp4"
        subprocess.Popen(['ffmpeg', '-i', '{}'.format(output_file_name+".h264"), '-c:v', 'copy', '-f',
                          'mp4', '{}'.format(output_file_name+".mp4")], stdin=subprocess.PIPE)
        # Remove h264 file
        try:
            os.remove(output_file_name + ".h264")
        except Exception as e:
            print(e)