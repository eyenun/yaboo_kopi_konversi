# Yaboo Kopi — AI Inventory & Cashflow Management

Sistem prediksi kebutuhan bahan baku dan asisten perencanaan belanja berbasis AI untuk UMKM Yaboo Kopi Palu.

## Struktur Repositori
- `mobile_app/` — Aplikasi Android berbasis Flutter (Uploader CSV, Dasbor Analitik, AI Advisor).
- `backend/` — REST API berbasis FastAPI, pipeline Machine Learning prediksi stok, dan integrasi Gemini API.
- `docs/` — Dokumentasi teknis, kontrak API, dan artefak pengujian sistem.

## Anggota Tim
- **Nur Ainun** — Lead Backend & Next-Gen AI Engineer
- **Ahmad Jayadi** — Lead Frontend Mobile (Flutter)
- **Gaida Muthmainnah** — Data Science (Data Wrangling & Synthetic POS)
- **Moh. Syahril A. K.** — Data Science (Stock Forecasting Model)
- **Ellen Salua** — Data Science (Financial Aggregation & Analytics UI)

## Cara Menjalankan Lokal
### Backend (FastAPI)
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Mobile App (Flutter)
```bash
cd mobile_app
flutter pub get
flutter run
```