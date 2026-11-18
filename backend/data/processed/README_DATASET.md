# Kamus Data (Data Dictionary) - Tim Capstone A26-CS216 Yaboo Kopi

## 1. `01_yaboo_transaksi_bersih.csv`
- `transaction_id`: ID unik transaksi kasir POS.
- `tanggal`: Tanggal transaksi (`YYYY-MM-DD`).
- `nama_produk`: Nama menu minuman terjual.
- `qty`: Jumlah cangkir terjual per transaksi.
- `harga_satuan` & `total_transaksi`: Nilai transaksi dalam Rupiah.
- `pakai_kopi_gr`, `pakai_susu_ml`, `pakai_sirup_ml`: Konversi pemakaian bahan baku per struk.

## 2. `02_yaboo_stok_harian_latih.csv` (Input Utama Model ML DS 2 & Grafik DS 3)
- `tanggal`: Deret waktu harian berurutan tanpa celah hari.
- `total_cup_terjual` & `total_omset_harian`: Agregasi penjualan harian untuk dasbor mobile.
- `kopi_arabika_kg`: Target prediksi kebutuhan Kopi Arabika (Kg).
- `susu_uht_karton`: Target prediksi kebutuhan Susu UHT (Karton isi 12 Liter).
- `sirup_palm_sugar_botol`: Target prediksi kebutuhan Sirup Palm Sugar (Botol 1 Liter).
- `hari_ke` (0=Senin..6=Minggu) & `is_weekend` (1=Jumat-Minggu): Fitur kalender.
- `*_lag1` & `*_rolling7`: Fitur historis 1 hari sebelumnya dan rata-rata bergerak 7 hari.

## 3. `03_sqa_cafe_sales_bersih.csv`
- Dataset hasil pembersihan nilai anomali (`ERROR`, `UNKNOWN`, `NaN`) untuk bukti pengujian kualitas data (SQA).

## 4. `04_audit_retail_tanpa_pii.csv`
- Dataset hasil sanitasi atribut pribadi pelanggan (`Customer_Name` dihapus) untuk bukti Matriks Audit Anonimisasi PII.
