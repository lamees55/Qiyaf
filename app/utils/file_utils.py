import os
import shutil
from fastapi import UploadFile
from app.core.config import settings

def save_upload_file(upload_file: UploadFile) -> str:
    """وظيفته يحفظ الصورة اللي يرفعها اليوزر في مجلد uploads ويرجع لنا مسارها"""
    if not os.path.exists(settings.UPLOAD_DIR):
        os.makedirs(settings.UPLOAD_DIR)
    
    file_path = os.path.join(settings.UPLOAD_DIR, upload_file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return file_path