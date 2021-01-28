from general import WebSocketHandler
from picamera import PiCamera, PiVideoFrameType
import numpy as np
import cv2
import io


# Buffer for the live camera feed.
class StreamBuffer(object):
    def __init__(self, camera):
        self.camera = camera
        self.loop = None
        self.buffer = io.BytesIO()

    def setLoop(self, loop):
        self.loop = loop

    def write(self, buf):
        if self.camera.frame.complete and self.camera.frame.frame_type != PiVideoFrameType().sps_header:
            self.buffer.write(buf)
            frame = self.buffer.getvalue()
            if self.loop is not None and WebSocketHandler.hasConnections():
                self.loop.add_callback(callback=WebSocketHandler.broadcast, message=frame)

            self.buffer.seek(0)
            self.buffer.truncate()
        else:
            self.buffer.write(buf)


# Buffer for the detection in the camera feed.
class DetectionBuffer(object):
    def __init__(self, detect_motion_function):
        self.detect_motion_function = detect_motion_function
        self.buffer = io.BytesIO()
        self.previous_frame = []
        self.current_frame = []

    # Converts bytes frame data into an openCV frame.
    def convert_frame_data_to_opencv_frame(self, frame_data):
        data = np.fromstring(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(data, 1)
        return frame

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame
            self.buffer.truncate()
            read_frame_data = self.buffer.getvalue()
            if read_frame_data != b'':
                self.previous_frame = self.current_frame
                self.current_frame = self.convert_frame_data_to_opencv_frame(read_frame_data)
                if self.previous_frame != [] and self.current_frame != []:
                    self.detect_motion_function(self.previous_frame, self.current_frame)
            self.buffer.seek(0)

        return self.buffer.write(buf)
