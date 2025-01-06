# File: preprocessing/frame_preprocessor.py
import cv2


class FramePreprocessor:
    def __init__(self, target_width=640, target_height=480):
        """
        Initialize the Frame Preprocessor.
        :param target_width: Width to resize the frame.
        :param target_height: Height to resize the frame.
        """
        self.target_width = target_width
        self.target_height = target_height

    def resize_frame(self, frame):
        """
        Resize the frame to the target dimensions.
        :param frame: The input frame.
        :return: Resized frame.
        """
        return cv2.resize(frame, (self.target_width, self.target_height))

    def normalize_frame(self, frame):
        """
        Normalize the frame pixel values to the range [0, 1].
        :param frame: The input frame.
        :return: Normalized frame.
        """
        return frame / 255.0

    def preprocess(self, frame):
        """
        Resize and normalize the frame.
        :param frame: The input frame.
        :return: Preprocessed frame.
        """
        resized_frame = self.resize_frame(frame)
        normalized_frame = self.normalize_frame(resized_frame)
        return normalized_frame
