import json
from typing import Any, Dict, List
from app.core.config import settings
from app.schemas.payload import AIAdviceOutput
from app.services.fallback_service import generate_rule_based_advice
from google import genai
from google.genai import types

SYSTEM_PROMPT = """
Kamu adalah konsultan manajemen inventaris dan arus kas (AI Procurement Advisor) khusus untuk UMKM kedai kopi 'Yaboo Kopi' di Palu.
Tugasmu adalah menganalisis data prediksi kebutuhan bahan baku 7 hari ke depan beserta estimasi harga satuannya, lalu menyusun strategi belanja yang efisien agar arus kas kedai tetap sehat dan tidak kehabisan stok saat jam ramai.

Aturan analisis:
1. Hitung total_anggaran_estimasi secara akurat berdasarkan jumlah stok_prediksi_7_hari dikali estimasi_biaya_satuan untuk seluruh bahan.
2. Hitung potensi_hemat_grosir secara realistis (sekitar 5% hingga 10% dari total anggaran jika bahan berprioritas tinggi dibeli sekaligus di awal minggu).
3. Susun 2 sampai 3 poin jadwal_belanja_disarankan yang praktis (pisahkan belanja utama awal minggu dan restock bahan segar menjelang akhir pekan).
4. Isi catatan_strategis dengan saran singkat, taktis, dan membumi untuk operasional kedai kopi take & go.
5. Gunakan bahasa Indonesia yang lugas dan profesional.
"""


async def get_procurement_advice(
    forecast_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
  if not settings.is_gemini_ready:
    return generate_rule_based_advice(forecast_items, mode="mock_setup")

  candidate_models = list(
      dict.fromkeys([
          settings.GEMINI_MODEL,
          "gemini-3.5-flash-lite",
          "gemini-3.1-flash-lite",
          "gemini-3.7-flash",
          "gemini-3.6-flash",
      ])
  )

  client = genai.Client(api_key=settings.GEMINI_API_KEY)
  prompt_input = (
      "Berikut adalah data prediksi kebutuhan bahan baku Yaboo Kopi untuk 7"
      " hari ke depan:\n"
      f"{json.dumps(forecast_items, indent=2, ensure_ascii=False)}\n\n"
      "Susun rekomendasi perencanaan belanja berdasarkan data tersebut."
  )

  last_error = None
  for model_name in candidate_models:
    try:
      response = await client.aio.models.generate_content(
          model=model_name,
          contents=prompt_input,
          config=types.GenerateContentConfig(
              system_instruction=SYSTEM_PROMPT,
              response_mime_type="application/json",
              response_schema=AIAdviceOutput,
              temperature=0.3,
          ),
      )

      print(f"[Gemini Success] Berhasil dijawab oleh model: {model_name}")
      result = json.loads(response.text)
      result["mode_sumber"] = "gemini_live"
      return result

    except Exception as e:
      last_error = e
      print(
          f"[Gemini Retry] Model '{model_name}' sibuk/gagal, lanjut model"
          " berikutnya..."
      )
      continue

  print(
      "[Gemini Service Warning] Semua model sibuk, beralih ke fallback:"
      f" {last_error}"
  )
  return generate_rule_based_advice(forecast_items, mode="rule_based_fallback")