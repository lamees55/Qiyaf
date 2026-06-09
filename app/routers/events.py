from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.database import engine
from app.db.models import User 

router = APIRouter(prefix="/events", tags=["System Events"])

@router.get("/health")
async def health_check():
    """فحص حالة السيرفر"""
    return {"status": "healthy", "service": "EyeFact API"}

@router.get("/db-status")
async def check_db():
    """فحص الاتصال بقاعدة البيانات"""
    try:
        with Session(engine) as session:
            # Try making a simple request to verify the connection
            session.exec(select(User)).first()
        return {"status": "connected", "database": "PostgreSQL"}
    except Exception as e:
        return {"status": "error", "message": str(e)}