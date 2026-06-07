import cv2

from app.utils.constants import FRAME_STRIDE


def open_video(video_path: str):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    return cap


def get_video_metadata(cap):
    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = fps if fps and fps > 0 else 10.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    duration_sec = total_frames / fps if fps > 0 else 0

    return {
        "fps": fps,
        "width": width,
        "height": height,
        "total_frames": total_frames,
        "duration_sec": duration_sec,
    }


def create_video_writer(output_path: str, fps: float, width: int, height: int):
    output_fps = fps / FRAME_STRIDE if FRAME_STRIDE > 1 else fps

    writer = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        output_fps,
        (width, height)
    )
    
    print("FPS:", output_fps)
    print("SIZE:", width, height)

    if not writer.isOpened():
        raise ValueError(f"Could not create video writer: {output_path}")
    return writer


def should_process_frame(frame_index: int):
    if FRAME_STRIDE <= 1:
        return True

    return frame_index % FRAME_STRIDE == 0