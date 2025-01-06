# File: main.py

import sys
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QTextEdit, QStatusBar, QPushButton, QTabWidget
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QTimer, Signal
import cv2
import numpy as np
from configs.config import camera_config, model_config
from gui.widgets import AlertWidget, SettingsWidget, TrainingWidget
from data_acquisition.video_stream import VideoStreamHandler
from data_analytics.analytics_manager import AnalyticsManager
from data_analytics.anomaly_report import AnomalyReport
from anomaly_detection.anomaly_detector import LoiteringDetector, ObjectInteractionDetector  # Import the detectors

class CCTVMonitorApp(QMainWindow):
    alert_signal = Signal(str)

    def __init__(self):

        super().__init__()
        self.setWindowTitle("CCTV Monitoring System")
        self.setGeometry(100, 100, 1200, 800)
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()

        # Left panel (video feed and controls)
        left_panel = QVBoxLayout()
        
        # Video feed with fixed size
        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 480)  # Set fixed size for video display
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #1e1e1e; border: 2px solid #3a3a3a;")
        left_panel.addWidget(self.video_label)

        # Controls layout
        controls_layout = QHBoxLayout()

        # Camera selection
        self.camera_combo = QComboBox()
        self.camera_combo.addItems(["Camera 1", "Camera 2", "Camera 3"])
        self.camera_combo.setStyleSheet("background-color: #2a2a2a; color: white; padding: 5px;")
        controls_layout.addWidget(QLabel("Select Camera:"))
        controls_layout.addWidget(self.camera_combo)

        # ML model toggle
        self.ml_toggle = QCheckBox("Enable ML Detection")
        self.ml_toggle.setStyleSheet("color: white;")
        controls_layout.addWidget(self.ml_toggle)

        # Record button
        self.record_button = QPushButton("Start Recording")
        self.record_button.setStyleSheet("background-color: #2a2a2a; color: white; padding: 5px;")
        self.record_button.clicked.connect(self.toggle_recording)
        controls_layout.addWidget(self.record_button)

        left_panel.addLayout(controls_layout)

        # Add left panel to main layout
        main_layout.addLayout(left_panel, 2)

        # Right panel (tabs for results, alerts, settings, and training)
        right_panel = QTabWidget()
        right_panel.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3a3a3a;
                background: #1e1e1e;
            }
            QTabBar::tab {
                background: #2a2a2a;
                color: white;
                padding: 5px;
            }
            QTabBar::tab:selected {
                background: #3a3a3a;
            }
        """)

        # Detection results tab
        results_widget = QWidget()
        results_layout = QVBoxLayout()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("background-color: #2a2a2a; color: white; border: none;")
        results_layout.addWidget(self.results_text)
        results_widget.setLayout(results_layout)
        right_panel.addTab(results_widget, "Detection Results")

        # Alerts tab
        self.alert_widget = AlertWidget()
        right_panel.addTab(self.alert_widget, "Alerts")

        # Settings tab
        self.settings_widget = SettingsWidget()
        right_panel.addTab(self.settings_widget, "Settings")

        # Training tab
        self.training_widget = TrainingWidget()
        right_panel.addTab(self.training_widget, "Training")

        main_layout.addWidget(right_panel, 1)

        # Set main layout
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("System Ready")

        # Set dark theme
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1a1a1a;
                color: white;
            }
            QLabel, QCheckBox {
                color: white;
            }
            QPushButton, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #2a2a2a;
                color: white;
                padding: 5px;
                border: 1px solid #3a3a3a;
            }
            QPushButton:hover, QComboBox:hover {
                background-color: #3a3a3a;
            }
        """)

        # Timer for updating video feed
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_video_feed)
        self.timer.start(30)  # Update every 30 ms

        # Initialize backend components
        self.video_handler = VideoStreamHandler(display_window=False)  # Set display_window to False since we'll show in GUI
        self.analytics_manager = AnalyticsManager()
        self.anomaly_report = AnomalyReport(self.analytics_manager)
        
        # Connect signals
        self.alert_signal.connect(self.alert_widget.add_alert)
        self.settings_widget.apply_button.clicked.connect(self.apply_settings)
        self.training_widget.training_started.connect(self.on_training_started)
        self.training_widget.training_progress.connect(self.on_training_progress)
        self.ml_toggle.stateChanged.connect(self.toggle_ml_detection)

        # Initialize state variables
        self.is_recording = False
        self.ml_enabled = False

        # Initialize camera settings dictionary
        self.camera_settings = {
            "Camera 1": {
                "resolution": "640x480",
                "fps": 30,
                "model": "YOLOv5",
                "confidence": 0.5,
                "source_type": "Webcam (0)",
                "source_input": "0"
            },
            "Camera 2": {
                "resolution": "640x480",
                "fps": 30,
                "model": "YOLOv5",
                "confidence": 0.5,
                "source_type": "Webcam (1)",
                "source_input": "1"
            },
            "Camera 3": {
                "resolution": "640x480",
                "fps": 30,
                "model": "YOLOv5",
                "confidence": 0.5,
                "source_type": "Webcam (2)",
                "source_input": "2"
            }
        }

        # Initialize video handlers for each camera but don't start streams
        self.video_handlers = {}
        self.recording_status = {}
        for camera in self.camera_settings.keys():
            self.video_handlers[camera] = VideoStreamHandler(display_window=False)
            self.recording_status[camera] = False

        # Connect camera selection change event
        self.camera_combo.currentTextChanged.connect(self.on_camera_changed)
        
        # Load initial camera settings
        self.current_camera = "Camera 1"
        self.load_camera_settings(self.current_camera)
        
        # Initialize ML detection state
        self.ml_enabled = False

        # Initialize detectors
        self.loitering_detector = LoiteringDetector()  # Instantiate LoiteringDetector
        self.object_interaction_detector = ObjectInteractionDetector()  # Instantiate ObjectInteractionDetector

    def load_camera_settings(self, camera_name):
        """Load settings for the selected camera into the settings widget"""
        settings = self.camera_settings[camera_name]
        self.settings_widget.resolution_combo.setCurrentText(settings["resolution"])
        self.settings_widget.fps_spinbox.setValue(settings["fps"])
        self.settings_widget.model_combo.setCurrentText(settings["model"])
        self.settings_widget.confidence_spinbox.setValue(settings["confidence"])
        self.settings_widget.source_combo.setCurrentText(settings["source_type"])
        self.settings_widget.source_input.setText(settings["source_input"])

    def on_camera_changed(self, camera_name):
        """Handle camera selection change"""
        # Stop the current camera stream if it's running
        if self.video_handlers[self.current_camera].running:
            self.video_handlers[self.current_camera].stop_stream()

        # Update current camera
        self.current_camera = camera_name
        
        # Load settings for the selected camera
        self.load_camera_settings(camera_name)
        
        # Only start the stream if this camera was recording
        if self.recording_status[camera_name]:
            self.start_camera_stream(camera_name)
        
        # Update recording button state
        self.update_recording_button_state()

    def start_camera_stream(self, camera_name):
        """Start video stream for the specified camera"""
        settings = self.camera_settings[camera_name]
        
        # Configure camera settings
        if settings["source_type"] == "Webcam (0)":
            camera_config["camera_type"] = "USB"
            camera_config["camera_source"] = int(settings["source_input"])
        elif settings["source_type"] in ["RTSP/RTMP/HTTP Stream"]:
            camera_config["camera_type"] = "IP"
            camera_config["camera_source"] = settings["source_input"]
        
        # Start the stream
        self.video_handlers[camera_name].start_stream()
        
        # Set ML detection state
        self.video_handlers[camera_name].ml_enabled = self.ml_enabled

    def apply_settings(self):
        """Apply settings to the current camera"""
        # Get settings values
        settings = {
            "resolution": self.settings_widget.resolution_combo.currentText(),
            "fps": self.settings_widget.fps_spinbox.value(),
            "model": self.settings_widget.model_combo.currentText(),
            "confidence": self.settings_widget.confidence_spinbox.value(),
            "source_type": self.settings_widget.source_combo.currentText(),
            "source_input": self.settings_widget.source_input.text()
        }
        
        # Update settings for current camera
        self.camera_settings[self.current_camera] = settings
        
        # Restart the camera stream with new settings only if it's currently recording
        if self.video_handlers[self.current_camera].running:
            self.video_handlers[self.current_camera].stop_stream()
            self.start_camera_stream(self.current_camera)
        
        self.alert_signal.emit(f"Applied settings to {self.current_camera}")
        self.statusBar.showMessage("Settings applied", 3000)

    def toggle_recording(self):
        """Toggle recording for the current camera"""
        current_status = self.recording_status[self.current_camera]
        self.recording_status[self.current_camera] = not current_status
        
        if self.recording_status[self.current_camera]:
            # Start the camera stream when recording begins
            self.start_camera_stream(self.current_camera)
            self.record_button.setText("Stop Recording")
            self.alert_signal.emit(f"Started recording on {self.current_camera}")
        else:
            # Stop the camera stream when recording stops
            self.video_handlers[self.current_camera].stop_stream()
            self.record_button.setText("Start Recording")
            self.alert_signal.emit(f"Stopped recording on {self.current_camera}")
        
        self.update_recording_button_state()

    def update_recording_button_state(self):
        """Update recording button text based on current camera's recording status"""
        if self.recording_status[self.current_camera]:
            self.record_button.setText("Stop Recording")
        else:
            self.record_button.setText("Start Recording")

    def update_video_feed(self):
        """Update the video feed display"""
        if not self.video_handlers[self.current_camera].running:
            return

        frame, detections = self.video_handlers[self.current_camera].get_latest_frame_with_detections()
        if frame is None:
            return

        # Check if detections is None or empty
        if detections is None:
            detections = []  # Initialize as an empty list if None

        # Process detections with the detectors
        for detection in detections:
            class_name = detection['class_name']
            bbox = detection['bbox']  # [x1, y1, x2, y2]
            person_id = detection.get('person_id')  # Assuming person_id is part of the detection data

            # Update loitering detector
            if class_name == 'person':
                area_name = self.get_area_name_from_bbox(bbox)  # Implement this method to get area name
                self.loitering_detector.update(person_id, area_name)

            # Update object interaction detector
            if class_name in ['person', 'cell phone']:
                self.object_interaction_detector.update(detections, frame_id=self.current_camera)

        try:
            # Convert frame back to BGR format if it was normalized
            if frame.dtype == np.float64 or frame.dtype == np.float32:
                frame = (frame * 255).astype(np.uint8)
            
            # Convert BGR to RGB format
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize frame to match video label size
            display_size = (self.video_label.width(), self.video_label.height())
            resized_frame = cv2.resize(rgb_frame, display_size)
            
            # Create QImage from the frame
            height, width = resized_frame.shape[:2]
            bytes_per_line = 3 * width
            qt_image = QImage(resized_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            # Convert to pixmap and display
            pixmap = QPixmap.fromImage(qt_image)
            self.video_label.setPixmap(pixmap)
            
            # Update detection results if ML is enabled
            if self.ml_enabled and detections:
                self.update_detection_results(detections)
            
            if self.recording_status[self.current_camera]:
                self.statusBar.showMessage(f"Recording {self.current_camera}...")
            else:
                self.statusBar.showMessage("System Ready")
            
        except Exception as e:
            self.statusBar.showMessage(f"Error updating video feed: {str(e)}")

    def update_detection_results(self, detections):
        """Update the detection results text area with YOLO detections"""
        timestamp = time.strftime("%H:%M:%S")
        result_text = f"\n[{timestamp}] Detections:\n"
        
        # Group detections by class
        detection_counts = {}
        for detection in detections:
            class_name = detection['class_name']
            confidence = detection['confidence']
            bbox = detection['bbox']  # [x1, y1, x2, y2]
            
            if class_name not in detection_counts:
                detection_counts[class_name] = {
                    'count': 0,
                    'confidences': []
                }
            
            detection_counts[class_name]['count'] += 1
            detection_counts[class_name]['confidences'].append(confidence)
        
        # Format detection results
        for class_name, data in detection_counts.items():
            count = data['count']
            avg_confidence = sum(data['confidences']) / len(data['confidences'])
            result_text += f"  • {class_name}: {count} detected (avg conf: {avg_confidence:.2f})\n"
        
        # Add to results text with auto-scroll
        self.results_text.append(result_text)
        self.results_text.verticalScrollBar().setValue(
            self.results_text.verticalScrollBar().maximum()
        )
        
        # Check for alerts based on detections
        self.check_detection_alerts(detection_counts)

    def check_detection_alerts(self, detection_counts):
        """Check detections for alert conditions"""
        alert_classes = ['person', 'car', 'truck']  # Add more classes as needed
        alert_thresholds = {
            'person': 1,  # Alert if more than 3 people detected
            'car': 2,     # Alert if more than 2 cars detected
            'truck': 1    # Alert if any truck detected
        }
        
        for class_name, threshold in alert_thresholds.items():
            if class_name in detection_counts:
                count = detection_counts[class_name]['count']
                if count > threshold:
                    alert_msg = f"Alert: Detected {count} {class_name}(s) in camera view"
                    self.alert_signal.emit(alert_msg)

    def toggle_ml_detection(self, state):
        """Toggle ML detection on/off"""
        self.ml_enabled = bool(state)
        
        # Update ML state for current camera if it's running
        if self.video_handlers[self.current_camera].running:
            self.video_handlers[self.current_camera].ml_enabled = self.ml_enabled
        
        if self.ml_enabled:
            self.results_text.append("ML Detection enabled")
        else:
            self.results_text.append("ML Detection disabled")

    def on_training_started(self, message):
        self.alert_widget.add_alert(message)
        self.statusBar.showMessage(message)

    def on_training_progress(self, progress, metrics):
        self.statusBar.showMessage(f"Training progress: {progress}%")
        # Update any metrics displays you have

    def closeEvent(self, event):
        """Handle application closure"""
        for handler in self.video_handlers.values():
            handler.stop_stream()
        event.accept()

    def get_area_name_from_bbox(self, bbox):
        """Determine the area name based on the bounding box coordinates"""
        # Implement logic to map bbox to area name
        return "some_area_name"  # Placeholder


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CCTVMonitorApp()
    window.show()
    sys.exit(app.exec())
