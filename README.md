# Raspberry Pi Zero W security camera system.

Project status: not finished

**Raspberry Pi Zero W security camera system.**
<<<<<<< HEAD
Script that sends a video feed from the Raspberry Pi over the network and starts recording when there is motion.
You can display this live video feed in a django view, and the recordings can be saved.

Every version has its own advantages and disadvantages but **I strongly recommend you use version 2 or 3 since they are faster and are way easier to use. Version 3 isn't always better than version 2 though. It just depends on your needs.**

| Version       | Advantages                                            | Disadvantages                                                                     |
| ------------- |:-------------                                         | -----                                                                             |
| V1            | - Requires less dependencies.                         | **- Relatively slow (low fps).**                                                  |
|               | - Over raw tcp instead of http.                       | - Stream is more difficult to view.                                               |
| V2            | - Requires less dependencies.                         | - Requires more processing power on the server.                                   |
|               | - Requires less processing power on the Rb Pi.        | **- Recording fps depends on internet speed.**                                    |
| V3            | - Higher frame rate recordings.                       | - Requires FFMPEG to be installed.                                                |
|               | - Requires less processing power on the server.       | - Requires more processing power on the Raspberry Pi (not too much though).       |    
|               | **- Recording fps isn't affected by internet speed.** |                                                                                   |  




### _VERSION 1_
In this version the Raspberry pi sends the camera feed to the server frame by frame using raw tcp sockets. The server receives these frames and detects motion in them. When it does detect motion it starts the recording.
**The main disadvantage here is that it is slow and because sending frame after frame requires a lot of processing power.**

**How to use:**
- Get yourself a Raspberry pi and a (Night Vision IR) camera module.
- Install an os and python3 + OpenCV.
=======
Script that sends a live video feed from the raspberry pi to the server.
the server processes the data, shows it on a django web page and saves the video stream when motion gets detected.

**I strongly recommend you use version 2 since it is faster and is way easier to use.**

### _VERSION 1_


**How to use:**
- Get yourself a Raspberry pi and a (Night Vision IR) camera module.
- Install an os and python3 + openCV.
>>>>>>> 1a8a596c1df1d8e66eee2b255d221fe2e337e382
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
<<<<<<< HEAD

In this version the Raspberry pi hosts a little http site with the stream of the camera on it. The server then scrapes that site and grabs the video stream.
Whenever motion is detected in the video stream the server will start the recording. **The main disadvantage here is that the fps of the recording is slow when the internet connection is slow.**

**How to use:**
- Get yourself a Raspberry pi and a (Night Vision IR) camera module.
- Install an os and python3 + OpenCV.
=======
The raspberry pi script of this version is based on this project https://github.com/pschmitt/docker-picamera from https://github.com/pschmitt

**How to use:**
- Get yourself a Raspberry pi and a (Night Vision IR) camera module.
- Install an os and python3 + openCV.
>>>>>>> 1a8a596c1df1d8e66eee2b255d221fe2e337e382
- Put the `Raspberry Pi.py` script on your Raspberry pi.
- enable the camera in the `sudo raspi-config` menu.
- You might want the script start on boot. I achieved this using crontab.
- Make a file called `data.json` and put it in the same folder as your `Raspberry Pi.py`.
<<<<<<< HEAD
- In your `data.json` add `{"username":"pi", "password":"picamera"}`. You might want to change the values.
- In `Raspberry Pi.py` change `/home/pi/camera/Camera/data.json` to the file location of your `data.json`.
- Put the `CameraReceiver.py` and `Camera.py` scripts on your server/host machine.
- You might also want this script to start on boot, again I used crontab.
- Also add that same `data.json` file from before to the folder your `CameraReceiver.py` is in.
- In `Camera.py` in the `Camera` class change `video_output_folder` from `.\\Recordings\\` to whatever path you want your video's to be stored in.
- In `CameraReceiver.py` change `data.json` in `file = open('data.json')` to the file location of your `data.json`.
- In `use.py` change the ip address to the ip of your camera.
- Enjoy

### _VERSION 3_

In this version the Raspberry pi still hosts a little http site with the stream of the camera on it. 
It is different from version 2 because here the recording (after movement is detected) takes place on the Raspberry pi itself instead of on the server.
**The main advantage here is that the fps of the recording isn't affected by the internet speed.** 

**How to use:**
- Get yourself a Raspberry pi and a camera module.
- Install an os and python3 + OpenCV + FFMPEG.
- Put the `Camera.py`, `CameraReceiver.py`, `HTTPServer.py` and `use.py` scripts on your Raspberry pi.
- enable the camera in the `sudo raspi-config` menu.
- You might want the `HTTPServer.py` and `use.py` scripts to start on boot. I achieved this using crontab.
- Make a file called `data.json` and put it in the same folder as your `Camera.py`, `CameraReceiver.py`, `HTTPServer.py` and `use.py`.
- In your `data.json` add `{"username":"pi", "password":"picamera"}`. You might want to change the values.
- In `HTTPServer.py` change `/home/pi/scripts/data.json` to the file location of your `data.json`.
- In `CameraReceiver.py` change `data.json` in `file = open('data.json')` to the same location as in `HTTPServer.py`.
- In `Camera.py` in the `Camera` class change `video_output_folder` from `/home/pi/recordings/` to whatever path you want your video's to be stored in.
- In `Camera.py` change the `server_ip` to the ip address of your server/host.
- In `FileReceiver.py` change the `host` in the `main` function to the same ip address.
- Put the `FileReceiver.py` script on your server/host machine.
- You might also want this script to start on boot, again I used crontab.
- Enjoy


### Additional info.

=======
- In your `data.json` add `{"username":"pi", "password":"picamera"}` you might want to change the values, but you'll also have to do that in `CameraReceiver.py`.
- In `Raspberry Pi.py` change `/home/pi/camera/Camera/data.json` to the file location of your `data.json`.
- Put the `CameraReceiver.py` and `Camera.py` on your server/host machine.
- Also add that same `data.json` file from before to the folder your `CameraReceiver.py` is in.
- In `Camera.py` in the `Camera` class change `video_output_folder` from `.\\Recordings\\` to whatever path you want your video's to be stored in.
- In `CameraReceiver.py` change `file = open('data.json')` to the file location of your `data.json`.
- In `use.py` change the ip address to the ip of your camera.
- Enjoy

>>>>>>> 1a8a596c1df1d8e66eee2b255d221fe2e337e382
**What I learned:**
- My first time using a Raspberry pi.
- OpenCV in python.
- Use of struct (un)packing in python.
- Use of crontab in linux.
- Use of base64
- HTTP/MJPG streaming
<<<<<<< HEAD
- FFMPEG


Part of the script running on the raspberry pi in version 2 & 3 is based on this project https://github.com/pschmitt/docker-picamera from https://github.com/pschmitt

This project assumes that the Raspberry Pi and the server/host are on the same network.

The os used on the raspberry pi is 'Raspbian Buster Lite'.
The OpenCV version used on the raspberry pi is '3.4.6'
The ffmpeg version used on the raspberry pi is 'git-2020-01-17-c95dfe5'
The python version used on the raspberry pi is 'Python 3.7.3'
=======
>>>>>>> 1a8a596c1df1d8e66eee2b255d221fe2e337e382
