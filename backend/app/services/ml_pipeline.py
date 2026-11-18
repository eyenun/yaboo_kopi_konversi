import io
from typing import Any, Dict
from app.services.csv_parser import DataQualityError, YabooPOSPreprocessor
import pandas as pd


def _read_csv_flexible(file_bytes: bytes) -> pd.DataFrame:
  """Membaca CSV dengan toleransi pemisah koma (,) maupun titik koma (;) khas Excel Indonesia."""
  for encoding in ("utf-8-sig", "utf-8", "latin-1"):
    try:
      df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
      if len(df.columns) == 1:
        df_semi = pd.read_csv(
            io.BytesIO(file_bytes), sep=";", encoding=encoding
        )
        if len(df_semi.columns) > 1:
          return df_semi
      return df
    except UnicodeDecodeError:
      continue
  raise DataQualityError(
      "Format encoding berkas CSV tidak didukung. Gunakan UTF-8."
  )


def run_pos_forecast_pipeline(
    file_bytes: bytes, filename: str
) -> Dict[str, Any]:
  """
    Pipeline terintegrasi:
    1. Validasi & Sanitasi PII via YabooPOSPreprocessor (Gaida)
    2. Agregasi tren penjualan harian untuk grafik mobile (Ellen)
    3. Proyeksi kebutuhan bahan baku 7 hari berbasis rolling-7 (siap ditimpa model .joblib Syahril)
    """
  df_raw = _read_csv_flexible(file_bytes)

  preprocessor = YabooPOSPreprocessor(min_quality_score=85.0)
  df_clean, quality_report = preprocessor.clean_and_validate(df_raw)
  daily_df = preprocessor.build_daily_ml_features(df_clean)

  total_omset_periode = round(float(daily_df["total_omset_idr"].sum()), 2)
  rata_rata_harian = round(float(daily_df["total_omset_idr"].mean()), 2)

  tren_penjualan = [
      {
          "tanggal": str(row["tanggal"]),
          "total_omset": float(row["total_omset_idr"]),
          "jumlah_transaksi": int(row["jumlah_transaksi"]),
      }
      for _, row in daily_df.iterrows()
  ]

  # Ambil rata-rata bergerak 7 hari terakhir sebagai baseline prediksi 7 hari ke depan
  latest = daily_df.iloc[-1]
  kopi_7d = max(round(float(latest["kopi_kg_rolling7"]) * 7, 2), 0.5)
  susu_7d = max(round(float(latest["susu_liter_rolling7"]) * 7, 2), 1.0)
  sirup_7d = max(round(float(latest["sirup_liter_rolling7"]) * 7, 2), 0.5)

  prediksi_kebutuhan_bahan = [
      {
          "nama_bahan": "Biji Kopi Arabika House Blend",
          "satuan": "kg",
          "stok_prediksi_7_hari": kopi_7d,
          "estimasi_biaya_satuan": 185000.0,
          "status_prioritas": "Tinggi" if kopi_7d >= 1.5 else "Sedang",
      },
      {
          "nama_bahan": "Susu UHT Full Cream",
          "satuan": "liter",
          "stok_prediksi_7_hari": susu_7d,
          "estimasi_biaya_satuan": 19500.0,
          "status_prioritas": "Tinggi" if susu_7d >= 10.0 else "Sedang",
      },
      {
          "nama_bahan": "Sirup Palm Sugar",
          "satuan": "liter",
          "stok_prediksi_7_hari": sirup_7d,
          "estimasi_biaya_satuan": 32000.0,
          "status_prioritas": "Sedang" if sirup_7d >= 2.0 else "Aman",
      },
  ]

  stripped_cols = quality_report.get("pii_columns_stripped", [])
  if stripped_cols:
    catatan_audit_pii = (
        f"Audit Privasi: {len(stripped_cols)} kolom PII"
        f" ({', '.join(stripped_cols)}) otomatis disanitasi."
    )
  else:
    catatan_audit_pii = (
        "Audit Privasi: Aman (tidak ditemukan atribut PII pelanggan)."
    )

  return {
      "nama_file_diproses": filename,
      "total_omset_periode": total_omset_periode,
      "rata_rata_harian": rata_rata_harian,
      "tren_penjualan": tren_penjualan,
      "prediksi_kebutuhan_bahan": prediksi_kebutuhan_bahan,
      "skor_kualitas_data": quality_report.get("quality_score_pct"),
      "catatan_audit_pii": catatan_audit_pii,
  }