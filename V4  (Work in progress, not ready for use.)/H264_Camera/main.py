from streamer import Streamer
from detector import Detector
from recorder import Recorder
from sender import Sender
import os
import json
from picamera import PiCamera

# TODO: put all this inside __main__
config_file_path = '/home/pi/scripts/pi-h264-to-browser/src/config.json'

with open(config_file_path) as file:
    stored_data = json.loads(file.read())

detection_sensitivity = stored_data["detection_sensitivity"]
delayed_seconds = stored_data["delayed_seconds"]
stream_resolution = stored_data["stream_resolution"]
stream_fps = stored_data["stream_fps"]
recordings_output_folder = stored_data['local_recordings_output_folder']
record_seconds_after_movement = stored_data['record_seconds_after_movement']
max_recording_seconds = stored_data['max_recording_seconds']
storage_option = stored_data['storage_option']
camera_vFlip = stored_data['camera_vFlip']
camera_HFlip = stored_data['camera_hFlip']
camera_denoise = stored_data['camera_denoise']
detection_resolution = tuple(map(int, stored_data['detection_resolution'].split("x")))
h264_stream_and_record_args = {
    'format': 'h264',
    #'bitrate': 25000000,
    'quality': 25,
    'profile': 'high',
    'level': '4.2',
    'intra_period': 15,
    'intra_refresh': 'both',
    'inline_headers': True,
    'sps_timing': True
}


# Change the execution directory of the script.
# This way we can use relative paths in the code.
def change_exec_dir():
    abspath = os.path.abspath(__file__)
    directory_name = os.path.dirname(abspath)
    os.chdir(directory_name)


# Run if this script is run on its own.
if __name__ == '__main__':
    change_exec_dir()

    # Create and configure the camera.
    camera = PiCamera(sensor_mode=4, resolution=stream_resolution, framerate=stream_fps)
    camera.vflip = camera_vFlip
    camera.hflip = camera_HFlip
    camera.video_denoise = camera_denoise

    sender = Sender(storage_ip=storage_option)

    recorder = Recorder(camera=camera,
                        sender=sender,
                        h264_args=h264_stream_and_record_args,
                        video_output_folder=recordings_output_folder,
                        record_seconds_after_movement=record_seconds_after_movement,
                        max_recording_seconds=max_recording_seconds,
                        storage_option=storage_option,
                        delayed_seconds=delayed_seconds)

    detector = Detector(camera=camera,
                        recorder=recorder,
                        sensitivity=detection_sensitivity,
                        detection_resolution=detection_resolution)

    streamer = Streamer(camera=camera,
                        h264_args=h264_stream_and_record_args,
                        fps=stream_fps,)
    detector.start()
    streamer.start()


