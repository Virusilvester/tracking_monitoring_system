# File: test_video_stream.py

from data_acquisition.video_stream import VideoStreamHandler
from anomaly_detection.anomaly_detector import LoiteringDetector
import time


def main():

    # Initialize the video stream handler
    video_stream = VideoStreamHandler(display_window=True)

    # Initialize the loitering detector
    loitering_detector = LoiteringDetector()

    try:
        print("Starting video stream with object detection...")
        video_stream.start_stream()

        # Simulate streaming and detecting anomalies
        start_time = time.time()
        while time.time() - start_time < 100:  # Stream for 100 seconds
            # Simulate detecting a person entering a restricted area
            person_id = "person_1"
            area_name = "flag_room"

            # Update the loitering detector as if a person is detected in the restricted area
            loitering_detector.update(person_id, area_name)

            # Simulate some time passing (e.g., the person is loitering)
            time.sleep(5)  # Simulate 5 seconds of loitering

            # Check for anomalies
            loitering_detector.flag_loitering(person_id, area_name)

        print("Stopping video stream...")
        video_stream.stop_stream()

        # Generate report after detections
        loitering_detector.generate_report("anomalies_report.csv")  # Generate report of anomalies
        print("Anomalies report generated: anomalies_report.csv")

        # Visualize recorded anomalies
        loitering_detector.visualize_data()  # Create visualizations for recorded anomalies

    except Exception as e:
        print(f"An error occurred: {e}")
        video_stream.stop_stream()


if __name__ == '__main__':
    main()
