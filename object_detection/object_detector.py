# File: object_detection/object_detector.py

import torch
import cv2
import numpy as np
import os

from configs.config import model_config


class ObjectDetector:
    def __init__(self):
        """
        Initialize the Object Detector using configurations from config.py.
        """
        try:
            self.model_path = model_config['model_path']
            self.confidence_threshold = model_config['confidence_threshold']

            # Get the absolute path to the yolov5 directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            yolov5_repo_path = os.path.join(current_dir, '..', 'lib', 'yolov5')
            model_full_path = os.path.join(current_dir, '..', self.model_path)

            # Ensure the model file exists
            if not os.path.isfile(model_full_path):
                raise FileNotFoundError(f"Model file not found: {model_full_path}")

            print(f"Loading model from: {model_full_path}")
            print(f"YOLOv5 repo path: {yolov5_repo_path}")

            # Load the model using the specified local path
            self.model = torch.hub.load(yolov5_repo_path, 'custom', path=model_full_path, source='local')
            self.model.eval()  # Set to evaluation mode
            
            print("Model loaded successfully")
        except Exception as e:
            print(f"Error initializing ObjectDetector: {str(e)}")
            raise

    def detect_objects(self, frame):
        """
        Perform object detection on the input frame.
        :param frame: The input frame.
        :return: List of detected objects, each represented as a dictionary containing 'id', 'label', 'confidence', and 'bbox'.
        """
        # Convert frame to uint8 if needed
        if frame.dtype != np.uint8:
            frame = (frame * 255).astype(np.uint8)

        # Convert the frame to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Perform inference
        results = self.model(rgb_frame)

        # Filter results based on confidence threshold
        detections = []
        for index, (*xyxy, confidence, class_id) in enumerate(results.xyxy[0]):
            if confidence > self.confidence_threshold:
                label = self.model.names[int(class_id)]
                bbox = [int(x.item()) for x in xyxy]  # Bounding box coordinates
                detections.append({
                    'id': index,  # Unique ID for each detection
                    'label': label,
                    'confidence': float(confidence),
                    'bbox': bbox
                })

        return detections

    def draw_bboxes(self, frame, detections):
        """
        Draw bounding boxes on the frame.
        :param frame: The input frame.
        :param detections: List of detected objects.
        :return: Frame with bounding boxes drawn.
        """
        for detection in detections:
            label = detection['label']
            confidence = detection['confidence']
            bbox = detection['bbox']

            # Draw bounding box
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)

            # Display label and confidence
            text = f"{label}: {confidence:.2f}"
            cv2.putText(frame, text, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return frame
