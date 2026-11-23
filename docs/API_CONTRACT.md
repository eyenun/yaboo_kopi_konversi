# Kontrak API Backend - Yaboo Kopi (Tim A26-CS216)

Base URL Lokal:
- Web / Desktop: `http://127.0.0.1:8000/api/v1`
- Emulator Android: `http://10.0.2.2:8000/api/v1`

---

## 1. Analisis Transaksi POS & Prediksi Stok
- **Endpoint:** `POST /api/v1/analyze-pos`
- **Content-Type:** `multipart/form-data`
- **Body Parameter:** `file` (berkas `.csv` dengan kolom minimal: `tanggal`, `nama_produk`, `qty`)

### Response Sukses (`200 OK`)
```json
{
  "status": "success",
  "nama_file_diproses": "synthetic_pos_yaboo_1200.csv",
  "total_omset_periode": 43009000.0,
  "rata_rata_harian": 318585.19,
  "skor_kualitas_data": 100.0,
  "catatan_audit_pii": "Audit Privasi: 2 kolom PII (nama_pelanggan, no_hp_pelanggan) otomatis disanitasi.",
  "tren_penjualan": [
    {
      "tanggal": "2026-07-01",
      "total_omset": 180000.0,
      "jumlah_transaksi": 6
    }
  ],
  "prediksi_kebutuhan_bahan": [
    {
      "nama_bahan": "Biji Kopi Arabika House Blend",
      "satuan": "kg",
      "stok_prediksi_7_hari": 2.18,
      "estimasi_biaya_satuan": 185000.0,
      "status_prioritas": "Tinggi"
    }
  ],
  "rekomendasi_ai": {
    "mode_sumber": "gemini_live",
    "ringkasan_kondisi": "...",
    "jadwal_belanja_disarankan": ["..."],
    "total_anggaran_estimasi": 758125.0,
    "potensi_hemat_grosir": 60650.0,
    "catatan_strategis": "..."
  }
}
```

### Response Gagal Validasi (`400 Bad Request`)
Dikembalikan jika format bukan `.csv` atau skor kebersihan data di bawah 85%:
```json
{
  "detail": "Quality Gate GAGAL! Skor kualitas data 72.5% berada di bawah batas minimum 85.0%."
}
```

---

## 2. Konsultasi Interaktif AI Advisor
- **Endpoint:** `POST /api/v1/chat-advisor`
- **Content-Type:** `application/json`

### Request Body
```json
{
  "pertanyaan": "Kalau modal belanja minggu ini cuma Rp500.000, bahan baku mana yang wajib saya dahulukan?",
  "konteks_analisis": {
    "total_anggaran_estimasi": 758125,
    "prediksi_kebutuhan_bahan": []
  }
}
```
*(Catatan: `konteks_analisis` bersifat opsional—kirimkan objek hasil response `/analyze-pos` terakhir jika tersedia agar jawaban AI menyesuaikan angka stok kedai).*

### Response Sukses (`200 OK`)
```json
{
  "status": "success",
  "mode_sumber": "gemini_live",
  "jawaban": "..."
}
```