import os
import re
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd


class DataQualityError(Exception):
    """Exception khusus ketika berkas CSV gagal melewati ambang batas Data Quality Gate."""
    pass


class YabooPOSPreprocessor:
    """
    Modul Preprocessing, Audit Privasi (PII Sanitization), & Data Quality Gate
    untuk transaksi POS UMKM Yaboo Kopi (Capstone Team A26-CS216).
    """

    # 1. Kamus Pemetaan Nama Kolom (Adaptor Fleksibel untuk POS Sintetis & POS Real Yaboo)
    COLUMN_ALIASES: Dict[str, List[str]] = {
        "transaction_id": ["transaction_id", "id_transaksi", "no_struk", "invoice", "kode_transaksi", "id"],
        "tanggal": ["tanggal", "date", "tgl", "waktu_transaksi", "transaction_date", "created_at"],
        "nama_produk": ["nama_produk", "menu", "item", "produk", "product_name", "nama_menu"],
        "qty": ["qty", "jumlah", "quantity", "terjual", "unit"],
        "harga_satuan": ["harga_satuan", "harga", "price", "unit_price"],
        "total_transaksi": ["total_transaksi", "total", "total_harga", "total_spent", "subtotal"],
        "metode_bayar": ["metode_bayar", "payment_method", "pembayaran", "metode"],
    }

    # 2. Daftar Kata Kunci PII (Personally Identifiable Information) yang Wajib Dihapus
    PII_KEYWORDS: List[str] = [
        "nama_pelanggan", "customer_name", "pelanggan", "nama_cust", "nama_pembeli",
        "no_hp", "no_hp_pelanggan", "telepon", "phone", "whatsapp", "wa",
        "email", "alamat", "address", "nik", "ktp"
    ]

    # 3. Takaran Resep Standar per Cup (Bill of Materials) berbasis Kata Kunci Menu
    # Sesuaikan gram/ml di bawah ini saat catatan resep asli dari Kak Dani diterima
    RECIPE_KEYWORDS: List[Tuple[str, Dict[str, float]]] = [
        ("palm sugar", {"kopi_gr": 18.0, "susu_ml": 130.0, "sirup_ml": 25.0}),
        ("gula aren", {"kopi_gr": 18.0, "susu_ml": 130.0, "sirup_ml": 25.0}),
        ("kopi susu", {"kopi_gr": 18.0, "susu_ml": 120.0, "sirup_ml": 20.0}),
        ("americano", {"kopi_gr": 18.0, "susu_ml": 0.0, "sirup_ml": 0.0}),
        ("caffe latte", {"kopi_gr": 18.0, "susu_ml": 150.0, "sirup_ml": 0.0}),
        ("cappuccino", {"kopi_gr": 18.0, "susu_ml": 140.0, "sirup_ml": 0.0}),
        ("matcha", {"kopi_gr": 0.0, "susu_ml": 150.0, "sirup_ml": 15.0}),
        ("chocolate", {"kopi_gr": 0.0, "susu_ml": 150.0, "sirup_ml": 15.0}),
    ]
    DEFAULT_RECIPE: Dict[str, float] = {"kopi_gr": 18.0, "susu_ml": 120.0, "sirup_ml": 15.0}

    CORRUPT_TOKENS = {"", "nan", "none", "null", "error", "unknown", "n/a", "-"}

    def __init__(self, min_quality_score: float = 85.0):
        self.min_quality_score = min_quality_score

    @staticmethod
    def _clean_currency(val: Any) -> float:
        """Membersihkan penulisan Rupiah seperti 'Rp 18.000' atau '18,000' menjadi float."""
        if pd.isna(val):
            return np.nan
        s = str(val).strip().lower()
        if s in YabooPOSPreprocessor.CORRUPT_TOKENS:
            return np.nan
        cleaned = re.sub(r"[^0-9.-]", "", s.replace(".", "").replace(",", "."))
        try:
            return float(cleaned) if cleaned else np.nan
        except ValueError:
            return np.nan

    def _match_recipe(self, product_name: str) -> Dict[str, float]:
        """Mencocokkan nama menu kasir terhadap kamus resep bahan baku."""
        lower_name = product_name.lower()
        for keyword, recipe in self.RECIPE_KEYWORDS:
            if keyword in lower_name:
                return recipe
        return self.DEFAULT_RECIPE

    def _standardize_columns(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Gate 1 & Gate 2: Standarisasi header kolom + penghapusan atribut PII."""
        df = df.copy()
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        # Deteksi & buang kolom PII demi kepatuhan Audit Privasi
        dropped_pii = [
            col for col in df.columns
            if any(pii in col for pii in self.PII_KEYWORDS)
        ]
        if dropped_pii:
            df = df.drop(columns=dropped_pii)

        # Pemetaan nama kolom ke skema standar
        rename_map = {}
        for canonical_name, aliases in self.COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in df.columns and canonical_name not in rename_map.values():
                    rename_map[alias] = canonical_name
                    break
        df = df.rename(columns=rename_map)

        required_cols = ["tanggal", "nama_produk", "qty"]
        missing_required = [c for c in required_cols if c not in df.columns]
        if missing_required:
            raise DataQualityError(
                f"Skema CSV ditolak! Kolom wajib tidak ditemukan: {missing_required}. "
                f"Kolom tersedia: {list(df.columns)}"
            )

        return df, dropped_pii

    def clean_and_validate(self, df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Gate 3: Pembersihan baris rusak, penghapusan duplikat, dan penghitungan skor kualitas.
        Mengembalikan: (df_clean, quality_report)
        """
        initial_rows = len(df_raw)
        if initial_rows == 0:
            raise DataQualityError("Berkas CSV kosong (0 baris transaksi).")

        df, dropped_pii = self._standardize_columns(df_raw)

        # Bersihkan teks produk & ubah token korup menjadi NaN
        df["nama_produk"] = df["nama_produk"].astype(str).str.strip()
        df.loc[df["nama_produk"].str.lower().isin(self.CORRUPT_TOKENS), "nama_produk"] = np.nan

        # Parsing tanggal
        df["tanggal"] = pd.to_datetime(df["tanggal"], errors="coerce")

        # Parsing kuantitas & nominal harga
        df["qty"] = pd.to_numeric(df["qty"], errors="coerce")
        if "harga_satuan" in df.columns:
            df["harga_satuan"] = df["harga_satuan"].apply(self._clean_currency)
        else:
            df["harga_satuan"] = 18000.0

        if "total_transaksi" in df.columns:
            df["total_transaksi"] = df["total_transaksi"].apply(self._clean_currency)
        else:
            df["total_transaksi"] = df["qty"] * df["harga_satuan"]

        if "metode_bayar" not in df.columns:
            df["metode_bayar"] = "Tidak Tercatat"
        else:
            df["metode_bayar"] = df["metode_bayar"].fillna("Tidak Tercatat").astype(str).str.strip()

        # Buang duplikasi nomor struk jika kolom transaction_id tersedia
        duplicate_count = 0
        if "transaction_id" in df.columns:
            duplicate_count = int(df.duplicated(subset=["transaction_id"]).sum())
            df = df.drop_duplicates(subset=["transaction_id"], keep="first")

        # Saring baris cacat (tanggal invalid, produk kosong, qty <= 0, harga negatif)
        invalid_mask = (
            df["tanggal"].isna()
            | df["nama_produk"].isna()
            | df["qty"].isna()
            | (df["qty"] <= 0)
            | (df["harga_satuan"].fillna(0) < 0)
        )
        invalid_rows_dropped = int(invalid_mask.sum())
        df = df[~invalid_mask].copy()

        # Rekalkulasi total_transaksi jika kosong/nol
        recalc_mask = df["total_transaksi"].isna() | (df["total_transaksi"] <= 0)
        df.loc[recalc_mask, "total_transaksi"] = df.loc[recalc_mask, "qty"] * df.loc[recalc_mask, "harga_satuan"]

        df["qty"] = df["qty"].astype(int)
        df["harga_satuan"] = df["harga_satuan"].astype(int)
        df["total_transaksi"] = df["total_transaksi"].astype(int)
        df["tanggal_str"] = df["tanggal"].dt.strftime("%Y-%m-%d")

        # Konversi pemakaian bahan baku per baris transaksi
        kopi_list, susu_list, sirup_list = [], [], []
        for _, row in df.iterrows():
            recipe = self._match_recipe(row["nama_produk"])
            qty = row["qty"]
            kopi_list.append(round(qty * recipe["kopi_gr"], 2))
            susu_list.append(round(qty * recipe["susu_ml"], 2))
            sirup_list.append(round(qty * recipe["sirup_ml"], 2))

        df["pakai_kopi_gr"] = kopi_list
        df["pakai_susu_ml"] = susu_list
        df["pakai_sirup_ml"] = sirup_list

        final_rows = len(df)
        quality_score = round((final_rows / initial_rows) * 100, 2)

        report = {
            "status": "PASSED" if quality_score >= self.min_quality_score else "FAILED",
            "initial_rows": initial_rows,
            "final_rows": final_rows,
            "duplicate_rows_removed": duplicate_count,
            "invalid_rows_removed": invalid_rows_dropped,
            "pii_columns_stripped": dropped_pii,
            "quality_score_pct": quality_score,
            "date_range": f"{df['tanggal_str'].min()} s/d {df['tanggal_str'].max()}" if final_rows > 0 else "-",
            "total_revenue_idr": int(df["total_transaksi"].sum()) if final_rows > 0 else 0,
        }

        if quality_score < self.min_quality_score:
            raise DataQualityError(
                f"Quality Gate GAGAL! Skor kualitas data {quality_score}% berada di bawah "
                f"batas minimum {self.min_quality_score}%."
            )

        return df, report

    def build_daily_ml_features(self, df_clean: pd.DataFrame) -> pd.DataFrame:
        """
        Gate 4: Agregasi transaksi ke tingkat harian + Feature Engineering deret waktu
        untuk model prediksi kebutuhan stok 7-14 hari (@aril pop).
        """
        daily = (
            df_clean.groupby("tanggal", as_index=False)
            .agg(
                jumlah_transaksi=("qty", "count"),
                total_cup_terjual=("qty", "sum"),
                total_omset_idr=("total_transaksi", "sum"),
                kopi_gr=("pakai_kopi_gr", "sum"),
                susu_ml=("pakai_susu_ml", "sum"),
                sirup_ml=("pakai_sirup_ml", "sum"),
            )
            .sort_values("tanggal")
            .reset_index(drop=True)
        )

        # Konversi ke satuan operasional gudang Yaboo Kopi
        daily["kopi_kg"] = (daily["kopi_gr"] / 1000.0).round(3)
        daily["susu_liter"] = (daily["susu_ml"] / 1000.0).round(3)
        daily["sirup_liter"] = (daily["sirup_ml"] / 1000.0).round(3)

        # Fitur kalender & historis deret waktu (mencegah data leakage dengan shift(1))
        daily["hari_ke"] = daily["tanggal"].dt.day_of_week  # 0=Senin .. 6=Minggu
        daily["is_weekend"] = (daily["hari_ke"] >= 4).astype(int)  # Jumat, Sabtu, Minggu

        for col in ["kopi_kg", "susu_liter", "sirup_liter"]:
            daily[f"{col}_lag1"] = daily[col].shift(1).bfill()
            daily[f"{col}_rolling7"] = daily[col].rolling(window=7, min_periods=1).mean().round(3)

        daily["tanggal"] = daily["tanggal"].dt.strftime("%Y-%m-%d")
        return daily


if __name__ == "__main__":
    service_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.abspath(os.path.join(service_dir, "..", ".."))

    candidate_files = [
        os.path.join(backend_dir, "notebooks", "synthetic_pos_yaboo_1200.csv"),
        os.path.join(backend_dir, "notebooks", "synthetic_pos_yaboo_300.csv"),
        os.path.join(backend_dir, "data", "processed", "01_yaboo_transaksi_bersih.csv"),
    ]
    input_path = next((p for p in candidate_files if os.path.exists(p)), None)

    if not input_path:
        raise FileNotFoundError("Dataset sintetis belum ditemukan di backend/notebooks/.")

    print(f"Membaca berkas input: {input_path}")
    raw_df = pd.read_csv(input_path)

    preprocessor = YabooPOSPreprocessor(min_quality_score=85.0)
    clean_df, quality_report = preprocessor.clean_and_validate(raw_df)
    daily_ml_df = preprocessor.build_daily_ml_features(clean_df)

    output_ml_path = os.path.join(backend_dir, "data", "processed", "05_yaboo_stok_harian_ml_ready.csv")
    daily_ml_df.to_csv(output_ml_path, index=False)

    print("\n=== LAPORAN DATA QUALITY GATE & AUDIT PRIVASI ===")
    for k, v in quality_report.items():
        print(f"- {k:<24}: {v}")

    print(f"\nDataset harian siap latih ML disimpan ke: {output_ml_path}")
    print(f"Total hari operasional: {len(daily_ml_df)} hari | Jumlah fitur: {len(daily_ml_df.columns)} kolom")
    print(daily_ml_df[["tanggal", "total_cup_terjual", "kopi_kg", "susu_liter", "sirup_liter", "is_weekend"]].head())