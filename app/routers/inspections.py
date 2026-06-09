import os
import cv2
import tempfile
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.db import models

# calling the AI pipeline function
from app.services.pipeline_service import run_pipeline_file

# Disable OpenCL to prevent Docker crashes with OpenCV
os.environ["OPENCV_OPENCL_RUNTIME"] = "disabled"

router = APIRouter(prefix="/inspections", tags=["inspections"])

@router.post("/predict")
async def predict(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    
    # 1. Create a single "Inspection Process" in the database (Your task as a Partner)
    new_inspection = models.Inspection(
        title=f"فحص آلي لعدد {len(files)} ملف/ملفات",
        status="completed"
    )
    db.add(new_inspection)
    db.commit()
    db.refresh(new_inspection)

    all_results = []
    total_panels = 0

    # 2. Iterate through all the uploaded files
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if not ext:
            ext = ".jpg" 
            
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        try:
            # 3. Send the path to the comprehensive AI function (AI team's code)
            # This function will return a dictionary containing detections and other details
            pipeline_result = run_pipeline_file(temp_file_path)
            
            results = pipeline_result.get("detections", [])
            
            all_results.append({
                "filename": file.filename,
                "pipeline_data": pipeline_result 
            })
            total_panels += len(results)

            # 4. Save the detailed results for each panel (Detections) in the database
            for res in results:
                new_result = models.DetectionResult(
                    inspection_id=new_inspection.id,
                    fault_type=res.get("fault_type", "unknown"),
                    confidence=res.get("confidence", 0.0),
                    box_coordinates=res.get("box", {})
                )
                db.add(new_result)
                
        except Exception as e:
            # If a processing error occurs, print it in the terminal and proceed to the next file
            print(f"Error processing file {file.filename}: {str(e)}")
            continue
            
        finally:
            # 5. Server cleanup: Delete the temporary file to free up space
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    db.commit()

    # 6. Final response to the browser
    return {
        "status": "success",
        "inspection_id": new_inspection.id,
        "num_files_processed": len(files),
        "num_panels_detected": total_panels,
        "results": all_results
    }