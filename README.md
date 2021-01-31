
*NOTE: Legacy versions are moved to the 'legacy' directory*

# Raspberry Pi security camera system.

A Raspberry Pi camera system with a live video feed, motion detection system, H.264 mp4 recording capabilities and a storage management system with support for remote storage. <br>
The recorder supports pre-motion frame recording and no internet environments (e.g. Wildlife cameras). 

Confirmed working on Raspberry Pi 3b, 3b+, 4. Other versions will probably work, but they haven't been tested.


### Features


| Feature       |                       |
| ------------- |:-------------                                                                                                       |
| - Live low-bandwidth **H.264 Streaming** to a local web page.          |       
| - Advanced **motion detection** system that **records H.264 .mp4 videos** when motion is detected.               |
| - Even frames from before the motion triggering event are recorded, so everything will be on video.              |
| - Detection sensitivity, recording length, and much more is all easily user configurable.           |
| - Storage management system that **automatically removes the oldest recordings when the storage is almost full.**         |
| - Recordings can be sent to a separate storage device on the network.          |
| - As long as local storage is used, the camera doesn't require an internet connection. So it **can be used as a wildlife camera.**          |
| - Support for **multiple cameras**.          |
| - The recordings and the live stream can be viewed from a Django web page.       |


### Installation guide
- [Install the Raspberry Pi OS on your Raspberry Pi.](https://www.raspberrypi.org/software/)
*On the Raspberry Pi:*
- Connect the camera and enable it in the `sudo raspi-config` menu.
- Install OpenCV by running the following commands:
  - `sudo apt update`
  - `sudo apt install python3-opencv`
  - To verify the installation, import the cv2 module and print the OpenCV version:
    - `python3 -c "import cv2; print(cv2.__version__)"`
  - If this outputs a version higher or equal to `3.0.0` you are good to go.
- [Install ffmpeg with h.264 support](http://jollejolles.com/installing-ffmpeg-with-h264-support-on-raspberry-pi/).
- Clone this repository (You might need to install git first: `sudo apt install git`):
  - `cd ~`
  - `git clone https://github.com/Ruud14/SecurityCamera.git`
  
### How to run
- Assuming you are in the cloned repository directory, **you can run the full script by running `python3 main.py`**. 
- If the default settings don't fit your needs, you should follow the *configuration guide* below.
- Stream:
    - The live stream can be accessed on `http://<local_pi_ip>:8000/index.html` as long as `streamer_active` is set to `true` in the configuration file. Don't forget to replace `<local_pi_ip>` with the local IP address of your Raspberry Pi.
- Storage:
    - If `storage_option` is set to `local` (default), the recordings will be stored in the `local_recordings_output_path` directory (assuming `recorder_active` is set to `true`).
    - If `storage_option` is set to be the IP address of another storage device on the network, you should follow the *Remote storage receiver* guide below the *Configuration guide*. 
- Playback:
    - Recordings can be played using pretty much any modern video player or web browser (assuming `convert_h264_to_mp4` is set to `true`).
    - Recordings can also be watched using [this](https://github.com/Ruud14/Django-Camera-View-And-Playback) Django web page. (assuming `convert_h264_to_mp4` is set to `true`).
- Run at startup:
    - Automatically running `main.py` at startup can be achieved with i.a [chronjobs](https://nl.wikipedia.org/wiki/Cronjob).


### Configuration guide

The configuration of the camera can be changed in the `config.json` file, which looks like this by default:

```json
{
 "streamer_active": true,
 "recorder_active": true,

 "camera_resolution": "1600x1200",
 "camera_fps": 15,
 "camera_vFlip": false,
 "camera_hFlip": false,
 "camera_denoise": true,
 "annotate_time": true,

 "stream_resolution": "1120x840",

 "detection_resolution": "64x48",
 "detector_motion_threshold": 20,
 "record_seconds_before_motion": 5,
 "record_seconds_after_motion": 12,
 "max_recording_seconds": 600,
 "temporary_local_recordings_output_path": "./temp_recordings/",

 "convert_h264_to_mp4": true,
 "ffmpeg_path": "/usr/local/bin/ffmpeg",

 "storage_option": "local",

 "local_recordings_output_path": "./recordings/",
 "max_local_storage_capacity": 25
}
```



| Name | Description | Type | Required |  Default value |
|---|---|---|---|---|
|  `streamer_active` |  Determines if the camera can be looked at via `http://<local_pi_ip>:8000/index.html`.  |  Boolean | Yes  | `true`  |
|  `recorder_active` |  Determines if the camera will start recording when there is motion.  |  Boolean | Yes  | `true`  |
|  `camera_resolution` |  The resolution of the camera. This resolution **can not be lower than `stream_resolution` and/or `detection_resolution`.** **Supported resolution and frame rate combinations can be found [here]([https://picamera.readthedocs.io/en/release-1.13/fov.html#sensor-modes](https://picamera.readthedocs.io/en/release-1.13/fov.html#sensor-modes)).**   |  String | Yes  | `"1600x1200"`  |
|  `camera_fps` |  The frame rate of the camera. **Supported resolution and frame rate combinations can be found [here]([https://picamera.readthedocs.io/en/release-1.13/fov.html#sensor-modes](https://picamera.readthedocs.io/en/release-1.13/fov.html#sensor-modes)).**  |  Integer | Yes  | `15`  |
|  `camera_vFlip` |  Determines if the camera is flipped vertically.  |  Boolean | Yes  | `false`  |
|  `camera_hFlip` |  Determines if the camera is flipped horizontally.  |  Boolean | Yes  | `false`  |
|  `camera_denoise` |  Determines if noise reduction is active.  |  Boolean | Yes  | `true`  |
|  `annotate_time` |  Determines if the current date and time will be shown in the video.  |  Boolean | Yes  | `true`  |
|  `stream_resolution` |  The resolution of the live stream. This resolution **can not be higher than `camera_resolution`**. **Try to use the same aspect ratio as `camera_resolution` e.g. 16:9 or 4:3.**  |  String | Only if `streamer_active` is set to `true`.  | `"1120x840"`  |
|  `detection_resolution` |  The resolution at which motion detection is happening. **This should be a really low resolution to make it less CPU intensive.** **Try to use the same aspect ratio as `camera_resolution` e.g. 16:9 or 4:3.**  |  String | Only if `recorder_active` is set to `true`.  | `"64x48"`  |
|  `detector_motion_threshold` |  Threshold for detecting motion. The higher this number, the less motion is detected.  |  Integer | Only if `recorder_active` is set to `true`.  | 20 |
|  `record_seconds_before_motion` |  The amount of seconds that will be recorded before motion is detected.  |  Integer | Only if `recorder_active` is set to `true`.  | 5 |
|  `record_seconds_after_motion` |  The amount of seconds that will be recorded after motion. If there is more motion detected within `record_seconds_after_motion` seconds after the first motion is detected, it will continue recording until no more motion is detected or `max_recording_seconds` is exceeded.  |  Integer | Only if `recorder_active` is set to `true`.  | 12 |
|  `max_recording_seconds` |  The maximum duration of a recording in seconds.  |  Integer | Only if `recorder_active` is set to `true`.  | 600 |
|  `temporary_local_recordings_output_path` |  The directory where parts of recordings will be temporarily stored.  |  String | Only if `recorder_active` is set to `true`.  | `./temp_recordings/` |
|  `convert_h264_to_mp4` |  Determines whether or not the .h264 recordings will be converted to .mp4.  |  Boolean | Only if `recorder_active` is set to `true`.  | `true` |
|  `ffmpeg_path` |  Path to the the ffmpeg executable. The default value will most likely be the right path. If not, you can find the correct path using the `whereis ffmpeg` command.  |  String | Only if `convert_h264_to_mp4` is set to `true`.  | `/usr/local/bin/ffmpeg` |
|  `storage_option` |  Determines how your recordings will be stored. Use the local IP address of a local storage device on which `file_receiver.py` is running for remote storage e.g. `192.168.x.x`. Use `local` to store all recordings locally in the `local_recordings_output_path` directory. |  String | Only if `recorder_active` is set to `true`.  | `local` |
|  `local_recordings_output_path` |  The directory where recordings will be stored. |  String | Only if `storage_option` is set to `local`.  | `./recordings/` |
|  `max_local_storage_capacity` |  The maximum storage capacity that the recordings can occupy in Gigabytes. If this value is about to be exceeded, the oldest recordings will be removed. |  Integer | Only if `storage_option` is set to `local`.  | `25` |

### Remote storage receiver

**This part is only necessary for users that want to use remote storage!**

If you want your recordings to be stored on another storage device on the network, you should do the following: <br>
<br>
On the Raspberry Pi Camera:
- In `config.json`:
    -  Change the value of `storage_option` to the local IP address of the storage device e.g. `192.168.x.x.`
 
On the Storage device:
- Clone the contents of the `recordings_receiver` directory.
- Run `python3 recordings_receiver.py`. 
- The receiver can be configured in `config.json` which looks something like this:
```json
{
  "recordings_output_path": "./recordings/",
  "max_storage_capacity": 25
}
```
The values can be changed according to the table below:

| Name | Description | Type | Required |  Default value |
|---|---|---|---|---|
|  `recordings_output_path` |  The directory where recordings will be stored. |  String | Yes  | `./recordings/` |
|  `max_storage_capacity` |  The maximum storage capacity that the recordings can occupy in Gigabytes. If this value is about to be exceeded, the oldest recordings will be removed. |  Integer | Yes  | `25` |

- Automatically running `recordings_receiver.py` at startup can be achieved with i.a [chronjobs](https://nl.wikipedia.org/wiki/Cronjob).


### Additional info
If you are having trouble installing or configuring, feel free to e-mail me! <br><br>
If you come across any bugs or want to see a new feature, please let me know [here](https://github.com/Ruud14/SecurityCamera/issues).

