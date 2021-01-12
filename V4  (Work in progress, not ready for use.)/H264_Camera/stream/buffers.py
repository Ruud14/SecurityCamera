from websockethandler import WebSocketHandler
from picamera import PiCamera, PiVideoFrameType
import io, os, socket
import cv2
import numpy as np
from detector import Detector


class StreamBuffer(object):
    def __init__(self, camera, fps, delayed_seconds):
        self.frameTypes = PiVideoFrameType()
        self.loop = None
        self.buffer = io.BytesIO()
        self.camera = camera
        self.fps = fps
        self.delayed_seconds = delayed_seconds
        self.frame = None
        self.old_frames = []

    def setLoop(self, loop):
        self.loop = loop

    def write(self, buf):
        if self.camera.frame.complete and self.camera.frame.frame_type != self.frameTypes.sps_header:
            self.buffer.write(buf)
            self.frame = self.buffer.getvalue()

            # Collect delayed frames.
            if len(self.old_frames) <= self.delayed_seconds * self.fps:
                self.old_frames.append(self.frame)
            else:
                del self.old_frames[0]
                self.old_frames.append(self.frame)

            if self.loop is not None and WebSocketHandler.hasConnections():
                self.loop.add_callback(callback=WebSocketHandler.broadcast, message=self.frame)

            self.buffer.seek(0)
            self.buffer.truncate()
        else:
            self.buffer.write(buf)


class DetectionBuffer(object):
    def __init__(self, motion_detector):
        self.motion_detector = motion_detector
        self.buffer = io.BytesIO()
        self.previous_frame = []
        self.current_frame = []

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
                    self.motion_detector.detect_motion(self.previous_frame, self.current_frame)
            self.buffer.seek(0)

        return self.buffer.write(buf)