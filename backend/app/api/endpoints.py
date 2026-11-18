from app.schemas.payload import (
    AnalysisResponse,
    ChatAdvisorRequest,
    ChatAdvisorResponse,
)
from app.services.csv_parser import DataQualityError
from app.services.gemini_service import (
    get_advisor_chat_reply,
    get_procurement_advice,
)
from app.services.ml_pipeline import run_pos_forecast_pipeline
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()


@router.post("/analyze-pos", response_model=AnalysisResponse)
async def analyze_pos_csv(file: UploadFile = File(...)):
  if not file.filename or not file.filename.lower().endswith(".csv"):
    raise HTTPException(
        status_code=400, detail="Format berkas harus berupa .csv"
    )

  file_bytes = await file.read()
  if not file_bytes:
    raise HTTPException(status_code=400, detail="Berkas CSV yang diunggah kosong.")

  # 1. Jalankan pipeline validasi kualitas data, sanitasi PII, & prediksi stok 7 hari
  try:
    ml_result = run_pos_forecast_pipeline(file_bytes, file.filename)
  except DataQualityError as dq_err:
    raise HTTPException(status_code=400, detail=str(dq_err))
  except Exception as exc:
    raise HTTPException(
        status_code=400,
        detail=f"Gagal memproses struktur CSV: {str(exc)}",
    )

  # 2. Jalankan AI Procurement Advisor berdasarkan hasil prediksi stok eksak
  ai_advice = await get_procurement_advice(
      ml_result["prediksi_kebutuhan_bahan"]
  )

  return {
      "status": "success",
      **ml_result,
      "rekomendasi_ai": ai_advice,
  }


@router.post("/chat-advisor", response_model=ChatAdvisorResponse)
async def chat_with_advisor(payload: ChatAdvisorRequest):
  reply = await get_advisor_chat_reply(
      pertanyaan=payload.pertanyaan,
      konteks_analisis=payload.konteks_analisis,
  )
  return {
      "status": "success",
      "mode_sumber": reply["mode_sumber"],
      "jawaban": reply["jawaban"],
  }