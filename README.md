# Raspberry Pi Zero W security camera system.

Project status: not finished

**Raspberry Pi Zero W security camera system.**
Script that sends a live video feed from the raspberry pi to the server.
the server processes the data, shows it on a django web page and saves the video stream when motion gets detected.

**I strongly recommend you use version 2 since it is faster and is way easier to use.**

### _VERSION 1_


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
The raspberry pi script of this version is based on this project https://github.com/pschmitt/docker-picamera from https://github.com/pschmitt

**How to use:**
- Get yourself a Raspberry pi and a (Night Vision IR) camera module.
- Install an os and python3 + openCV.
- Put the `Raspberry Pi.py` script on your Raspberry pi.
- enable the camera in the `sudo raspi-config` menu.
- You might want the script start on boot. I achieved this using crontab.
- Make a file called `data.json` and put it in the same folder as your `Raspberry Pi.py`.
- In your `data.json` add `{"username":"pi", "password":"picamera"}` you might want to change the values, but you'll also have to do that in `CameraReceiver.py`.
- In `Raspberry Pi.py` change `/home/pi/camera/Camera/data.json` to the file location of your `data.json`.
- Put the `CameraReceiver.py` and `Camera.py` on your server/host machine.
- Also add that same `data.json` file from before to the folder your `CameraReceiver.py` is in.
- In `Camera.py` in the `Camera` class change `video_output_folder` from `.\\Recordings\\` to whatever path you want your video's to be stored in.
- In `CameraReceiver.py` change `file = open('data.json')` to the file location of your `data.json`.
- In `use.py` change the ip address to the ip of your camera.
- Enjoy

**What I learned:**
- My first time using a Raspberry pi.
- OpenCV in python.
- Use of struct (un)packing in python.
- Use of crontab in linux.
- Use of base64
- HTTP/MJPG streaming
