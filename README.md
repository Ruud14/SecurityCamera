# Raspberry Pi (Zero W) security camera system.

Project status: finished, but nowhere near perfect.

**Raspberry Pi Zero W security camera system.**

Script that sends a video feed from the Raspberry Pi over the network and starts recording when there is motion. The recordings will be saved and removed when the storage gets full. 
The camera and the recordings can be looked at using a Django website  (https://github.com/Ruud14/Django-Camera-View-And-Playback). This feature only works with version 3. Version 3 also has a nice feature where the recording always contains the a couple of frames from before the action happened that triggered the recording. 

![image](https://i.imgur.com/9pVfhrq.png)
Schematic of version 3.

Every version has its own advantages and disadvantages but **I strongly recommend you use version 2 or 3 since they are faster and are way easier to use. Version 3 isn't always better than version 2 though. It just depends on your needs.**

| Version       | Advantages                                            | Disadvantages                                                                     |
| ------------- |:-------------                                         | -----                                                                             |
| V1            | - Requires less dependencies.                         | **- Relatively slow (low fps).**                                                  |
|               | - Over raw tcp instead of http.                       | - Stream is more difficult to view.                                               |
| V2            | - Requires less dependencies.                         | - Requires more processing power on the server.                                   |
|               | - Requires less processing power on the Rb Pi.        | **- Recording fps depends on internet speed.**                                    |
| V3            | - Higher frame rate recordings.                       | - Requires FFMPEG to be installed.                                                |  
|               | **- Recording fps isn't affected by internet speed.** |                                                                                   |  
|               | **- Also records frames that happened before there the motion got detected.** |                                                                                   |  
|               | Stores the recordings in h264 format for easier playback and less storage occupation. |                                                                                   |  


### _VERSION 1_
In this version the Raspberry pi sends the camera feed to the server frame by frame using raw tcp sockets. The server receives these frames and detects motion in them. When it does detect motion it starts the recording.
**The main disadvantage here is that it is slow and because sending frame after frame requires a lot of processing power.**

**How to use:**
- Get yourself a Raspberry pi and a (Night Vision IR) camera module.
- Install an os and python3 + openCV.
- Put the `Raspberry Pi.py` script on your Raspberry pi.
- enable the camera in the `sudo raspi-config` menu.
- You might want the script start on boot. I achieved this using crontab.
- Make a file called `data.json` and put it in the same folder as your `Raspberry Pi.py`.
- In your `data.json` add `{"server_ip":"your_server_ip", "server_port": your_port_number, "secret_key": "your_made_up_key"}` and change the values.
- In `Raspberry Pi.py` in the `setup` function change `/home/pi/Scripts/Camera/data.json` to the file location of your `data.json`.
- Put the `CameraReceiver.py` and `Camera.py` on your server/host machine.
- Also add that same `data.json` file from before to the folder your `CameraReceiver.py` is in.
- In `Camera.py` in the `Camera` class change `video_output_folder` from `.\\Recordings\\` to whatever path you want your video's to be stored in.
- In `CameraReceiver.py` in the `__init__` method change `file = open('data.json')` to the file location of your `data.json`.
- You might want to change the `camera_count` to the amount of camera's you're using. (The value of `camera_count` can be more but can't be less.)
- If your host machine's os has a GUI you might want to enable `cv2.imshow("Frame",frame_data)` in the `recv_stream` method.
- If you want to use this with a django webpage you'd want to get the content of `django_views.py` and add it to your django `views.py`. You should also change `from .scripts.Cameras_Receiver import CameraReceiver` in `django_views.py` to `from PATH_TO_YOUR_CAMERASRECEIVERSCRIPT import CameraReceiver`.
- Enjoy

### _VERSION 2_

In this version the Raspberry pi hosts a little http site with the stream of the camera on it. The server then scrapes that site and grabs the video stream.
Whenever motion is detected in the video stream the server will start the recording. **The main disadvantage here is that the fps of the recording is slow when the internet connection is slow.**

**How to use:**
- Get yourself a Raspberry pi and a (Night Vision IR) camera module.
- Install an os and python3 + openCV.
- Put the `Raspberry Pi.py` script on your Raspberry pi.
- enable the camera in the `sudo raspi-config` menu.
- You might want the script start on boot. I achieved this using crontab.
- Make a file called `data.json` and put it in the same folder as your `Raspberry Pi.py`.
- In your `data.json` add `{"username":"pi", "password":"picamera"}`. You might want to change the values.
- In `Raspberry Pi.py` change `/home/pi/camera/Camera/data.json` to the file location of your `data.json`.
- Put the `CameraReceiver.py` and `Camera.py` scripts on your server/host machine.
- You might also want this script to start on boot, again I used crontab.
- Also add that same `data.json` file from before to the folder your `CameraReceiver.py` is in.
- In `Camera.py` in the `Camera` class change `video_output_folder` from `.\\Recordings\\` to whatever path you want your video's to be stored in.
- In `Camera.py` in the `Camera` class you can change `motion_sensitivity` to change the sensitivity for detecting motion.
- In `CameraReceiver.py` change `data.json` in `file = open('data.json')` to the file location of your `data.json`.
- In `use.py` change the ip address to the ip of your camera.
- Enjoy

### _VERSION 3_

In this version the Raspberry pi still hosts a little http site with the stream of the camera on it. 
It is different from version 2 because here the recording (after movement is detected) takes place on the Raspberry pi itself instead of on the server.
The movement is detected on the server side and the server then sends a message to the camera to start the recording.
After the recording is done the recording is sent to the server.
**The main advantages here are that the fps of the recording isn't affected by the internet speed and that it records frames that happen before there the motion was detected. So the action causing the camera to record will always be visible in the recording.** 

**How to use:**
- Get yourself a Raspberry pi and a camera module.

*On the Raspberry Pi:*
- Install an os and python3 + OpenCV + FFMPEG.
- Put everything from inside the `camera` folder on your Raspberry Pi.
- enable the camera in the `sudo raspi-config` menu.
- You might want the `HTTPServer.py` and `use.py` scripts to start on boot. I achieved this using crontab.
- Make a file called `data.json` and put it in the same folder as your `Camera.py`, `CameraReceiver.py`, `HTTPServer.py` and `use.py` (if there isn't one already).
- In your `data.json` add `{"username":"pi", "password":"picamera"}`. You might want to change the values.
- In `HTTPServer.py` change `/home/pi/scripts/data.json` to the file location of your `data.json`.
- In `CameraReceiver.py` change `data.json` in `file = open('data.json')` to the same location as in `HTTPServer.py`.
- In `Camera.py` in the `Camera` class change `video_output_folder` from `/home/pi/recordings/` to whatever path you want your video's to be stored in. (The recordings will get removed after sending it to the server.)
- In `Camera.py` change the `server_ip` to the ip address of your server/host.

*On the Server:*
- Put everything from inside the `server` folder on your server/host.
- In `FileReceiver.py` change the `host` in the `main` function to the same ip address as `server_ip` in `Camera.py` on your Raspberry pi.
- In `use.py` change the ip-address to the ip of your camera/Raspberry pi.
- Make a file called `data.json` and put it in the same folder as your `detector.py`, `CameraReceiver.py`, `FileReceiver.py` and `use.py` (if there isn't one already).
- In your `data.json` add the same content as in the `data.json` file of your Raspberry pi.
- In `detector.py` in the `Camera` class you can change `motion_sensitivity` to change the sensitivity for detecting motion.
- You might also want this script to start on boot, again I used crontab.
- Enjoy


### Additional info.

**What I learned:**
- My first time using a Raspberry pi.
- OpenCV in python.
- Use of struct (un)packing in python.
- Use of crontab in linux.
- Use of base64
- HTTP/MJPG streaming
- FFMPEG


Part of the script running on the raspberry pi in version 2 & 3 is based on [this project](https://github.com/pschmitt/docker-picamera).

This project assumes that the Raspberry Pi and the server/host are on the same network.

The os used on the raspberry pi is 'Raspbian Buster Lite'.
The OpenCV version used on the raspberry pi is '3.4.6'
The ffmpeg version used on the raspberry pi is 'git-2020-01-17-c95dfe5'
The python version used on the raspberry pi is 'Python 3.7.3'


