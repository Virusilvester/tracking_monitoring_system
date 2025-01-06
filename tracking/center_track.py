# File: tracking/center_track.py

class CenterTracker:
    def __init__(self):
        self.tracks = {}
        self.track_id = 0

    def update(self, detections):
        current_tracks = {}

        for det in detections:
            box, class_id = det
            x, y, w, h = box
            center = (x + w / 2, y + h / 2)

            # Assign a new ID or update existing ID based on distance
            matched_id = None
            for tid, (existing_center) in self.tracks.items():
                if np.linalg.norm(np.array(existing_center) - np.array(center)) < 50:  # Distance threshold
                    matched_id = tid
                    break

            if matched_id is not None:
                current_tracks[matched_id] = center
            else:
                current_tracks[self.track_id] = center
                self.track_id += 1

        # Update tracks with current detections
        self.tracks = current_tracks

    def get_tracks(self):
        return [(track_id, center) for track_id, center in self.tracks.items()]