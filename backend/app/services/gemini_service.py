import json
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from app.core.config import settings
from app.schemas.payload import AIAdviceOutput
from app.services.fallback_service import generate_rule_based_advice

PROCUREMENT_SYSTEM_PROMPT = """
Kamu adalah AI Procurement & Cashflow Advisor khusus untuk UMKM kedai kopi 'Yaboo Kopi' (konsep take & go) di Palu.
Tugasmu adalah menganalisis kebutuhan bahan baku 7 hari ke depan agar pemilik kedai tidak terjebak belanja eceran harian yang menguras arus kas.

Aturan analisis:
1. Gunakan angka `total_anggaran_eksak` yang sudah dihitung sistem sebagai patokan mutlak `total_anggaran_estimasi`.
2. Hitung `potensi_hemat_grosir` secara realistis (5% hingga 10% dari total anggaran jika item prioritas Tinggi dibeli sekaligus di awal minggu).
3. Susun 2 sampai 3 poin `jadwal_belanja_disarankan` yang praktis, mempertimbangkan lonjakan transaksi akhir pekan (Jumat–Minggu) serta tanggal gajian.
4. Isi `catatan_strategis` dengan saran taktis dan ringkas yang langsung bisa dieksekusi oleh pemilik kedai.
5. Gunakan bahasa Indonesia yang lugas, ramah UMKM, dan profesional.
"""

CHAT_SYSTEM_PROMPT = """
Kamu adalah asisten konsultan keuangan dan stok bahan baku untuk 'Yaboo Kopi' di Palu.
Jawab pertanyaan pemilik kedai secara singkat, padat, praktis, dan berbasis data POS yang dilampirkan.
Jika pemilik kedai menanyakan simulasi keterbatasan modal belanja, prioritaskan pembelian bahan baku berstatus 'Tinggi' (kopi dan susu UHT) terlebih dahulu sebelum item pelengkap.
Gunakan format poin singkat jika menyebutkan langkah tindakan, tanpa basa-basi panjang.
"""


def _get_candidate_models() -> List[str]:
    return list(
        dict.fromkeys([
            settings.GEMINI_MODEL,
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
        ])
    )


async def get_procurement_advice(
    forecast_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    exact_total_budget = round(
        sum(
            float(item.get("stok_prediksi_7_hari", 0))
            * float(item.get("estimasi_biaya_satuan", 0))
            for item in forecast_items
        ),
        2,
    )

    if not settings.is_gemini_ready:
        fallback = generate_rule_based_advice(forecast_items, mode="mock_setup")
        fallback["total_anggaran_estimasi"] = exact_total_budget
        return fallback

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt_input = (
        "Data prediksi kebutuhan bahan baku Yaboo Kopi 7 hari ke depan:\n"
        f"{json.dumps(forecast_items, indent=2, ensure_ascii=False)}\n\n"
        f"Total anggaran eksak hasil perhitungan sistem: Rp{exact_total_budget:,.0f}\n"
        "Susun rekomendasi jadwal belanja grosir dan strategi arus kas berdasarkan data tersebut."
    )

    last_error = None
    for model_name in _get_candidate_models():
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt_input,
                config=types.GenerateContentConfig(
                    system_instruction=PROCUREMENT_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=AIAdviceOutput,
                    temperature=0.3,
                ),
            )

            print(f"[Gemini Success] analyze-pos dijawab oleh model: {model_name}")
            result = json.loads(response.text)
            result["mode_sumber"] = "gemini_live"
            result["total_anggaran_estimasi"] = exact_total_budget

            max_discount = round(exact_total_budget * 0.15, 2)
            if (
                result.get("potensi_hemat_grosir", 0) > max_discount
                or result.get("potensi_hemat_grosir", 0) < 0
            ):
                result["potensi_hemat_grosir"] = round(exact_total_budget * 0.07, 2)

            return result

        except Exception as e:
            last_error = e
            print(f"[Gemini Retry] Model '{model_name}' gagal ({type(e).__name__}), lanjut model berikutnya...")
            continue

    print(f"[Gemini Service Warning] Semua model gagal, beralih ke fallback: {last_error}")
    fallback = generate_rule_based_advice(forecast_items, mode="rule_based_fallback")
    fallback["total_anggaran_estimasi"] = exact_total_budget
    return fallback


async def get_advisor_chat_reply(
    pertanyaan: str,
    konteks_analisis: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    if not settings.is_gemini_ready:
        return {
            "mode_sumber": "rule_based_fallback",
            "jawaban": (
                "Mode AI live belum aktif. Dahulukan belanja Kopi Arabika dan Susu UHT "
                "di awal minggu sebelum memesan sirup atau kemasan tambahan."
            ),
        }

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    context_str = (
        json.dumps(konteks_analisis, indent=2, ensure_ascii=False)
        if konteks_analisis
        else "Belum ada data POS yang diunggah pada sesi ini."
    )
    prompt_input = (
        f"Konteks data toko saat ini:\n{context_str}\n\n"
        f"Pertanyaan pemilik kedai: {pertanyaan}"
    )

    last_error = None
    for model_name in _get_candidate_models():
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt_input,
                config=types.GenerateContentConfig(
                    system_instruction=CHAT_SYSTEM_PROMPT,
                    temperature=0.4,
                ),
            )
            print(f"[Gemini Success] chat-advisor dijawab oleh model: {model_name}")
            return {
                "mode_sumber": "gemini_live",
                "jawaban": response.text.strip(),
            }
        except Exception as e:
            last_error = e
            print(f"[Gemini Retry] Chat model '{model_name}' gagal ({type(e).__name__}), lanjut...")
            continue

    print(f"[Gemini Chat Warning] Semua model gagal: {last_error}")
    return {
        "mode_sumber": "rule_based_fallback",
        "jawaban": (
            "Layanan Gemini sedang sibuk sementara. Saran cepat: alokasikan 70% "
            "modal belanja untuk stok inti (Kopi Arabika & Susu UHT) dan sisakan "
            "30% untuk restock menjelang hari Jumat."
        ),
    }