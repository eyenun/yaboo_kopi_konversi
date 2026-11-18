import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


def generate_yaboo_pos_dataset(total_days: int = 135, seed: int = 42) -> pd.DataFrame:
    """
    Generator dataset sintetis transaksi POS UMKM Yaboo Kopi.
    Memuat tanggal, jam operasional, varian menu kopi/non-kopi, qty, harga,
    serta konversi Bill of Materials (gram kopi, ml susu UHT, ml gula aren).
    """
    np.random.seed(seed)
    random.seed(seed)

    start_date = datetime(2026, 7, 1)

    menu_catalog = [
        {"menu": "Es Kopi Susu Yaboo", "harga": 18000, "kopi_gr": 18, "susu_ml": 120, "sirup_ml": 20, "weight": 0.35},
        {"menu": "Palm Sugar Latte", "harga": 22000, "kopi_gr": 18, "susu_ml": 130, "sirup_ml": 25, "weight": 0.25},
        {"menu": "Americano Arabika", "harga": 15000, "kopi_gr": 18, "susu_ml": 0, "sirup_ml": 0, "weight": 0.15},
        {"menu": "Caffe Latte", "harga": 20000, "kopi_gr": 18, "susu_ml": 150, "sirup_ml": 0, "weight": 0.15},
        {"menu": "Matcha / Chocolate Latte", "harga": 20000, "kopi_gr": 0, "susu_ml": 150, "sirup_ml": 15, "weight": 0.10},
    ]
    menu_weights = [item["weight"] for item in menu_catalog]
    payment_methods = ["QRIS", "Tunai", "Transfer"]
    sample_names = ["Rizky", "Aulia", "Fajar", "Nadia", "Bima", "Siti", "Dimas", None, None]

    # Jam sibuk kedai kopi (pagi 08-10 dan sore-malam 16-21 lebih sering muncul)
    operating_hours = list(range(8, 23))
    hour_weights = [0.06, 0.07, 0.05, 0.04, 0.05, 0.06, 0.05, 0.06, 0.09, 0.10, 0.10, 0.10, 0.09, 0.05, 0.03]

    records = []
    trx_counter = 10001

    for day_offset in range(total_days):
        current_date = start_date + timedelta(days=day_offset)
        is_weekend = current_date.weekday() >= 4
        daily_trx_count = random.randint(10, 14) if is_weekend else random.randint(6, 10)

        # Bangkitkan jam transaksi terurut dalam satu hari
        hours_today = sorted(random.choices(operating_hours, weights=hour_weights, k=daily_trx_count))

        for hour in hours_today:
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            jam_str = f"{hour:02d}:{minute:02d}:{second:02d}"

            item = random.choices(menu_catalog, weights=menu_weights, k=1)[0]
            qty = random.choices([1, 2, 3, 4], weights=[0.55, 0.28, 0.12, 0.05])[0]
            if is_weekend and random.random() < 0.3:
                qty += 1

            cust_name = random.choice(sample_names)
            cust_phone = f"0812{random.randint(10000000, 99999999)}" if cust_name else None

            records.append({
                "transaction_id": f"TRX-{trx_counter}",
                "tanggal": current_date.strftime("%Y-%m-%d"),
                "jam": jam_str,
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

    df_hasil = generate_yaboo_pos_dataset(total_days=135)
    df_hasil.to_csv(output_csv, index=False)

    print("=== GENERATOR DATASET SINTETIS YABOO KOPI (+ KOLOM JAM) SELESAI ===")
    print(f"Total Baris   : {len(df_hasil)} baris transaksi")
    print(df_hasil[["transaction_id", "tanggal", "jam", "nama_produk", "qty", "total_transaksi"]].head())