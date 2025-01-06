# File: data_analytics/analytics_manager.py

import csv
import time
from collections import defaultdict


class AnalyticsManager:
    def __init__(self):
        self.anomalies = []  # List to store anomaly records
        self.anomaly_count = defaultdict(int)  # Count of anomalies per person
        self.total_duration = defaultdict(int)  # Total duration of loitering per person

    def record_anomaly(self, person_id, timestamp, duration):
        """Record an anomaly with the person's ID, timestamp, and duration."""
        self.anomalies.append({
            'person_id': person_id,
            'timestamp': timestamp,
            'duration': duration
        })
        self.anomaly_count[person_id] += 1
        self.total_duration[person_id] += duration

    def analyze_data(self):
        """Analyze recorded anomalies to calculate metrics."""
        total_anomalies = len(self.anomalies)
        average_duration = (
            sum(self.total_duration.values()) / total_anomalies if total_anomalies > 0 else 0
        )

        return {
            'total_anomalies': total_anomalies,
            'average_duration': average_duration,
            'anomaly_count': dict(self.anomaly_count),
            'total_duration': dict(self.total_duration)
        }

    def generate_report(self, report_type="summary"):
        """Generate a report based on the analyzed data."""
        if report_type == "summary":
            return self.analyze_data()
        else:
            raise ValueError("Unsupported report type. Use 'summary'.")