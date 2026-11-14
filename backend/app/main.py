from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import router as api_router

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0-setup",
    description="Backend API untuk Prediksi Stok & AI Procurement Advisor UMKM Yaboo Kopi",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1", tags=["POS Analytics & AI"])


@app.get("/", tags=["Health Check"])
def health_check():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "gemini_configured": settings.is_gemini_ready,
    }
