import os
import socket
import cv2
import json
import time
import struct
import threading
import base64


# This line was essential to get the VideoCapture to work. (Only on linux)
os.system("sudo modprobe bcm2835-v4l2")

s = socket.socket()
cap = cv2.VideoCapture(0)
# also change the resolution on the server side.
# 1080p
#cap.set(3,1920)
#cap.set(4,1080)
# 720p
cap.set(3,1280)
cap.set(4,720)
server_ip = None
server_port = None
secret_key = None
last_frame = None
connected = False

# setting all private variables
def setup():
    global server_ip, server_port, secret_key
    with open('/home/pi/Scripts/Camera/data.json') as file:
        stored_data = json.loads(file.read())
        server_ip = stored_data["server_ip"]
        server_port = stored_data["server_port"]
        secret_key = stored_data["secret_key"]


def connect_to_server():
    global connected
    # Attempts a connection to the server by sending the secret key.
    # 'pass' = permission to enter the secret key.
    # 'True' = the secret key was correct, connection established.
    # 'False' = the secret key was incorrect.
    connected = False
    while not connected:
        try:
            s.connect((server_ip,server_port))
        except socket.error:
            print("Can't connect to server.")
            return "Cant't connect to server"
        entered = False
        while not entered:
            try:
                msg = s.recv(1024).decode()
            except socket.error:
                print("Can't receive message from server.")
                return "Can't receive message from server."
            if msg == 'pass':
                s.send(secret_key.encode())
            elif msg == 'False':
                print("Wrong secret key, trying again.")
                s.close()
                break
            elif msg == 'True':
                entered = True
                connected = True
                print("Connected to server.")
                return True


# sends the live video feed to the server.
def send_stream():
    connection = True
    while connection:
        ret,frame = cap.read()
        if ret:
            # For me the camera was upside down so I had to rotate the frame by 180 degrees.
            (h, w) = frame.shape[:2]
            center = (w / 2, h / 2)
            M = cv2.getRotationMatrix2D(center, 180, 1.0)
            frame = cv2.warpAffine(frame, M, (w, h))

            # You might want to enable this while testing.
            # cv2.imshow('camera', frame)
            b_frame = pickle.dumps(frame)
            b_size = len(b_frame)
            try:
                s.sendall(struct.pack("<L", b_size) + b_frame)
            except socket.error:
                print("Socket Error!")
                connection = False

        else:
            print("Received no frame from camera.")
            break



# Gets the frame from the camera.
def get_frame():
    global last_frame
    while True:
        ret,frame = cap.read()
        time.sleep(0.02)
        if ret:
            # For me the camera was upside down, so I had to rotate the frame by 180 degrees.
            (h, w) = frame.shape[:2]
            center = (w / 2, h / 2)
            M = cv2.getRotationMatrix2D(center, 180, 1.0)
            frame = cv2.warpAffine(frame, M, (w,h))
            last_frame = frame
        else:
            print("Received no frame from the camera.")


# sends the live video feed to the server.
def send_stream():
    global connected
    connection = True
    while connection:
        if last_frame is not None:

            # You might want to uncomment these lines while testing.
            # cv2.imshow('camera', frame)
            # cv2.waitKey(1)
            frame = last_frame
            # Using the old method
            #b_frame = pickle.dumps(frame)

            encoded, buffer = cv2.imencode('.jpg', frame)
            b_frame = base64.b64encode(buffer)
            b_size = len(b_frame)
            try:
                s.sendall(struct.pack("<L", b_size) + b_frame)
            except socket.error:
                print("Socket Error!")
                connection = False
                connected = False
                s.close()
                return "Socket Error"
        else:
            return "Received no frame from camera"


setup()
iterations = 0
return_msg = ''
# Start retrieving frames from the camera.
get_frame_thread = threading.Thread(target=get_frame)
get_frame_thread.start()

while True:
    # Writing to log file, You might want to enable this while testing.
    #with open("/home/pi/logs/log.txt","a") as f:
        #f.write("Iteration "+str(iterations)+ str(return_msg)+"\n")
        #iterations+=1
    return_msg = connect_to_server()
    if return_msg == True:
        return_msg = send_stream()
    s.close()
    s = None
    s = socket.socket()
    time.sleep(10)

