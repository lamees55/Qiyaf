from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/notifications", tags=["Notifications"])

class Notification(BaseModel):
    id: int
    message: str
    timestamp: datetime
    is_read: bool = False

fake_notifications = [
    Notification(id=1, message="Starting UAV flight... ", timestamp=datetime.now(), is_read=True),
    Notification(id=2, message="Defect detected in Panel #12! ", timestamp=datetime.now(), is_read=False)
]

@router.get("/", response_model=List[Notification])
async def get_all_notifications():
    """جلب قائمة التنبيهات الأخيرة"""
    return fake_notifications

@router.post("/mark-read/{notif_id}")
async def mark_as_read(notif_id: int):
    """تحديد تنبيه معين كـ 'مقروء'"""
    for n in fake_notifications:
        if n.id == notif_id:
            n.is_read = True
            return {"status": "success", "message": f"Notification {notif_id} marked as read"}
    raise HTTPException(status_code=404, detail="Notification not found")