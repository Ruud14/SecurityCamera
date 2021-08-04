from general import get_exec_dir
import threading
import datetime
import socket
import shutil
import time
import os


# Class responsible for storing the recordings. Either locally or on another device on the network.
class Storage:
    def __init__(self, storage_option='local', recordings_output_path='./recordings/', max_local_storage_capacity=5):
        self.storage_option = storage_option
        self.recordings_output_path = recordings_output_path
        self.max_local_storage_capacity = max_local_storage_capacity
        self.transfer_port = 5005
        # Start making room for the video's be saved.
        threading.Thread(target=self._make_room, daemon=True).start()

    def store(self, file_path):
        if self.storage_option == 'local':
            self._store_recording(file_path)
        else:
            self._send_recording(file_path)

    # Stores the recording locally.
    def _store_recording(self, file_path):
        current_date = str(datetime.date.today())
        file_name = file_path.split("/")[-1]
        if not os.path.isdir(os.path.join(get_exec_dir(), self.recordings_output_path)):
            os.mkdir(os.path.join(get_exec_dir(), self.recordings_output_path))

        rec_dir_path = os.path.join(get_exec_dir(), self.recordings_output_path, current_date)
        # Create a folder for the specific date if there isn't one already.
        if not os.path.isdir(rec_dir_path):
            os.mkdir(rec_dir_path)

        output_file_path = os.path.join(rec_dir_path, file_name)
        
        # Try moving the recording to the recordings directory. Delete file if this operation fails.
        try:
            shutil.move(file_path, output_file_path)
            print("Stored {} in local storage.".format(file_name))
        except Exception as e:
            os.remove(file_path)
            print("Removed {}. Could not be put into local storage.".format(file_name))


    # Sends the recorded file to server and deletes the file.
    def _send_recording(self, file_path):
        if os.path.isfile(file_path):
            file_name = file_path.split("/")[-1]
            if(len(file_name)) > 255:
                raise Exception("File name '{}' is too long. Max 255 characters".format(file_name))
            file_name_container = "_"*255  # 10 symbols
            file_name_container = file_name+file_name_container[len(file_name):]
            s = socket.socket()
            s.settimeout(5)
            try:
                s.connect((self.storage_option, self.transfer_port))
                print("Sending Recording {} to {}.".format(file_path, self.storage_option))
            except Exception as e:
                print(
                    "Sending recording failed,"
                    " Still removing the recording to prevent local storage from getting full. \n",
                    str(e))
                os.remove(file_path)
                return
            s.settimeout(None)
            file_size_str = str(os.path.getsize(file_path))
            s.send(("EXISTS" + file_name_container + file_size_str).encode())
            print("FileSize: ", file_size_str.encode())
            response = s.recv(1024)
            response = response.decode()
            if response.startswith('OK'):
                with open(file_path, 'rb') as f:
                    bytes_to_send = f.read(4096)
                    s.send(bytes_to_send)
                    while bytes_to_send != b"":
                        bytes_to_send = f.read(4096)
                        s.send(bytes_to_send)
            s.close()
            os.remove(file_path)
            print("File Removed")
        else:
            print(file_path + " Does not exist.")

    # Deletes old recordings if we're running out of storage capacity.
    def _make_room(self):
        while True:
            # Convert Gb to b.
            max_folder_size = 1000000000 * self.max_local_storage_capacity
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

            folder_size = calc_folder_size(self.recordings_output_path)
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
