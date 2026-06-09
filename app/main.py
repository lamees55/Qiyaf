from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles 
import os

from app.routers import auth, inspections, upload, prediction, inference
from app.core.database import engine
from app.db import models
from app.core.config import settings

models.SQLModel.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Solar Panel Fault Detection using UAV and AI",
    version="1.0.0"
)

# --- Add CORS configurations for frontend integration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- Middleware to bypass ngrok warning screen and allow direct image loading ---
@app.middleware("http")
async def add_ngrok_skip_header(request: Request, call_next):
    response: Response = await call_next(request)
    # Add the header that prevents ngrok from blocking images and requests from the browser
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

# --- Serve the static directory containing the AI output images ---
# Serves the directory inside the Docker container to be accessible directly via URL
print("AI OUTPUTS EXISTS:", os.path.exists("/app/app/ai_outputs"))
if os.path.exists("/app/app/ai_outputs"):
    app.mount("/ai_outputs", StaticFiles(directory="/app/app/ai_outputs"), name="ai_outputs")

# --- Include Routers ---
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