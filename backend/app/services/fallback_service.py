from typing import List, Dict, Any


def generate_rule_based_advice(
    forecast_items: List[Dict[str, Any]], mode: str = "rule_based_fallback"
) -> Dict[str, Any]:
    total_biaya = sum(
        item["stok_prediksi_7_hari"] * item["estimasi_biaya_satuan"]
        for item in forecast_items
    )
    prioritas_tinggi = [
        f"{item['nama_bahan']} ({item['stok_prediksi_7_hari']} {item['satuan']})"
        for item in forecast_items
        if item["status_prioritas"] == "Tinggi"
    ]

    return {
        "mode_sumber": mode,
        "ringkasan_kondisi": (
            f"Terdapat {len(prioritas_tinggi)} bahan baku berprioritas tinggi "
            "yang perlu segera dipesan untuk mengamankan operasional 7 hari ke depan."
        ),
        "jadwal_belanja_disarankan": [
            f"Senin Pagi (Belanja Utama): {', '.join(prioritas_tinggi) or 'Stok aman'}",
            "Kamis Sore (Restock Menjelang Akhir Pekan): Cek ulang sisa susu & es batu",
        ],
        "total_anggaran_estimasi": round(total_biaya, 2),
        "potensi_hemat_grosir": round(total_biaya * 0.08, 2),
        "catatan_strategis": (
            "Satukan pembelian biji kopi dan susu UHT dalam satu pengiriman grosir "
            "untuk menekan ongkos kirim dan menjaga rasio kas harian tetap sehat."
        ),
    }
