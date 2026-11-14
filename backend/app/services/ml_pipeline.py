from typing import Dict, Any


def run_dummy_forecast_pipeline(filename: str) -> Dict[str, Any]:
    """
    Placeholder untuk tim Data Science (Gaida, Syahril, Ellen).
    Nantinya diganti dengan fungsi pembersihan CSV POS Santai Scale & inferensi model .joblib.
    """
    return {
        "nama_file_diproses": filename,
        "total_omset_periode": 14850000.0,
        "rata_rata_harian": 2121428.0,
        "tren_penjualan": [
            {"tanggal": "2026-11-08", "total_omset": 1950000.0, "jumlah_transaksi": 78},
            {"tanggal": "2026-11-09", "total_omset": 2300000.0, "jumlah_transaksi": 92},
            {"tanggal": "2026-11-10", "total_omset": 2114280.0, "jumlah_transaksi": 84},
        ],
        "prediksi_kebutuhan_bahan": [
            {
                "nama_bahan": "Biji Kopi House Blend",
                "satuan": "kg",
                "stok_prediksi_7_hari": 6.5,
                "estimasi_biaya_satuan": 185000.0,
                "status_prioritas": "Tinggi",
            },
            {
                "nama_bahan": "Susu UHT Full Cream",
                "satuan": "liter",
                "stok_prediksi_7_hari": 42.0,
                "estimasi_biaya_satuan": 19500.0,
                "status_prioritas": "Tinggi",
            },
            {
                "nama_bahan": "Gula Aren Cair",
                "satuan": "liter",
                "stok_prediksi_7_hari": 10.0,
                "estimasi_biaya_satuan": 32000.0,
                "status_prioritas": "Sedang",
            },
        ],
    }
