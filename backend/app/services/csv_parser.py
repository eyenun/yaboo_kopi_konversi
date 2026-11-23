import os
import re
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd


class DataQualityError(Exception):
    """Exception khusus ketika dataset POS gagal melewati Data Quality Gate."""


class YabooPOSPreprocessor:
    """
    Pipeline Preprocessing, Sanitasi PII, Data Quality Gate, dan Konversi
    Bill of Materials (BOM) Asli untuk UMKM Yaboo Kopi.
    """

    PII_COLUMNS = [
        "pelanggan", "nama_pelanggan", "customer_name", "nama",
        "no._hp", "no_hp", "no_hp_pelanggan", "phone", "telepon",
        "alamat", "address", "email", "kasir"
    ]

    # Resep Asli per Porsi/Cup berdasarkan sheet 'Resep_Bahan_Baku' Yaboo Kopi
    YABOO_BOM_RECIPES: Dict[str, Dict[str, float]] = {
        "americano": {"kopi_gr": 9, "susu_ml": 0, "krimer_gr": 0, "powder_aren_gr": 0, "sirup_ml": 0, "skm_gr": 0},
        "apple americano": {"kopi_gr": 9, "susu_ml": 0, "krimer_gr": 0, "powder_aren_gr": 0, "sirup_ml": 20, "skm_gr": 0},
        "aren": {"kopi_gr": 8, "susu_ml": 80, "krimer_gr": 12, "powder_aren_gr": 15, "sirup_ml": 5, "skm_gr": 0},
        "seliter aren": {"kopi_gr": 64, "susu_ml": 640, "krimer_gr": 96, "powder_aren_gr": 120, "sirup_ml": 40, "skm_gr": 0},
        "aren seliter": {"kopi_gr": 64, "susu_ml": 640, "krimer_gr": 96, "powder_aren_gr": 120, "sirup_ml": 40, "skm_gr": 0},
        "butterscotch seasalt": {"kopi_gr": 9, "susu_ml": 80, "krimer_gr": 8, "powder_aren_gr": 0, "sirup_ml": 15, "skm_gr": 10},
        "caramel": {"kopi_gr": 9, "susu_ml": 80, "krimer_gr": 8, "powder_aren_gr": 0, "sirup_ml": 15, "skm_gr": 10},
        "cokelat": {"kopi_gr": 0, "susu_ml": 80, "krimer_gr": 0, "powder_aren_gr": 0, "sirup_ml": 0, "skm_gr": 30},
        "eskopi alcho": {"kopi_gr": 9, "susu_ml": 80, "krimer_gr": 8, "powder_aren_gr": 0, "sirup_ml": 20, "skm_gr": 10},
        "hot kopi susu": {"kopi_gr": 9, "susu_ml": 0, "krimer_gr": 0, "powder_aren_gr": 0, "sirup_ml": 0, "skm_gr": 30},
        "ice kopsu": {"kopi_gr": 9, "susu_ml": 80, "krimer_gr": 8, "powder_aren_gr": 0, "sirup_ml": 0, "skm_gr": 10},
        "matcha latte": {"kopi_gr": 0, "susu_ml": 80, "krimer_gr": 0, "powder_aren_gr": 0, "sirup_ml": 0, "skm_gr": 15},
        "vanilla": {"kopi_gr": 0, "susu_ml": 0, "krimer_gr": 0, "powder_aren_gr": 0, "sirup_ml": 0, "skm_gr": 10},
    }

    def __init__(self, min_quality_score: float = 85.0):
        self.min_quality_score = min_quality_score

    @staticmethod
    def load_pos_file(filepath: str) -> pd.DataFrame:
        if filepath.lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(filepath, sheet_name=0)
        return pd.read_csv(filepath)

    @staticmethod
    def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        alias_map = {
            "no._pesanan": "transaction_id",
            "no_pesanan": "transaction_id",
            "no_struk": "transaction_id",
            "tgl": "tanggal",
            "date": "tanggal",
            "produk": "nama_produk",
            "menu": "nama_produk",
            "item": "nama_produk",
            "jumlah": "qty",
            "quantity": "qty",
            "harga_jual": "harga_satuan",
            "harga": "harga_satuan",
            "total_gross": "total_transaksi",
            "total": "total_transaksi",
            "subtotal": "total_transaksi",
        }
        return df.rename(columns={k: v for k, v in alias_map.items() if k in df.columns})

    @staticmethod
    def _parse_currency(val) -> float:
        if pd.isna(val):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        cleaned = re.sub(r"[^\d.]", "", str(val))
        return float(cleaned) if cleaned else 0.0

    def _map_bom_per_unit(self, product_name: str) -> pd.Series:
        name = str(product_name).strip().lower()
        recipe = self.YABOO_BOM_RECIPES.get(
            name,
            {"kopi_gr": 9, "susu_ml": 80, "krimer_gr": 8, "powder_aren_gr": 0, "sirup_ml": 0, "skm_gr": 0},
        )
        return pd.Series(recipe)

    def clean_and_validate(self, raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        df = self._normalize_column_names(raw_df)
        initial_rows = len(df)

        if initial_rows == 0:
            raise DataQualityError("File POS kosong (0 baris transaksi).")

        required_cols = {"tanggal", "nama_produk", "qty"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise DataQualityError(f"Kolom wajib tidak ditemukan di file POS: {missing_cols}")

        # 1. Sanitasi PII (Hapus identitas pelanggan & kasir)
        dropped_pii = [col for col in self.PII_COLUMNS if col in df.columns]
        df = df.drop(columns=dropped_pii, errors="ignore")

        # 2. Hapus duplikat berdasarkan No. Pesanan + Produk + Qty
        subset_dup = [c for c in ["transaction_id", "tanggal", "nama_produk", "qty"] if c in df.columns]
        before_dedup = len(df)
        df = df.drop_duplicates(subset=subset_dup).copy()
        duplicate_rows_removed = before_dedup - len(df)

        # 3. Parsing tanggal, qty, harga, dan HPP/laba
        df["tanggal"] = pd.to_datetime(df["tanggal"], errors="coerce")
        df["qty"] = pd.to_numeric(df["qty"], errors="coerce")
        df["nama_produk"] = df["nama_produk"].astype(str).str.strip()
        df["nama_produk"] = df["nama_produk"].replace({"Aren Seliter": "Seliter Aren"})

        if "harga_satuan" in df.columns:
            df["harga_satuan"] = df["harga_satuan"].apply(self._parse_currency)
        else:
            df["harga_satuan"] = 15000.0

        if "total_transaksi" in df.columns:
            df["total_transaksi"] = df["total_transaksi"].apply(self._parse_currency)
        else:
            df["total_transaksi"] = df["qty"] * df["harga_satuan"]

        if "hpp" in df.columns:
            df["total_hpp"] = df["hpp"].apply(self._parse_currency) * df["qty"]
        else:
            df["total_hpp"] = 0.0

        if "laba_bersih" in df.columns:
            df["laba_bersih"] = df["laba_bersih"].apply(self._parse_currency)
        else:
            df["laba_bersih"] = df["total_transaksi"] - df["total_hpp"]

        # 4. Filter baris anomali
        valid_mask = (
            df["tanggal"].notna()
            & (df["qty"] > 0)
            & (df["total_transaksi"] >= 0)
            & (df["nama_produk"] != "")
            & (~df["nama_produk"].str.lower().isin(["nan", "none", "null", "error"]))
        )
        invalid_rows_removed = int((~valid_mask).sum())
        df = df[valid_mask].copy()

        final_rows = len(df)
        quality_score = round((final_rows / initial_rows) * 100.0, 2)

        if quality_score < self.min_quality_score:
            raise DataQualityError(
                f"Quality Gate GAGAL! Skor kualitas data {quality_score}% berada di bawah batas minimum {self.min_quality_score}%."
            )

        # 5. Konversi Bill of Materials (BOM) Asli Yaboo Kopi
        bom_unit = df["nama_produk"].apply(self._map_bom_per_unit)
        for col in bom_unit.columns:
            df[f"pakai_{col}"] = df["qty"] * bom_unit[col]

        # Normalisasi satuan cup (Seliter Aren = 8 porsi Aren)
        df["cup_ekuivalen"] = np.where(df["nama_produk"] == "Seliter Aren", df["qty"] * 8, df["qty"])

        report = {
            "status": "PASSED",
            "initial_rows": initial_rows,
            "final_rows": final_rows,
            "duplicate_rows_removed": duplicate_rows_removed,
            "invalid_rows_removed": invalid_rows_removed,
            "pii_columns_stripped": dropped_pii,
            "quality_score_pct": quality_score,
            "date_range": f"{df['tanggal'].min().strftime('%Y-%m-%d')} s/d {df['tanggal'].max().strftime('%Y-%m-%d')}",
            "total_revenue_idr": int(df["total_transaksi"].sum()),
            "total_profit_idr": int(df["laba_bersih"].sum()),
        }
        return df, report

    def build_daily_ml_features(self, clean_df: pd.DataFrame) -> pd.DataFrame:
        df = clean_df.copy()
        df["tanggal_str"] = df["tanggal"].dt.strftime("%Y-%m-%d")

        # Lengkapi seluruh tanggal kalender agar deret waktu kontinyu
        full_dates = pd.date_range(df["tanggal"].min(), df["tanggal"].max(), freq="D")

        daily = (
            df.groupby("tanggal", as_index=False)
            .agg(
                jumlah_transaksi=("nama_produk", "count"),
                total_cup_terjual=("cup_ekuivalen", "sum"),
                total_omset_idr=("total_transaksi", "sum"),
                total_hpp_idr=("total_hpp", "sum"),
                laba_bersih_idr=("laba_bersih", "sum"),
                kopi_gr=("pakai_kopi_gr", "sum"),
                susu_ml=("pakai_susu_ml", "sum"),
                krimer_gr=("pakai_krimer_gr", "sum"),
                powder_aren_gr=("pakai_powder_aren_gr", "sum"),
                sirup_ml=("pakai_sirup_ml", "sum"),
                skm_gr=("pakai_skm_gr", "sum"),
            )
            .set_index("tanggal")
            .reindex(full_dates, fill_value=0)
            .rename_axis("tanggal")
            .reset_index()
        )

        # Konversi ke satuan pembelian gudang (Kg & Liter)
        daily["kopi_kg"] = (daily["kopi_gr"] / 1000.0).round(3)
        daily["susu_liter"] = (daily["susu_ml"] / 1000.0).round(3)
        daily["krimer_kg"] = (daily["krimer_gr"] / 1000.0).round(3)
        daily["powder_aren_kg"] = (daily["powder_aren_gr"] / 1000.0).round(3)
        daily["sirup_liter"] = (daily["sirup_ml"] / 1000.0).round(3)

        # Fitur kalender & lag dasar
        daily["hari_ke"] = daily["tanggal"].dt.day_of_week
        daily["is_weekend"] = (daily["hari_ke"] >= 4).astype(int)

        for col in ["kopi_kg", "susu_liter", "krimer_kg", "powder_aren_kg", "sirup_liter"]:
            daily[f"{col}_lag1"] = daily[col].shift(1).bfill().round(3)
            daily[f"{col}_rolling7"] = daily[col].shift(1).rolling(window=7, min_periods=1).mean().bfill().round(3)

        daily["tanggal"] = daily["tanggal"].dt.strftime("%Y-%m-%d")
        return daily


if __name__ == "__main__":
    service_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.abspath(os.path.join(service_dir, "..", ".."))

    raw_excel_path = os.path.join(backend_dir, "data", "raw", "rekap_per_transaksi_2026-11-23.xlsx")
    output_clean_trx = os.path.join(backend_dir, "data", "processed", "01_yaboo_real_transaksi_clean.csv")
    output_daily_csv = os.path.join(backend_dir, "data", "processed", "05_yaboo_stok_harian_ml_ready.csv")

    print(f"Membaca berkas POS asli Yaboo Kopi: {raw_excel_path}")
    processor = YabooPOSPreprocessor(min_quality_score=85.0)
    raw_pos = processor.load_pos_file(raw_excel_path)

    clean_pos, audit_report = processor.clean_and_validate(raw_pos)
    print("\n=== LAPORAN DATA QUALITY GATE & AUDIT PRIVASI (DATA ASLI) ===")
    for k, v in audit_report.items():
        print(f"- {k:<24}: {v}")

    os.makedirs(os.path.dirname(output_daily_csv), exist_ok=True)
    clean_pos.to_csv(output_clean_trx, index=False)

    daily_ml_df = processor.build_daily_ml_features(clean_pos)
    daily_ml_df.to_csv(output_daily_csv, index=False)

    print(f"\nDataset transaksi bersih disimpan ke : {output_clean_trx}")
    print(f"Dataset harian ML disimpan ke       : {output_daily_csv}")
    print(f"Total hari kalender                 : {len(daily_ml_df)} hari | Jumlah fitur: {daily_ml_df.shape[1]} kolom")