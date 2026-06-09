from collections import defaultdict

import numpy as np

from app.utils.constants import (
    MIN_TRACK_HITS_TO_DRAW,
    MAX_MISSING_FRAMES,
    BOX_SMOOTH_ALPHA,
)
from app.utils.tracking_utils import get_track_final_label


def smooth_box(prev_box, new_box, alpha=BOX_SMOOTH_ALPHA):
    prev = np.array(prev_box, dtype=float)
    new = np.array(new_box, dtype=float)

    smoothed = alpha * prev + (1 - alpha) * new

    return smoothed.astype(int).tolist()


class TrackMemory:
    def __init__(self):
        self.votes = defaultdict(list)        
        self.smooth_boxes = {}                
        self.last_boxes = {}                  
        self.hits = defaultdict(int)          
        self.last_seen = {}                   

    def update_track(self, track_id, box, label, confidence, frame_number):
        self.votes[track_id].append((label, confidence))
        self.hits[track_id] += 1
        self.last_seen[track_id] = frame_number
        self.last_boxes[track_id] = box

        if track_id not in self.smooth_boxes:
            self.smooth_boxes[track_id] = box
        else:
            self.smooth_boxes[track_id] = smooth_box(
                self.smooth_boxes[track_id],
                box
            )

        stable_label, stable_conf = get_track_final_label(
            self.votes[track_id]
        )

        return {
            "track_id": int(track_id),
            "stable_label": stable_label,
            "stable_confidence": float(stable_conf),
            "smooth_box": self.smooth_boxes[track_id],
            "hits": int(self.hits[track_id]),
        }

    def get_recent_missing_tracks(self, current_ids, frame_number):
        results = []

        for track_id, box in self.smooth_boxes.items():
            if track_id in current_ids:
                continue

            if track_id not in self.last_seen:
                continue

            missing = frame_number - self.last_seen[track_id]

            if (
                0 < missing <= MAX_MISSING_FRAMES
                and self.hits[track_id] >= MIN_TRACK_HITS_TO_DRAW
            ):
                label, conf = get_track_final_label(self.votes[track_id])

                results.append({
                    "track_id": int(track_id),
                    "stable_label": label,
                    "stable_confidence": float(conf),
                    "smooth_box": box,
                    "hits": int(self.hits[track_id]),
                    "missing_frames": int(missing),
                })

        return results

    def final_results(self):
        results = []

        for track_id, votes in self.votes.items():
            label, conf = get_track_final_label(votes)

            box = self.last_boxes.get(track_id, [0, 0, 0, 0])

            results.append({
                "panel_id": int(track_id),
                "type": label,
                "fault_type": label,
                "confidence": float(conf),
                "frames_seen": int(self.hits[track_id]),
                "box": {
                    "x1": int(box[0]),
                    "y1": int(box[1]),
                    "x2": int(box[2]),
                    "y2": int(box[3]),
                },
                "box_coordinates": {
                    "x1": int(box[0]),
                    "y1": int(box[1]),
                    "x2": int(box[2]),
                    "y2": int(box[3]),
                },
            })

        return results