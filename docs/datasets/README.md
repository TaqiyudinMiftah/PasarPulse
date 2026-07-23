# Dokumentasi Teknis Dataset PasarPulse

Dokumentasi ini menjelaskan fungsi, grain, schema, transformasi, aturan join, risiko leakage, dan keterbatasan setiap dataset yang digunakan oleh PasarPulse.

## Peta aliran data

```text
World Bank RTFP ──> raw ──> market-long ──> province price panel ─────┐
                                                                      │
NASA POWER ───────> raw monthly province weather ─────────────────────┤
                                                                      ├─> multimodal model
Market coordinates ──> province centroids ──> k-NN graph ─────────────┤
                                                                      │
Sentinel-2 L2A ──> quarterly four-band image chips + valid masks ─────┘
```

## Dokumen

| Dokumen | Isi |
|---|---|
| [`WORLD_BANK_RTFP.md`](WORLD_BANK_RTFP.md) | Harga pasar, quality fields, commodity mapping, dan caveat estimasi |
| [`NASA_POWER.md`](NASA_POWER.md) | Variabel agroklimat, sampling titik, satuan, missing values, dan join |
| [`SPATIAL_GRAPH.md`](SPATIAL_GRAPH.md) | Konstruksi graph provinsi, edge, distance weighting, dan batas interpretasi |
| [`SENTINEL2_IMAGERY.md`](SENTINEL2_IMAGERY.md) | Tensor citra empat band, sampling kuartalan, cloud mask, shard NPZ, dan as-of join |
| [`DERIVED_TABLES.md`](DERIVED_TABLES.md) | Market-long, centroid, price panel, dan master modeling table |
| [`MODEL_OUTPUT_DATA.md`](MODEL_OUTPUT_DATA.md) | Prediksi, metrik, model files, figures, dan quality report |

## Struktur repository

```text
data/raw/          snapshot sumber tabular
data/interim/      hasil normalisasi dan reshape
data/processed/    dataset tabular siap analisis/training
data/satellite/    tensor citra, mask, metadata, dan manifest
models/            fitted pipelines
reports/           hasil evaluasi dan visualisasi
artifacts/         compressed bundles
```

## Data contract

Primary key tabular:

```text
adm1_name × commodity × date
```

Primary key citra:

```text
sample_id = province × year × quarter
```

Citra digabungkan ke data bulanan menggunakan backward as-of join berdasarkan provinsi dan acquisition time. Model tidak boleh menggunakan citra yang belum tersedia ketika prediction cutoff berlangsung.

Aturan penting:

1. `date` harga dan cuaca dinormalisasi menjadi awal bulan.
2. `adm1_name` dinormalisasi ke huruf kapital.
3. Harga dan target bersifat komoditas-spesifik.
4. Cuaca dan citra bersifat provinsi-spesifik dan dapat digunakan oleh lebih dari satu komoditas.
5. Semua lag dan rolling feature hanya memakai informasi sebelum target month.
6. Citra harus menggunakan `acquisition_datetime <= prediction_cutoff`.
7. Split evaluasi bersifat out-of-time, bukan random split.

## Definisi multimodal setelah penambahan Sentinel-2

PasarPulse sekarang memiliki tipe input yang berbeda secara native:

```text
price sequence              -> temporal/tabular encoder
weather covariates          -> tabular encoder
Sentinel-2 raster tensor    -> CNN atau Vision Transformer
province relation graph     -> GNN pada tahap pengembangan berikutnya
```

Citra tidak diringkas hanya menjadi NDVI untuk klaim multimodal. Shard menyimpan tensor piksel empat band agar encoder visi dapat dilatih langsung.

## Status data

Dataset ini merupakan **research snapshot**, bukan data harga resmi pemerintah Indonesia dan bukan ground truth murni hasil observasi. World Bank RTFP memadukan observasi dengan estimasi model untuk mengisi gap. NASA POWER adalah data reanalysis/satellite-derived pada koordinat centroid pasar. Sentinel-2 merupakan surface reflectance nyata, tetapi patch berpusat pada centroid pasar dan belum merupakan observasi lahan cabai atau bawang yang terverifikasi.
