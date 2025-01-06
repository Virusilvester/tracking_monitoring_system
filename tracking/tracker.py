# File: tracking/tracker.py

from tracking.deep_sort import DeepSortTracker


class Tracker:
    def __init__(self, max_age=30, min_hits=3):
        self.deepsort = DeepSortTracker(max_age=max_age, min_hits=min_hits)

    def update_tracks(self, detections):
        """
        Update tracks based on detections.
        :param detections: List of detections, each with 'bbox' and 'label'.
        :return: Tracked objects with IDs and centers.
        """
        formatted_detections = [(det['bbox'], det['label']) for det in detections]
        self.deepsort.update(formatted_detections)
        return self.deepsort.get_tracks()
