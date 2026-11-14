from typing import List, Dict, Any
from app.core.config import settings
from app.services.fallback_service import generate_rule_based_advice


async def get_procurement_advice(forecast_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Selama tahap setup (API Key belum dipasang), kembalikan respons simulasi terstruktur
    if not settings.is_gemini_ready:
        return generate_rule_based_advice(forecast_items, mode="mock_setup")

    try:
        # Nantinya pada Sprint 2, panggilan resmi google-genai SDK dipasang di blok ini
        return generate_rule_based_advice(forecast_items, mode="gemini_live")
    except Exception:
        return generate_rule_based_advice(forecast_items, mode="rule_based_fallback")
