import socket
import os


class Sender:
    def __init__(self, storage_ip):
        self.storage_ip = storage_ip
        self.transfer_port = 5005

    # Sends the recorded file to server and deletes the file.
    def send_recording(self, filepath):
        if os.path.isfile(filepath):
            print("Sending Recording {} to server.".format(filepath))
            s = socket.socket()
            s.settimeout(5)
            try:
                s.connect((self.storage_ip, self.transfer_port))
            except Exception as e:
                print(
                    "Sending recording failed,"
                    " Still removing the recording to prevent local storage from getting full. \n",
                    str(e))
                os.remove(filepath)
                return
            s.settimeout(None)
            s.send(("EXISTS" + str(os.path.getsize(filepath))).encode())
            print("FileSize: ", str(os.path.getsize(filepath)).encode())
            response = s.recv(1024)
            response = response.decode()
            if response.startswith('OK'):
                with open(filepath, 'rb') as f:
                    bytes_to_send = f.read(4096)
                    s.send(bytes_to_send)
                    while bytes_to_send != b"":
                        bytes_to_send = f.read(4096)
                        s.send(bytes_to_send)
            s.close()
            os.remove(filepath)
            print("File Removed")
        else:
            print(filepath + " Does not exist.")