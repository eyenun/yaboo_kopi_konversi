import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


def generate_yaboo_pos_dataset(num_rows: int = 1200, seed: int = 42) -> pd.DataFrame:
    """
    Generator dataset sintetis transaksi POS Santai Scale untuk UMKM Yaboo Kopi.
    Menghasilkan 1.200+ baris transaksi realistis (pola lonjakan akhir pekan,
    konversi resep bahan baku utama, serta simulasi kolom PII untuk pengujian audit).
    """
    np.random.seed(seed)
    random.seed(seed)

    start_date = datetime(2026, 7, 1)
    total_days = 135  # ~4.5 bulan data historis hingga pertengahan November 2026

    menu_catalog = [
        {"menu": "Es Kopi Susu Yaboo", "harga": 18000, "kopi_gr": 18, "susu_ml": 120, "sirup_ml": 20, "weight": 0.35},
        {"menu": "Palm Sugar Latte", "harga": 22000, "kopi_gr": 18, "susu_ml": 130, "sirup_ml": 25, "weight": 0.25},
        {"menu": "Americano Arabika", "harga": 15000, "kopi_gr": 18, "susu_ml": 0, "sirup_ml": 0, "weight": 0.15},
        {"menu": "Caffe Latte", "harga": 20000, "kopi_gr": 18, "susu_ml": 150, "sirup_ml": 0, "weight": 0.15},
        {"menu": "Matcha / Chocolate Latte", "harga": 20000, "kopi_gr": 0, "susu_ml": 150, "sirup_ml": 15, "weight": 0.10},
    ]
    menu_weights = [item["weight"] for item in menu_catalog]
    payment_methods = ["QRIS", "Tunai", "Transfer"]

    # Simulasi kolom PII pelanggan untuk pengujian sanitasi Audit Sistem Informasi
    sample_names = ["Rizky", "Aulia", "Fajar", "Nadia", "Bima", "Siti", "Dimas", None, None]

    records = []
    trx_counter = 10001

    for day_offset in range(total_days):
        current_date = start_date + timedelta(days=day_offset)
        is_weekend = current_date.weekday() >= 4  # Jumat, Sabtu, Minggu lebih ramai

        daily_trx_count = random.randint(10, 14) if is_weekend else random.randint(6, 10)

        for _ in range(daily_trx_count):
            item = random.choices(menu_catalog, weights=menu_weights, k=1)[0]
            qty = random.choices([1, 2, 3, 4], weights=[0.55, 0.28, 0.12, 0.05])[0]
            if is_weekend and random.random() < 0.3:
                qty += 1

            cust_name = random.choice(sample_names)
            cust_phone = f"0812{random.randint(10000000, 99999999)}" if cust_name else None

            records.append({
                "transaction_id": f"TRX-{trx_counter}",
                "tanggal": current_date.strftime("%Y-%m-%d"),
                "nama_pelanggan": cust_name,
                "no_hp_pelanggan": cust_phone,
                "nama_produk": item["menu"],
                "qty": qty,
                "harga_satuan": item["harga"],
                "total_transaksi": qty * item["harga"],
                "metode_bayar": random.choices(payment_methods, weights=[0.55, 0.35, 0.10])[0],
                "pakai_kopi_gr": qty * item["kopi_gr"],
                "pakai_susu_ml": qty * item["susu_ml"],
                "pakai_sirup_ml": qty * item["sirup_ml"],
            })
            trx_counter += 1

    return pd.DataFrame(records)


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_csv = os.path.join(base_dir, "synthetic_pos_yaboo_1200.csv")

    df_hasil = generate_yaboo_pos_dataset(num_rows=1200)
    df_hasil.to_csv(output_csv, index=False)

    print("=== GENERATOR DATASET SINTETIS YABOO KOPI SELESAI ===")
    print(f"Lokasi Berkas : {output_csv}")
    print(f"Total Baris   : {len(df_hasil)} baris transaksi (>= 1.000 baris terpenuhi)")
    print(f"Rentang Waktu : {df_hasil['tanggal'].min()} s/d {df_hasil['tanggal'].max()}")
    print("\nContoh 5 baris pertama:")
    print(df_hasil[["transaction_id", "tanggal", "nama_produk", "qty", "total_transaksi"]].head())