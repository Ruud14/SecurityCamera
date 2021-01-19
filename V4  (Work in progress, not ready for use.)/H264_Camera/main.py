from streamer import Streamer
from detector import Detector
from recorder import Recorder
from picamera import PiCamera
from sender import Sender
import socket
import json
import time
import sys
import os

# Maximum amount of attempts to connect to the internet.
# Exit if this is exceeded.
MAX_INTERNET_CONNECT_ATTEMPTS = 100
current_internet_connect_attempts = 0

# H262 configuration
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


# Checks there is internet connectivity.
def has_internet_connectivity(host="8.8.8.8", port=53):
    try:
        socket.socket().connect((host, port))
        return True
    except socket.error:
        print("No internet connectivity could be established. Trying again in a second.")
        return False


# Returns the full file path of the script.
def get_exec_dir():
    abspath = os.path.abspath(__file__)
    directory_name = os.path.dirname(abspath)
    return directory_name


# Run if this script is run on its own.
if __name__ == '__main__':
    # Get the path of the configuration file.
    if len(sys.argv) >= 2:
        config_file_path = sys.argv[1]
    else:
        config_file_path = os.path.join(get_exec_dir(), 'config.json')

    # Exit if the configuration file doesn't exist.
    if not os.path.isfile(config_file_path):
        raise FileNotFoundError("The configuration file can't be found at {}. "
                                "Use 'python3 main.py <PATH_TO_CONFIG_FILE>' "
                                "to use a configuration file from a different directory.".format(config_file_path))

    # Wait for internet connectivity.
    while not has_internet_connectivity():
        time.sleep(1)
        current_internet_connect_attempts += 1
        if current_internet_connect_attempts > 100:
            raise socket.error("No internet connection could be established "
                               "within the first {} seconds of running.".format(MAX_INTERNET_CONNECT_ATTEMPTS))

    # Get the configuration data from the config file.
    with open(config_file_path) as file:
        stored_data = json.loads(file.read())

    motion_threshold = stored_data["detector_motion_threshold"]
    delayed_seconds = stored_data["delayed_seconds"]
    record_resolution = stored_data["record_resolution"]
    stream_resolution = stored_data["stream_resolution"]
    stream_fps = stored_data["stream_fps"]
    recordings_output_path = stored_data['local_recordings_output_path']
    path_to_ffmpeg = stored_data['path_to_ffmpeg']
    record_seconds_after_movement = stored_data['record_seconds_after_movement']
    max_recording_seconds = stored_data['max_recording_seconds']
    storage_option = stored_data['storage_option']
    camera_vFlip = stored_data['camera_vFlip']
    camera_HFlip = stored_data['camera_hFlip']
    camera_denoise = stored_data['camera_denoise']
    detection_resolution = tuple(map(int, stored_data['detection_resolution'].split("x")))

    # Create and configure the camera.
    camera = PiCamera(resolution=record_resolution, framerate=stream_fps)
    camera.vflip = camera_vFlip
    camera.hflip = camera_HFlip
    camera.video_denoise = camera_denoise

    sender = Sender(storage_ip=storage_option)

    recorder = Recorder(camera=camera,
                        sender=sender,
                        h264_args=h264_stream_and_record_args,
                        video_output_folder=recordings_output_path,
                        record_seconds_after_movement=record_seconds_after_movement,
                        max_recording_seconds=max_recording_seconds,
                        storage_option=storage_option,
                        delayed_seconds=delayed_seconds,
                        path_to_ffmpeg=path_to_ffmpeg)

    detector = Detector(camera=camera,
                        recorder=recorder,
                        motion_threshold=motion_threshold,
                        detection_resolution=detection_resolution)

    streamer = Streamer(camera=camera,
                        streaming_resolution=stream_resolution,
                        h264_args=h264_stream_and_record_args,
                        fps=stream_fps,)
    detector.start()
    streamer.start()


