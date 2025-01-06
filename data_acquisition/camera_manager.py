# File: data_acquisition/camera_manager.py
import cv2
from configs.config import camera_config


class CameraManager:
    def __init__(self):
        """
        Initialize the Camera Manager with settings strictly from config.py.
        """
        self.camera_type = camera_config["camera_type"]
        self.camera_source = camera_config["camera_source"]
        self.capture = None

    def connect(self):
        """
        Connect to the camera using settings from config.py.
        """
        try:
            if self.camera_type == 'USB':
                self.capture = cv2.VideoCapture(self.camera_source)
                
                # Set fixed camera properties
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.capture.set(cv2.CAP_PROP_FPS, 30)
                
            elif self.camera_type in ['IP', 'RTSP']:
                self.capture = cv2.VideoCapture(self.camera_source)
            else:
                raise ValueError(f"Unsupported camera type: {self.camera_type}")

            if not self.capture.isOpened():
                raise ConnectionError("Failed to connect to the camera")

            # Read a test frame to verify connection
            ret, _ = self.capture.read()
            if not ret:
                raise ConnectionError("Camera connected but failed to read frame")

            print(f"Connected to {self.camera_type} camera at {self.camera_source}")
            
        except Exception as e:
            print(f"Error connecting to camera: {str(e)}")
            raise

    def disconnect(self):
        """
        Disconnect from the camera and release resources.
        """
        if self.capture:
            self.capture.release()
            self.capture = None
            print("Camera disconnected")

    def is_connected(self):
        """
        Check if the camera is currently connected.
        :return: True if connected, False otherwise.
        """
        return self.capture is not None and self.capture.isOpened()

    def get_frame(self):
        """
        Capture a single frame from the camera.
        :return: The captured frame.
        """
        if not self.is_connected():
            raise RuntimeError("Camera is not connected")

        ret, frame = self.capture.read()
        if not ret:
            raise RuntimeError("Failed to capture frame")

        return frame
