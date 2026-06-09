import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.services.pipeline_service import run_pipeline_file
from app.utils.image_utils import ensure_dir


router = APIRouter(
    prefix="/inference",
    tags=["AI Inference"]
)

UPLOAD_DIR = "app/uploads"
ensure_dir(UPLOAD_DIR)


@router.post("/analyze-chunk")
async def analyze_chunk(
    file: UploadFile = File(...),

    # ===== METADATA =====
    drone_id: str = Form(...),
    mission_id: str = Form(...),
    sequence_number: int = Form(...),
    timestamp: str = Form(...),

    fps: int = Form(...),
    frame_width: int = Form(...),
    frame_height: int = Form(...),

    chunk_duration: int = Form(...),
    drone_role: str = Form(...),
    topic_name: str = Form(...),
):
    file_ext = os.path.splitext(file.filename)[1].lower()

    allowed_ext = [".mp4", ".avi", ".mov", ".mkv"]

    if file_ext not in allowed_ext:
        raise HTTPException(status_code=400, detail="Video only")

    save_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        pipeline_result = run_pipeline_file(save_path)

        # ===== FINAL RESPONSE =====
        return {
            "status": "success",

            # Returns metadata to the frontend
            "metadata": {
                "drone_id": drone_id,
                "mission_id": mission_id,
                "sequence_number": sequence_number,
                "timestamp": timestamp,
                "fps": fps,
                "frame_width": frame_width,
                "frame_height": frame_height,
                "chunk_duration": chunk_duration,
                "drone_role": drone_role,
                "topic_name": topic_name,
            },

            # Returns AI results to the frontend
            "ai_result": pipeline_result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))