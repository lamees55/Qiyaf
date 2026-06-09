from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str 

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

class DetectionResultBase(BaseModel):
    fault_type: str
    confidence: float
    box_coordinates: Any 
    image_path: str

class DetectionResult(DetectionResultBase):
    id: int
    inspection_id: int
    class Config:
        from_attributes = True

class InspectionBase(BaseModel):
    title: str

class InspectionCreate(InspectionBase):
    pass

class Inspection(InspectionBase):
    id: int
    status: str
    created_at: datetime
    results: List[DetectionResult] = [] 
    class Config:
        from_attributes = True