import socket
import threading
import datetime
import time
import os
import sys
import json

# Maximum amount of attempts to connect to the internet.
# Exit if this is exceeded.
MAX_INTERNET_CONNECT_ATTEMPTS = 100
current_internet_connect_attempts = 0


# Returns the full file path of the script.
def get_exec_dir():
    abspath = os.path.abspath(__file__)
    directory_name = os.path.dirname(abspath)
    return directory_name


with open(os.path.join(get_exec_dir(),"config.json")) as file:
    stored_data = json.loads(file.read())
    video_output_folder = stored_data['recordings_output_path']
    max_storage = stored_data['max_storage_capacity']

# Change the slashes if the script is run on a windows device.
if sys.platform.startswith("win"):
    video_output_folder = video_output_folder.replace("/", "\\")


# Checks there is internet connectivity.
def has_internet_connectivity(host="8.8.8.8", port=53):
    try:
        socket.socket().connect((host, port))
        return True
    except socket.error:
        print("No internet connectivity could be established. Trying again in a second.")
        return False


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
    rec_dir_path = os.path.join(get_exec_dir(), video_output_folder, current_date)
    # Create a folder for the specific date if there isn't one already.
    if not os.path.isdir(rec_dir_path):
        os.mkdir(rec_dir_path)

    data = s.recv(4096)
    data = data.decode()
    if data.startswith("EXISTS"):
        file_name_container = data[6:261]
        file_name = file_name_container.replace("_", "")
        file_size = (data[261:])
        print("FileSize:", file_size)
        s.send(b'OK')
        file_path = os.path.join(get_exec_dir(), video_output_folder, current_date, file_name)
        f = open(file_path, 'wb')
        data = s.recv(4096)
        total_received = len(data)
        f.write(data)
        while total_received < float(file_size):
            data = s.recv(4096)
            total_received += len(data)
            f.write(data)
        f.close()
        print("download of {} Complete!".format(file_path))
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
                # Remove directories if they are empty, they might be empty because old recordings are deleted.
                for dir in dirs:
                    if not os.listdir(os.path.join(dirpath, dir)):
                        os.rmdir(os.path.join(dirpath, dir))
            return size

        folder_size = calc_folder_size(os.path.join(get_exec_dir(), video_output_folder))
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

    # Wait for internet connectivity.
    while not has_internet_connectivity():
        time.sleep(1)
        current_internet_connect_attempts += 1
        if current_internet_connect_attempts > 100:
            raise socket.error("No internet connection could be established "
                               "within the first {} seconds of running.".format(MAX_INTERNET_CONNECT_ATTEMPTS))

    main()
