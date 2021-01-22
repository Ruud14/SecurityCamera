import socket
import threading
import datetime
import time
import os
import sys
import json

with open("config.json") as file:
    stored_data = json.loads(file.read())
    video_output_folder = stored_data['video_output_folder']
    max_storage = stored_data['max_storage_capacity']

# Change the slashes if the script is run on a windows device.
if sys.platform.startswith("win"):
    video_output_folder = video_output_folder.replace("/", "\\")


# Sets up the socket and accepts clients.
def main():
    host = "0.0.0.0"
    port = 5005

    s = socket.socket()
    s.bind((host,port))
    s.listen(5)
    print("Recording Receiver started.")
    # Start making room for the video's be saved.
    threading.Thread(target=make_room, daemon=True).start()

    while True:
        c, addr = s.accept()
        print(f"Receiving recording from {addr}")
        threading.Thread(target=receive_recording, args=(c,)).start()


# Receives files from client 's'.
def receive_recording(s):
    current_date = str(datetime.date.today())
    # Create a folder for the specific date if there isn't one already.
    if not os.path.isdir(os.path.join(video_output_folder, current_date)):
        os.mkdir(os.path.join(video_output_folder, current_date))

    current_time = str(datetime.datetime.now())[11:13] + "-" + str(datetime.datetime.now())[14:16] + '-' + str(
        datetime.datetime.now())[17:19]

    data = s.recv(4096)
    data = data.decode()
    if data.startswith("EXISTS"):
        file_type_container = data[6:16]
        file_type = file_type_container.replace("_", "")
        file_size = (data[16:])
        print("FileSize:", file_size)
        s.send(b'OK')
        filepath = os.path.join(video_output_folder, current_date, current_time + ".{}".format(file_type))
        f = open(filepath, 'wb')
        data = s.recv(4096)
        total_received = len(data)
        f.write(data)
        while total_received < float(file_size):
            data = s.recv(4096)
            total_received += len(data)
            f.write(data)
        f.close()
        print("download Complete!")
    else:
        print("File does not exist!")
    s.close()


# Deletes old recordings if we're running out of storage capacity.
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
