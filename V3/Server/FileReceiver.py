import socket
import threading
import datetime
import os

video_output_folder = "C:/Users/Ruud Brouwers/Desktop/recordings/"

# Sets up the socket and accepts clients.
def Main():
    host = '192.168.178.129'
    port = 5000

    s = socket.socket()
    s.bind((host,port))
    s.listen(5)
    print("Recording Receiver started.")

    while True:
        c, addr = s.accept()
        print(f"Receiving recording from {addr}")
        t = threading.Thread(target=RecvFile, args=(c,))
        t.start()

# Receives files from client 's'.
def RecvFile(s):
    current_date = str(datetime.date.today())
    # Create a folder for the specific date if there isn't one already.
    if not os.path.isdir(os.path.join(video_output_folder, current_date)):
        os.mkdir(os.path.join(video_output_folder, current_date))

    current_time = str(datetime.datetime.now())[11:13] + "-" + str(datetime.datetime.now())[14:16] + '-' + str(
        datetime.datetime.now())[17:19]
    filepath = os.path.join(video_output_folder, current_date, current_time + ".mp4")

    data = s.recv(4096)
    data = data.decode()
    if data.startswith("EXISTS"):
        filesize = (data[6:])
        print("FileSize:", filesize)
        s.send(b'OK')
        f = open(filepath, 'wb')
        data = s.recv(4096)
        totalRecv = len(data)
        f.write(data)
        while totalRecv < float(filesize):
            data = s.recv(4096)
            totalRecv += len(data)
            f.write(data)
        print("download Complete!")
    else:
        print("File does not exist!")
    s.close()


if __name__ == "__main__":
    Main()

