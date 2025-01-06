# File: tracking/deep_sort.py

import numpy as np
from collections import deque


class DeepSortTracker:
    def __init__(self, max_age=30, min_hits=3):
        self.tracks = []
        self.max_age = max_age
        self.min_hits = min_hits
        self.track_id = 0

    def update(self, detections):
        # Update tracks with new detections
        for det in detections:
            box, class_id = det
            x, y, w, h = box
            center = (x + w / 2, y + h / 2)

            # Create a new track if no existing track matches
            if not self.tracks:
                self.tracks.append({'id': self.track_id, 'center': center, 'age': 0})
                self.track_id += 1
            else:
                # Check if the detected object matches an existing track
                matched = False
                for track in self.tracks:
                    if np.linalg.norm(np.array(track['center']) - np.array(center)) < 50:  # Distance threshold
                        track['center'] = center
                        track['age'] = 0  # Reset age if matched
                        matched = True
                        break

                if not matched:
                    self.tracks.append({'id': self.track_id, 'center': center, 'age': 0})
                    self.track_id += 1

        # Increment age of all tracks and remove old tracks
        for track in self.tracks:
            track['age'] += 1

        self.tracks = [track for track in self.tracks if track['age'] < self.max_age]

    def get_tracks(self):
        return [(track['id'], track['center']) for track in self.tracks]