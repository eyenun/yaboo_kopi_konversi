from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.payload import AnalysisResponse
from app.services.ml_pipeline import run_dummy_forecast_pipeline
from app.services.gemini_service import get_procurement_advice

router = APIRouter()


@router.post("/analyze-pos", response_model=AnalysisResponse)
async def analyze_pos_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Format berkas harus berupa .csv")

    # 1. Jalankan pipeline data & prediksi stok (saat ini masih dummy)
    ml_result = run_dummy_forecast_pipeline(file.filename)

    # 2. Jalankan AI Advisor berdasarkan hasil prediksi stok
    ai_advice = await get_procurement_advice(ml_result["prediksi_kebutuhan_bahan"])

    return {
        "status": "success",
        **ml_result,
        "rekomendasi_ai": ai_advice,
    }
