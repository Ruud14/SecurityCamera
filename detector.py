from buffers import DetectionBuffer
import cv2


# Class that handles the detection of motion in the live camera feed.
class Detector:
    def __init__(self, camera, recorder, motion_threshold=20, detection_resolution=(64, 48)):
        self.camera = camera
        self.recorder = recorder
        # The motion threshold. Higher number = less detection.
        self.motion_threshold = motion_threshold
        self.detection_resolution = detection_resolution
        self.detection_buffer = DetectionBuffer(self.detect_motion)

    # Start the detector.
    def start(self):
        # Start recording to the detection buffer.
        self.camera.start_recording(
            self.detection_buffer,
            splitter_port=3,
            resize=self.detection_resolution,
            format='mjpeg'
        )
        # Let the user know that the detector started successfully.
        print("Motion detector started successfully!")

    # Calculates the difference between previous_frame and current_frame.
    # Reports motion to the recorder if the difference exceeds the threshold.
    def detect_motion(self, previous_frame, current_frame):

        blur = (5, 5)
        # convert the previous frame to grey scale and apply blur.
        start_frame = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
        start_frame = cv2.GaussianBlur(start_frame, blur, 0)

        # convert the current frame to grey scale and apply blur.
        next_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        next_frame = cv2.GaussianBlur(next_frame, blur, 0)

        # Calculate the difference between the current and previous frame.
        frame_difference = cv2.absdiff(next_frame, start_frame)
        thresh = cv2.threshold(frame_difference, self.motion_threshold, 255, cv2.THRESH_BINARY)[1]

        # Start recording when the difference between the frames is too big.
        if thresh.sum() > 100:
            # Report motion to the recorder so it can start recording.
            self.recorder.report_motion()
