import os
import pandas as pd


def build_advanced_timeseries_dataset(input_daily_csv: str, output_train_csv: str) -> pd.DataFrame:
    df = pd.read_csv(input_daily_csv)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    df = df.sort_values("tanggal").reset_index(drop=True)

    # 1. Fitur Kalender & Siklus Gajian
    df["hari_ke"] = df["tanggal"].dt.day_of_week
    df["is_weekend"] = (df["hari_ke"] >= 4).astype(int)
    df["tanggal_bulan"] = df["tanggal"].dt.day
    df["is_payday"] = ((df["tanggal_bulan"] >= 25) | (df["tanggal_bulan"] <= 5)).astype(int)

    # 2. Konversi Kemasan Gudang Yaboo Kopi (1 Karton Susu = 12 Liter, 1 Botol Sirup = 1 Liter)
    df["susu_karton"] = (df["susu_liter"] / 12.0).round(3)
    df["sirup_botol"] = (df["sirup_liter"] / 1.0).round(3)

    materials = ["kopi_kg", "susu_liter", "krimer_kg", "powder_aren_kg", "sirup_liter"]

    # 3. Fitur Lag & Rolling Window (Strictly Shifted / Bebas Data Leakage)
    for col in materials:
        shifted = df[col].shift(1)
        df[f"{col}_lag1"] = shifted.bfill().round(3)
        df[f"{col}_lag2"] = df[col].shift(2).bfill().round(3)
        df[f"{col}_lag3"] = df[col].shift(3).bfill().round(3)
        df[f"{col}_lag7"] = df[col].shift(7).bfill().round(3)

        df[f"{col}_roll7_mean"] = shifted.rolling(window=7, min_periods=1).mean().bfill().round(3)
        df[f"{col}_roll7_std"] = shifted.rolling(window=7, min_periods=2).std().fillna(0.0).round(3)
        df[f"{col}_roll14_mean"] = shifted.rolling(window=14, min_periods=1).mean().bfill().round(3)

    # 4. Target Prediksi Kebutuhan 7 Hari ke Depan (t+1 s/d t+7)
    for col in materials:
        df[f"target_{col}_7d"] = sum(df[col].shift(-step) for step in range(1, 8)).round(3)

    df_ml = df.dropna(subset=[f"target_{col}_7d" for col in materials]).copy()
    df_ml["tanggal"] = df_ml["tanggal"].dt.strftime("%Y-%m-%d")
    df_ml.to_csv(output_train_csv, index=False)
    return df_ml


if __name__ == "__main__":
    nb_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.abspath(os.path.join(nb_dir, ".."))

    input_path = os.path.join(backend_dir, "data", "processed", "05_yaboo_stok_harian_ml_ready.csv")
    output_path = os.path.join(backend_dir, "data", "processed", "02_yaboo_stok_harian_latih.csv")

    df_result = build_advanced_timeseries_dataset(input_path, output_path)
    print("=== KALIBRASI FEATURE ENGINEERING DATA ASLI YABOO KOPI SELESAI ===")
    print(f"Dimensi Tabel Latih : {df_result.shape[0]} hari x {df_result.shape[1]} kolom | Total Null: {df_result.isna().sum().sum()}")