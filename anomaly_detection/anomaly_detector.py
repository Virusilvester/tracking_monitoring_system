# File: anomaly_detection/anomaly_detector.py

import time
from configs.config import restricted_areas
from notifications.alert_manager import NotificationManager
from data_analytics.analytics_manager import AnalyticsManager
from data_analytics.anomaly_report import AnomalyReport  # Import AnomalyReport
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime


class LoiteringDetector:
    def __init__(self):
        self.active_loiters = {}
        self.notification_manager = NotificationManager()
        self.analytics_manager = AnalyticsManager()  # Initialize AnalyticsManager
        self.anomaly_report = AnomalyReport(self.analytics_manager)  # Initialize AnomalyReport
        self.alerted_messages = set()  # Track alerted messages to avoid duplicates

    def update(self, person_id, area_name):
        current_time = time.time()

        if area_name in restricted_areas and restricted_areas[area_name]["is_restricted"]:
            if person_id not in self.active_loiters:
                # Start tracking when entering the restricted area
                self.active_loiters[person_id] = {
                    "entry_time": current_time,
                    "area_name": area_name
                }
            else:
                # Check if they are still in the area
                elapsed_time = current_time - self.active_loiters[person_id]["entry_time"]
                if elapsed_time > restricted_areas[area_name]["time_threshold"]:
                    self.flag_loitering(person_id, area_name)

    def flag_loitering(self, person_id, area_name):
        current_time = time.time()

        anomaly_message = (
            f"Loitering detected: {person_id} in {area_name} "
            f"for more than {restricted_areas[area_name]['time_threshold']} seconds."
        )

        # Check if this message has already been alerted
        if anomaly_message not in self.alerted_messages:
            print(anomaly_message)  # Print to console for debugging (optional)

            # Record the anomaly in analytics manager
            duration = current_time - self.active_loiters[person_id]["entry_time"]

            # Record anomaly details
            self.analytics_manager.record_anomaly(person_id, current_time, duration)

            # Send alert via NotificationManager
            self.notification_manager.alert(anomaly_message)

            # Add this message to alerted messages set
            self.alerted_messages.add(anomaly_message)

    def exit_area(self, person_id):
        if person_id in self.active_loiters:
            del self.active_loiters[person_id]

    def generate_report(self, filename="anomalies_report.csv"):
        """Generate a report of anomalies."""
        self.anomaly_report.export_csv(filename)  # Export anomalies to CSV

    def visualize_data(self):
        """Visualize the recorded anomalies."""
        self.anomaly_report.create_visualizations()  # Create visualizations for anomalies

class ObjectInteractionDetector:
    def __init__(self):
        self.notification_manager = NotificationManager()
        self.analytics_manager = AnalyticsManager()
        self.active_detections = {}
        self.detection_threshold = 3  # Number of consecutive frames to confirm detection
        self.last_alert_time = {}
        self.alert_cooldown = 30  # Seconds between alerts for the same area

    def update(self, frame_detections, frame_id, location=None):
        """
        Update detector with current frame detections
        frame_detections: list of detection dictionaries
        """
        # Find persons and cell phones in current frame
        persons = [det for det in frame_detections if det.get('class_name') == 'person']
        phones = [det for det in frame_detections if det.get('class_name') == 'cell phone']

        # Check for close interactions
        for person in persons:
            person_bbox = person['bbox']  # Access bbox from the dictionary
            for phone in phones:
                phone_bbox = phone['bbox']  # Access bbox from the dictionary
                
                # If phone is near person
                if self._check_proximity(person_bbox, phone_bbox):
                    area_key = f"{location or 'unknown'}_{int(person_bbox[0])}_{int(person_bbox[1])}"
                    
                    if area_key not in self.active_detections:
                        self.active_detections[area_key] = 1
                    else:
                        self.active_detections[area_key] += 1

                    # Alert if threshold reached and cooldown passed
                    if (self.active_detections[area_key] >= self.detection_threshold and 
                        self._check_alert_cooldown(area_key)):
                        self._trigger_alert(area_key, person, phone, location)
                        self.active_detections[area_key] = 0

    def _check_proximity(self, bbox1, bbox2, threshold=100):
        """Check if two bounding boxes are close to each other"""
        x1_center = (bbox1[0] + bbox1[2]) / 2
        y1_center = (bbox1[1] + bbox1[3]) / 2
        x2_center = (bbox2[0] + bbox2[2]) / 2
        y2_center = (bbox2[1] + bbox2[3]) / 2
        
        distance = ((x1_center - x2_center) ** 2 + (y1_center - y2_center) ** 2) ** 0.5
        return distance < threshold

    def _check_alert_cooldown(self, area_key):
        """Check if enough time has passed since last alert"""
        current_time = time.time()
        if area_key not in self.last_alert_time:
            return True
        
        time_since_last_alert = current_time - self.last_alert_time[area_key]
        return time_since_last_alert > self.alert_cooldown

    def _trigger_alert(self, area_key, person_detection, phone_detection, location):
        """Send alert and record the incident"""
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        location_str = location or "Unknown Location"
        
        alert_message = (
            f"ALERT: Person with cell phone detected at {location_str}\n"
            f"Time: {current_time}\n"
            f"Person confidence: {person_detection[1]:.2f}\n"
            f"Phone confidence: {phone_detection[1]:.2f}"
        )
        
        # Send alert
        self.notification_manager.alert(alert_message)
        
        # Record for analytics
        self.analytics_manager.record_anomaly(
            person_id=f"person_{area_key}",
            timestamp=time.time(),
            anomaly_type="person_with_phone",
            location=location_str
        )
        
        # Update last alert time
        self.last_alert_time[area_key] = time.time()

    def reset(self):
        """Reset all detections"""
        self.active_detections.clear()
        self.last_alert_time.clear()

