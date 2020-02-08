import socket
import threading
import datetime
import time
import os

video_output_folder = "C:/Users/Ruud Brouwers/Desktop/recordings/"
max_storage = 0.15 # In Gb


# Sets up the socket and accepts clients.
def main():
    host = '192.168.178.129'
    port = 5000

    s = socket.socket()
    s.bind((host,port))
    s.listen(5)
    print("Recording Receiver started.")
    # Start making room for the video's be saved.
    threading.Thread(target=make_room, daemon=True).start()

    while True:
        c, addr = s.accept()
        print(f"Receiving recording from {addr}")
        threading.Thread(target=recvfile, args=(c,)).start()


# Receives files from client 's'.
def recvfile(s):
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


# Makes room for video's is there isn't enough.
def make_room():
    while True:
        # Convert Gb to b.
        max_folder_size = 1000000000*max_storage
        file_dict = {}

        # Calculates the size of a folder and populates file_dict.
        def calc_folder_size(path):
            size = 0
            for dirpath, dirs, files in os.walk(path):
                for f in files:
                    fp = os.path.join(dirpath, f)
                    size += os.path.getsize(fp)
                    file_dict[fp] = os.path.getctime(fp)
                # Remove directories if they are empty, they might get empty because of deleting files to save storage.
                for dir in dirs:
                    if not os.listdir(os.path.join(dirpath, dir)):
                        os.rmdir(os.path.join(dirpath, dir))
            return size

        folder_size = calc_folder_size(video_output_folder)
        # Sort the files based on the ctime.
        files = sorted(file_dict.items(), key=lambda x: x[1])

        # Delete the oldest file as long as there is too little storage left.
        while folder_size >= max_folder_size:
            deleted_size = os.path.getsize(files[0][0])
            os.remove(files[0][0])
            del files[0]
            folder_size -= deleted_size
            print("File ", files[0][0], " Deleted because there wasn't enough space.")
        time.sleep(10)


if __name__ == "__main__":
    main()

