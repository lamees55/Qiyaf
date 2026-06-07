import os
import time
import uuid

import cv2
import numpy as np

from app.services.yolo_service import (
    predict_panels,
    track_panels,
    predict_defects,
)

from app.services.tracker_service import TrackMemory

from app.services.video_service import (
    open_video,
    get_video_metadata,
    create_video_writer,
    should_process_frame,
)

from app.utils.image_utils import (
    ensure_dir,
    crop_panel,
    draw_detection,
)

from app.utils.prediction_utils import final_panel_status
from app.utils.constants import DEFAULT_LABEL ,MIN_TRACK_FRAMES ,MIN_TRACK_HITS_TO_DRAW
#from fastapi import File


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "ai_outputs")
ensure_dir(OUTPUT_DIR)


# ===================== IMAGE =====================

def run_pipeline(image):
    if image is None:
        return []

    result = predict_panels(image)

    if result.boxes is None or len(result.boxes) == 0:
        return []

    boxes = result.boxes.xyxy.cpu().numpy()
    confs = result.boxes.conf.cpu().numpy()

    detections = []

    for i, box in enumerate(boxes):
        crop, expanded_box = crop_panel(image, box)

        if crop is None:
            continue

        defect_result = predict_defects(crop)

        label, defect_conf = final_panel_status(defect_result)

        panel_conf = float(confs[i])
        final_conf = defect_conf if label != DEFAULT_LABEL else panel_conf

        x1, y1, x2, y2 = map(int, expanded_box)

        detections.append({
            "panel_id": i + 1,
            "type": label,
            "fault_type": label,
            "confidence": float(final_conf),
            "panel_confidence": float(panel_conf),
            "box": {
                "x1": x1, "y1": y1,
                "x2": x2, "y2": y2,
            },
            "box_coordinates": {
                "x1": x1, "y1": y1,
                "x2": x2, "y2": y2,
            },
            "image_path": "",
        })

    return detections


# ===================== IMAGE FILE =====================

def process_image_file(image_path: str):
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    detections = run_pipeline(image)

    annotated = image.copy()

    for det in detections:
        box = [
            det["box"]["x1"],
            det["box"]["y1"],
            det["box"]["x2"],
            det["box"]["y2"],
        ]

        draw_detection(
            annotated,
            box=box,
            label=det["fault_type"],
            panel_id=det["panel_id"],
        )

    out_name = f"annotated_{uuid.uuid4().hex}.jpg"
    out_path = os.path.join(OUTPUT_DIR, out_name)

    cv2.imwrite(out_path, annotated)

    return {
        "input_type": "image",
        "output_path": out_path,
        "detections": detections,
    }


# ===================== VIDEO =====================

def process_video_file(video_path: str):
    print("INSIDE PROCESS_VIDEO_FILE")
    print("OPEN VIDEO:", video_path)
    cap = open_video(video_path)
    meta = get_video_metadata(cap)

    print("VIDEO META:", meta)

    fps = meta["fps"]
    width = meta["width"]
    height = meta["height"]

    out_name = f"annotated_{uuid.uuid4().hex}.mp4"
    out_path = os.path.join(OUTPUT_DIR, out_name)

    writer = create_video_writer(out_path, fps, width, height)

    tracker = TrackMemory()

    frame_index = 0
    processed_frames = 0

    start = time.time()

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        frame_index += 1

        if not should_process_frame(frame_index):
            continue

        processed_frames += 1

        annotated = frame.copy()

        # ===== TRACKER =====
        result = track_panels(frame)

        if result.boxes is None:
            print("FRAME:", frame_index, "TRACK BOXES: None")
        else:
            print(
                "FRAME:",
                frame_index,
                "TRACK BOXES:",
                len(result.boxes),
                "IDS:",
                result.boxes.id
            )
            current_ids = set()

        if result.boxes is not None and len(result.boxes) > 0:

            boxes = result.boxes.xyxy.cpu().numpy()
            confs = result.boxes.conf.cpu().numpy()

            if result.boxes.id is not None:
                ids = result.boxes.id.cpu().numpy().astype(int)
            else:
                ids = np.arange(len(boxes))

            for i, box in enumerate(boxes):

                crop, expanded_box = crop_panel(frame, box)

                if crop is None:
                    continue

                defect_result = predict_defects(crop)

                label, defect_conf = final_panel_status(defect_result)

                tid = int(ids[i])

                current_ids.add(tid)

                state = tracker.update_track(
                    track_id=tid,
                    box=expanded_box,
                    label=label,
                    confidence=defect_conf,
                    frame_number=processed_frames,
                )

                print("TRACK STATE:", state)

                # ===== TEMP TEST =====
                if state["hits"] >= MIN_TRACK_HITS_TO_DRAW:
                    draw_detection(
                        annotated,
                        box=state["smooth_box"],
                        label=state["stable_label"],
                        panel_id=state["track_id"],
                    )

        
        print("FRAME SHAPE:", annotated.shape)
        print("FRAME DTYPE:", annotated.dtype)
        writer.write(annotated)
        print("FRAME WRITTEN")

    cap.release()
    writer.release()

    elapsed = time.time() - start

    detections = tracker.final_results()
    detections = [
        d for d in detections
        if d.get("frames_seen", 0) >= MIN_TRACK_FRAMES
    ]
    print("FINAL DETECTIONS:", detections)
    print("TOTAL FINAL:", len(detections))

    for d in detections:
        d["image_path"] = out_path


    return {
        "input_type": "video",
        "output_path": out_path,
        "detections": detections,
        "processing_time_sec": float(elapsed),
        "frames_processed": int(processed_frames),
    }


# ===================== ROUTER HELPER =====================

def run_pipeline_file(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
        return process_image_file(file_path)

    if ext in [".mp4", ".avi", ".mov", ".mkv"]:
        return process_video_file(file_path)

    raise ValueError(f"Unsupported file type: {ext}")