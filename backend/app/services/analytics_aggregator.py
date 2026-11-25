import os
from typing import Dict, Any, List
import pandas as pd


class YabooAnalyticsAggregator:
    """
    Modul Agregasi Analitik & Chart UI Data Asli Yaboo Kopi
    PIC: Data Science 3 (@elen) - Capstone Team A26-CS216
    """

    def __init__(self, processed_dir: str = None):
        if processed_dir is None:
            service_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.abspath(os.path.join(service_dir, "..", ".."))
            processed_dir = os.path.join(backend_dir, "data", "processed")

        self.trx_path = os.path.join(processed_dir, "01_yaboo_real_transaksi_clean.csv")
        self.daily_path = os.path.join(processed_dir, "05_yaboo_stok_harian_ml_ready.csv")

        self.df_trx = pd.read_csv(self.trx_path)
        self.df_daily = pd.read_csv(self.daily_path)

    @staticmethod
    def _pick_col(df: pd.DataFrame, candidates: List[str]) -> str:
        """Mencari nama kolom yang cocok secara otomatis dari daftar kandidat."""
        for col in candidates:
            if col in df.columns:
                return col
        raise KeyError(f"Tidak menemukan kolom dari kandidat {candidates}. Kolom tersedia: {list(df.columns)}")

    def get_top_menus(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Agregasi menu terlaris berdasarkan total cup terjual & omset dari 01_yaboo_real_transaksi_clean.csv."""
        prod_col = self._pick_col(self.df_trx, ["nama_produk", "menu", "produk", "item"])
        qty_col = self._pick_col(self.df_trx, ["qty", "jumlah", "quantity", "terjual"])
        rev_col = self._pick_col(self.df_trx, ["total_transaksi", "total_harga", "total", "omset"])

        grouped = (
            self.df_trx.groupby(prod_col, as_index=False)
            .agg(
                total_cup=(qty_col, "sum"),
                jumlah_transaksi=(qty_col, "count"),
                total_omset_idr=(rev_col, "sum"),
            )
            .sort_values(by=["total_cup", "total_omset_idr"], ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )

        total_all_cups = self.df_trx[qty_col].sum()
        grouped["kontribusi_cup_pct"] = ((grouped["total_cup"] / total_all_cups) * 100).round(2)
        grouped = grouped.rename(columns={prod_col: "nama_produk"})
        return grouped.to_dict(orient="records")

    def get_payment_methods(self) -> List[Dict[str, Any]]:
        """Agregasi distribusi metode pembayaran (Tunai, QRIS, dll.) dari 01_yaboo_real_transaksi_clean.csv."""
        pay_col = self._pick_col(self.df_trx, ["metode_bayar", "payment_method", "pembayaran", "metode"])
        rev_col = self._pick_col(self.df_trx, ["total_transaksi", "total_harga", "total", "omset"])

        grouped = (
            self.df_trx.groupby(pay_col, as_index=False)
            .agg(
                jumlah_transaksi=(rev_col, "count"),
                total_nominal_idr=(rev_col, "sum"),
            )
            .sort_values(by="jumlah_transaksi", ascending=False)
            .reset_index(drop=True)
        )

        total_trx = len(self.df_trx)
        grouped["persentase_trx"] = ((grouped["jumlah_transaksi"] / total_trx) * 100).round(2)
        grouped = grouped.rename(columns={pay_col: "metode_bayar"})
        return grouped.to_dict(orient="records")

    def get_daily_revenue_profit_trend(self) -> Dict[str, Any]:
        """Agregasi tren omset & laba bersih harian untuk grafik Flutter dari 05_yaboo_stok_harian_ml_ready.csv."""
        df = self.df_daily.copy()
        date_col = self._pick_col(df, ["tanggal", "date", "tgl"])
        rev_col = self._pick_col(df, ["total_omset_idr", "total_omset", "omset", "revenue"])
        profit_col = self._pick_col(df, ["laba_bersih_idr", "laba_bersih", "net_profit", "laba", "profit"])
        cup_col = self._pick_col(df, ["total_cup_terjual", "total_cup", "qty"])

        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col).reset_index(drop=True)

        summary = {
            "total_hari": int(len(df)),
            "periode": f"{df[date_col].min().strftime('%Y-%m-%d')} s/d {df[date_col].max().strftime('%Y-%m-%d')}",
            "total_omset_idr": int(df[rev_col].sum()),
            "total_laba_bersih_idr": int(df[profit_col].sum()),
            "rata_rata_omset_harian_idr": round(float(df[rev_col].mean()), 2),
            "rata_rata_laba_harian_idr": round(float(df[profit_col].mean()), 2),
            "total_cup_terjual": int(df[cup_col].sum()),
        }

        series = []
        for _, row in df.iterrows():
            series.append({
                "tanggal": row[date_col].strftime("%Y-%m-%d"),
                "total_cup": int(row[cup_col]),
                "omset_idr": int(row[rev_col]),
                "laba_bersih_idr": int(row[profit_col]),
            })

        return {"summary": summary, "daily_series": series}


if __name__ == "__main__":
    agg = YabooAnalyticsAggregator()

    print("=== 1. RINGKASAN OMSET & LABA BERSIH HARIAN (139 HARI) ===")
    trend_data = agg.get_daily_revenue_profit_trend()
    for k, v in trend_data["summary"].items():
        print(f"- {k:<28}: {v}")

    print("\n=== 2. TOP 5 MENU TERLARIS YABOO KOPI ===")
    for idx, item in enumerate(agg.get_top_menus(top_n=5), start=1):
        print(f"{idx}. {item['nama_produk']} -> {item['total_cup']} cup ({item['kontribusi_cup_pct']}%) | Rp {item['total_omset_idr']:,}")

    print("\n=== 3. DISTRIBUSI METODE PEMBAYARAN ===")
    for item in agg.get_payment_methods():
        print(f"- {item['metode_bayar']}: {item['jumlah_transaksi']} trx ({item['persentase_trx']}%) | Rp {item['total_nominal_idr']:,}")