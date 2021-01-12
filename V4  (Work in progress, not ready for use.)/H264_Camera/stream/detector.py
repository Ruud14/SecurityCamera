import cv2


# Class that handles the detection of motion in the live camera feed.
class Detector:
    def __init__(self, sensitivity=25):

        # The sensitivity. Higher number = less detection.
        self.motion_sensitivity = sensitivity
        # Create the recorder
        #self.recorder = Recorder(self.ip, self.credentials)
        self.first_run = True

    # Detects motion in the live video feed.
    def detect_motion(self, previous_frame, current_frame):
        if self.first_run:
            self.first_run = False
            print("Detector started!")
        blur = (5, 5)
        # convert the previous frame to grey scale and apply blur.
        start_frame = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
        start_frame = cv2.GaussianBlur(start_frame, blur, 0)

        # convert the current frame to grey scale and apply blur.
        next_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        next_frame = cv2.GaussianBlur(next_frame, blur, 0)

        # Calculate the difference between the current and previous frame.
        frame_difference = cv2.absdiff(next_frame, start_frame)
        thresh = cv2.threshold(frame_difference, self.motion_sensitivity, 255, cv2.THRESH_BINARY)[1]

        # Start recording when the difference between the frames is too big.
        if thresh.sum() > 100:
            print("Movement detected!")
            # self.recorder.report_motion()
