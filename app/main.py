from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # استيراد مكتبة الملفات الثابتة لتشغيل مسار الصور
import os

from app.routers import auth, inspections, upload, prediction, inference
from app.core.database import engine
from app.db import models
from app.core.config import settings

# إنشاء الجداول
models.SQLModel.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Solar Panel Fault Detection using UAV and AI",
    version="1.0.0"
)

# --- إضافة إعدادات الـ CORS للربط مع الفرونت آند ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- 🚀 الـ Middleware السحري لتخطي شاشة تحذير ngrok وتمرير الصور فوراً ---
@app.middleware("http")
async def add_ngrok_skip_header(request: Request, call_next):
    response: Response = await call_next(request)
    # إضافة الهيدر الذي يمنع ngrok من حجب الصور والطلبات عن المتصفح
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

# --- 📸 مشاركة وعرض مجلد الصور المخرجة من الذكاء الاصطناعي (Static Serve) ---
# يقوم بمشاركة المجلد الموجود داخل حاوية الدوكر ليكون متاحاً عبر الرابط مباشرة
print("AI OUTPUTS EXISTS:", os.path.exists("/app/app/ai_outputs"))
if os.path.exists("/app/app/ai_outputs"):
    app.mount("/ai_outputs", StaticFiles(directory="/app/app/ai_outputs"), name="ai_outputs")

# --- ربط المسارات (Routers) ---
app.include_router(auth.router)
app.include_router(inspections.router)
app.include_router(inference.router)
app.include_router(upload.router)
#app.include_router(prediction.router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "مرحباً بكم في نظام قياف - الباك آند يعمل بنجاح",
        "project": settings.PROJECT_NAME  
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}