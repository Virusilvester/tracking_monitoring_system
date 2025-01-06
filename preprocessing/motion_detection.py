# File: preprocessing/motion_detection.py
import cv2


class MotionDetector:
    def __init__(self, min_area=500):
        """
        Initialize the Motion Detector.
        :param min_area: Minimum area size for motion to be considered significant.
        """
        self.min_area = min_area
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2()

    def detect_motion(self, frame):
        """
        Detect motion in the given frame.
        :param frame: The input frame.
        :return: Boolean indicating if significant motion is detected.
        """
        # Apply the background subtraction model
        fg_mask = self.bg_subtractor.apply(frame)

        # Find contours in the foreground mask
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Check if any contour area is larger than the minimum threshold
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                return True

        return False
