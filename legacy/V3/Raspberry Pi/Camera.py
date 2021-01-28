import time
import threading
import datetime
import os
import subprocess
import socket


class Camera:
    # ------------- Values you might want to change ----------------
    video_output_folder = "/home/pi/recordings/"
    record_seconds_after_movement = 10
    max_recording_time = 300    # in seconds
    server_ip = '192.168.178.129'
    transfer_port = 5005
    message_port = 5006

    # --------------------------------------------------------------

    timer = 0
    detected_motion = False
    is_connected = False

    def __init__(self,url,id,up):
        self.ip = "192.168.178.178"
        self.url = url
        self.id = id
        self.is_connected = True
        self.username = up[0]
        self.password = up[1]
        record_thread = threading.Thread(target=self.recv_msg).start()

    # Starts the recording
    def start_recording(self):
        current_time = str(datetime.datetime.now())[11:13]+"-"+str(datetime.datetime.now())[14:16]+'-'+str(datetime.datetime.now())[17:19]
        output_filepath = os.path.join(self.video_output_folder, current_time+".mp4")

        proc = subprocess.Popen(['ffmpeg', '-i', f'http://{self.username}:{self.password}@localhost:8000/delayed_stream.mjpg', '-an', '-vcodec', 'copy', f"{output_filepath}"], stdin=subprocess.PIPE)
        # libx262, but there was something wrong with my ffmpeg so this didn't work for me.
        #proc = subprocess.Popen(['ffmpeg', '-i', f'http://{self.username}:{self.password}@localhost:8000/delayed_stream.mjpg', '-an', '-pix_fmt', 'yuv420p', '-b:v', '4000k', '-c:v', 'libx264', f"{output_filepath}"], stdin=subprocess.PIPE)
        threading.Thread(target=self.start_countdown, args=(proc,output_filepath,), daemon=True).start()

    # Checks for incoming request to start the recording.
    def recv_msg(self):
        s = socket.socket()
        s.bind((self.ip, self.message_port))
        s.listen(5)
        print("Message Receiver started.")

        while True:
            c, addr = s.accept()
            msg = c.recv(1024).decode()
            if msg.startswith("record"):
                # Reset the timer
                if self.timer == 0:
                    self.start_recording()
                self.timer = self.record_seconds_after_movement

    # Starts counting down from record_seconds_after_movement after movement is detected.
    def start_countdown(self, proc, filepath):
        self.timer = self.record_seconds_after_movement
        print("Started Recording")
        recorded_time = 0
        while self.timer > 0 and not recorded_time > self.max_recording_time:
            time.sleep(1)
            recorded_time += 1
            self.timer -= 1
        proc.communicate(b'q')
        time.sleep(1)
        proc.terminate()
        proc.kill()
        print("Stopped Recording")
        self.send_recording(filepath)

    # Sends the recorded file to server and deletes the file.
    def send_recording(self, filepath):
        if os.path.isfile(filepath):
            print(f"Sending Recording {filepath} to server.")
            s = socket.socket()
            s.settimeout(5)
            try:
                s.connect((self.server_ip, self.transfer_port))
            except:
                print("Sending recording failed, Still removing the recording to prevent storage from getting full.")
                os.remove(filepath)
                return
            s.settimeout(None)
            s.send(("EXISTS" + str(os.path.getsize(filepath))).encode())
            print("FileSize: ",str(os.path.getsize(filepath)).encode())
            userResponse = s.recv(1024)
            userResponse = userResponse.decode()
            if userResponse.startswith('OK'):
                with open(filepath, 'rb') as f:
                    bytesToSend = f.read(4096)
                    s.send(bytesToSend)
                    while bytesToSend != b"":
                        bytesToSend = f.read(4096)
                        s.send(bytesToSend)
            s.close()
            os.remove(filepath)
            print("File Removed")




