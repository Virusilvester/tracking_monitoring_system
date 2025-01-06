# File: configs/config.py

restricted_areas = {
    "flag_room": {
        "is_restricted": True,
        "time_threshold": 10  # Time in seconds
    }
}

# Camera configuration
camera_config = {
    "camera_type": "USB",  # Options: 'USB', 'IP', or 'RTSP'
    "camera_source": 0,    # Source for the camera (index for USB or URL for IP/RTSP)
    "resolution": {
        "width": 640,
        "height": 480
    },
    "fps": 30
}

# Model configuration
model_config = {
    "model_path": "datasets/model/yolov5s.pt",  # Path to the YOLOv5 model file (weights)
    "confidence_threshold": 0.5                   # Minimum confidence score for a detection to be considered valid
}
