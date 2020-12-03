import cv2
import threading
import numpy as np
import urllib.request
import json
import socket

#TODO: change to localhost!
stream_url = "http://192.168.178.207:8000/stream.mjpg"

# Getting private data from 'data.json'
file = open('data.json')
stored_data = json.loads(file.read())
username = stored_data["username"]
password = stored_data["password"]
file.close()
current_frame = None
current_lowres_frame = None
motion_sensitivity = 50 # Higher number = less detection

def login():
    try:
        # create a password manager
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, stream_url, username, password)
        handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        opener = urllib.request.build_opener(handler)
        opener.open(stream_url)
        urllib.request.install_opener(opener)
        print("Camera login succeeded.")
        return True
    except:
        print("Camera login failed.")
        return False

# Receives the live video feed from the camera.
def recv_stream():
    global current_frame, current_lowres_frame
    # start streaming
    stream = urllib.request.urlopen(stream_url)
    bytes = b''
    while True:

        bytes += stream.read(1024)
        a = bytes.find(b'\xff\xd8')
        b = bytes.find(b'\xff\xd9')
        if a != -1 and b != -1:
            jpg = bytes[a:b + 2]
            bytes = bytes[b + 2:]
            i = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            # Resize the low-res image for faster detection.
            #TODO: make low res resolution changable.
            lowres_i = cv2.resize(i, (640, 480), interpolation = cv2.INTER_AREA)
            current_lowres_frame = lowres_i
            current_frame = i
            if cv2.waitKey(1) == 27:
                break

    print("Loop Broke")
    exit(0)


def detect_motion():
    while True:
        try:
            current_lowres_frame.any()
            break
        except:
            continue

    print("Detector started.")

    start_frame = cv2.cvtColor(current_lowres_frame, cv2.COLOR_BGR2GRAY)
    while True:
        next_frame = cv2.cvtColor(current_lowres_frame, cv2.COLOR_BGR2GRAY)

        #TODO: Show frames for testing.
        # cv2.imshow("Resized image", next_frame)
        # cv2.waitKey(1)

        frame_difference = cv2.absdiff(next_frame, start_frame)
        thresh = cv2.threshold(frame_difference, motion_sensitivity, 255, cv2.THRESH_BINARY)[1]
        start_frame = next_frame

        if thresh.sum() > 100:
            print("movement detected")
        else:
            pass


if __name__ == "__main__":
    if login():
        recv_thread = threading.Thread(target=recv_stream).start()
        detect_thread = threading.Thread(target=detect_motion).start()