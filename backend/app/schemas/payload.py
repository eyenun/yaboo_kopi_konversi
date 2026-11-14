from pydantic import BaseModel
from typing import List


class DailySalesPoint(BaseModel):
    tanggal: str
    total_omset: float
    jumlah_transaksi: int


class StockForecastItem(BaseModel):
    nama_bahan: str
    satuan: str
    stok_prediksi_7_hari: float
    estimasi_biaya_satuan: float
    status_prioritas: str  # "Tinggi" | "Sedang" | "Aman"


class AIAdviceOutput(BaseModel):
    mode_sumber: str  # "gemini_live" | "mock_setup" | "rule_based_fallback"
    ringkasan_kondisi: str
    jadwal_belanja_disarankan: List[str]
    total_anggaran_estimasi: float
    potensi_hemat_grosir: float
    catatan_strategis: str


class AnalysisResponse(BaseModel):
    status: str
    nama_file_diproses: str
    total_omset_periode: float
    rata_rata_harian: float
    tren_penjualan: List[DailySalesPoint]
    prediksi_kebutuhan_bahan: List[StockForecastItem]
    rekomendasi_ai: AIAdviceOutput
