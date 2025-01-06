# File: data_acquisition/video_stream.py

import cv2
import threading
import time

from data_acquisition.camera_manager import CameraManager
from preprocessing.frame_preprocessor import FramePreprocessor
from preprocessing.motion_detection import MotionDetector
from object_detection.object_detector import ObjectDetector
from anomaly_detection.anomaly_detector import LoiteringDetector
from configs.config import camera_config, model_config


class VideoStreamHandler:
    def __init__(self, display_window=False):
        """
        Initialize the Video Stream Handler.
        :param display_window: Whether to display the video stream in a window.
        """
        self.camera_manager = CameraManager() 
        self.display_window = display_window
        self.running = False
        self.current_frame = None
        self.lock = threading.Lock()
        self.preprocessor = FramePreprocessor()
        self.motion_detector = MotionDetector()
        self.object_detector = ObjectDetector()
        self.loitering_detector = LoiteringDetector()
        self.ml_enabled = False
        self.capture = None
        self.model = None  # YOLO model will be initialized when needed
        
    def start_stream(self):
        """
        Start the video stream.
        """
        try:
            # Initialize video capture
            if camera_config["camera_type"] == "USB":
                self.capture = cv2.VideoCapture(camera_config["camera_source"])
            elif camera_config["camera_type"] == "IP":
                self.capture = cv2.VideoCapture(camera_config["camera_source"])
            
            if not self.capture.isOpened():
                raise Exception("Failed to open video stream")
            
            self.running = True
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._capture_frames)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            # Initialize YOLO model if ML is enabled
            if self.ml_enabled and self.model is None:
                self.model = self._initialize_model()
                
        except Exception as e:
            print(f"Error starting stream: {str(e)}")
            self.running = False

    def _capture_frames(self):
        """
        Continuously capture frames in a separate thread.
        """
        while self.running:
            ret, frame = self.capture.read()
            if ret:
                self.current_frame = frame
            else:
                print("Failed to capture frame")
                self.running = False
            time.sleep(0.01)  # Small delay to prevent excessive CPU usage

    def stop_stream(self):
        """
        Stop the video stream.
        """
        self.running = False
        if self.capture_thread is not None:
            self.capture_thread.join()
        if self.capture is not None:
            self.capture.release()
        self.current_frame = None
        self.camera_manager.disconnect()
        if self.display_window:
            cv2.destroyAllWindows()

    def get_latest_frame(self):
        """
        Get the latest frame from the video stream.
        :return: The latest frame with object detection.
        """
        with self.lock:
            return self.frame

    def get_latest_frame_with_detections(self):
        """Get the latest frame and its detections"""
        if not self.running or self.current_frame is None:
            return None, None
        
        frame = self.current_frame.copy()
        
        if self.ml_enabled and self.model is not None:
            # Perform YOLO detection
            results = self.model(frame)
            detections = []
            
            # Process YOLO results
            for *xyxy, conf, cls in results.xyxy[0]:
                x1, y1, x2, y2 = map(int, xyxy)
                class_name = self.model.names[int(cls)]
                confidence = float(conf)
                
                # Add detection to list
                detections.append({
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2]
                })
                
                # Draw bounding box on frame
                color = (0, 255, 0)  # Green box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f'{class_name} {confidence:.2f}'
                cv2.putText(frame, label, (x1, y1 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            return frame, detections
        
        return frame, None

    def _initialize_model(self):
        """
        Initialize the YOLO model.
        :return: The initialized YOLO model.
        """
        try:
            import torch
            model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
            model.conf = model_config.get("confidence_threshold", 0.5)
            return model
        except Exception as e:
            print(f"Error initializing YOLO model: {str(e)}")
            return None
