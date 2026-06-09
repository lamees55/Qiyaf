from .core.celery_config import celery_app
import time

@celery_app.task
def process_solar_image(image_path: str):
    # Simulate image processing (e.g., running the YOLO model)
    print(f"Starting analysis for: {image_path}")
    time.sleep(10)  
    return {"status": "Completed", "defects_found": 3, "image": image_path}