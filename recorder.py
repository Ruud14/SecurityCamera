from picamera import PiCamera, PiCameraCircularIO
from general import get_exec_dir
import subprocess
import threading
import datetime
import time
import os


# Class that handles the recording.
class Recorder:
    def __init__(self, camera, storage, h264_args,
                 temporary_recordings_output_path="./temp_recordings/",
                 record_seconds_after_motion=12, max_recording_seconds=600,
                 record_seconds_before_motion=5, ffmpeg_path="/usr/local/bin/ffmpeg", convert_h264_to_mp4=True):
        self.camera = camera
        self.storage = storage
        self.h264_args = h264_args
        self.temporary_recordings_output_path = temporary_recordings_output_path
        self.record_seconds_after_motion = record_seconds_after_motion
        self.max_recording_seconds = max_recording_seconds
        self.timer = 0
        self.record_seconds_before_motion = record_seconds_before_motion
        self.ffmpeg_path = ffmpeg_path
        self.convert_h264_to_mp4 = convert_h264_to_mp4

        # Make sure PiCameraCircularIO contains at least 20 seconds of footage. Since this is the minimum for it work.
        if record_seconds_before_motion > 20:
            delayed_storage_length_seconds = record_seconds_before_motion
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
            self.timer = self.record_seconds_after_motion
            self._start_recording()
        else:
            self.timer = self.record_seconds_after_motion

    # Starts the recording.
    def _start_recording(self):
        # Create the filename and path.
        current_time_string = str(datetime.datetime.now())[11:13] + "-" + str(datetime.datetime.now())[14:16] \
                              + '-' + str(datetime.datetime.now())[17:19]
        if not os.path.isdir(os.path.join(get_exec_dir(), self.temporary_recordings_output_path)):
            os.mkdir(os.path.join(get_exec_dir(), self.temporary_recordings_output_path))
        output_file_name = os.path.join(get_exec_dir(), self.temporary_recordings_output_path, current_time_string)
        print('Started recording '+output_file_name)

        # record the frames "after" motion
        self.camera.split_recording(output_file_name+'_after.h264', splitter_port=1, seconds=10)
        # Write the 10 seconds "before" motion to disk as well
        self.delayed_recording_stream.copy_to(output_file_name+'_before.h264', seconds=self.record_seconds_before_motion)
        # Clear the delayed recording stream.
        self.delayed_recording_stream.clear()

        threading.Thread(target=self._start_countdown, args=(output_file_name,), daemon=True).start()

    # Starts counting down from record_seconds_after_movement after movement is detected.
    # Stop recording if the timer gets to 0.
    def _start_countdown(self, output_file_name):
        self.timer = self.record_seconds_after_motion
        recorded_time = 0
        while self.timer > 0 and not recorded_time > self.max_recording_seconds:
            time.sleep(1)
            recorded_time += 1
            self.timer -= 1
        # split the recording back to the delayed frames stream.
        self.camera.split_recording(self.delayed_recording_stream, splitter_port=1)
        # Merge the two recordings.
        file_path = self._merge_recordings(output_file_name)
        # Put the h264 recording into an mp4 container.
        if self.convert_h264_to_mp4:
            file_path = self._put_in_mp4_container(file_path)
        # Store the recording in the right place.
        self.storage.store(file_path)

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
        return output_file_name+".h264"

    # Put the h264 recording into an mp4 container.
    def _put_in_mp4_container(self, file_path):
        output_file_path = file_path.replace("h264", "mp4")
        # ffmpeg -i "before.h264" -c:v copy -f mp4 "myOutputFile.mp4"
        subprocess.call(['{}'.format(self.ffmpeg_path), '-i', '{}'.format(file_path), '-c:v', 'copy',
                         '-f', 'mp4', '{}'.format(output_file_path)], stdin=subprocess.PIPE)
        # Remove h264 file
        try:
            os.remove(file_path)
        except Exception as e:
            print(e)
        return output_file_path