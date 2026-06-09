from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os

router = APIRouter(prefix="/storage", tags=["File Storage"])

# Define the upload/save directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-file")
async def upload_image(file: UploadFile = File(...)):
    # Ensure the file is of the correct type (optional but professional)
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save the file in the directory
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {
        "message": "File uploaded successfully",
        "file_name": file.filename,
        "path": file_path
    }