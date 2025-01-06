# File: data_analytics/anomaly_report.py

import csv
import matplotlib.pyplot as plt


class AnomalyReport:
    def __init__(self, analytics_manager):
        self.analytics_manager = analytics_manager

    def export_csv(self, filename):
        """Export recorded anomalies to a CSV file."""
        with open(filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['person_id', 'timestamp', 'duration'])
            writer.writeheader()
            for anomaly in self.analytics_manager.anomalies:
                writer.writerow(anomaly)

    def create_visualizations(self):
        """Create visualizations based on the analyzed data."""
        analysis_results = self.analytics_manager.analyze_data()

        # Plotting total anomalies per person
        plt.figure(figsize=(10, 5))
        plt.bar(analysis_results['anomaly_count'].keys(), analysis_results['anomaly_count'].values())
        plt.title('Total Anomalies per Person')
        plt.xlabel('Person ID')
        plt.ylabel('Number of Anomalies')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

        # Plotting average duration of loitering per person
        plt.figure(figsize=(10, 5))
        avg_durations = [
            duration / analysis_results['anomaly_count'][pid] for pid, duration in
            analysis_results['total_duration'].items()
            if analysis_results['anomaly_count'][pid] > 0
        ]

        plt.bar(analysis_results['total_duration'].keys(), avg_durations)

        plt.title('Average Duration of Loitering per Person')
        plt.xlabel('Person ID')
        plt.ylabel('Average Duration (seconds)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
