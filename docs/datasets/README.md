# Dokumentasi Teknis Dataset PasarPulse

Dokumentasi ini menjelaskan fungsi, grain, schema, transformasi, aturan join, risiko leakage, dan keterbatasan setiap dataset yang digunakan oleh pilot PasarPulse.

## Peta aliran data

```text
World Bank RTFP ──> raw ──> market-long ──> province price panel ──┐
                                                                  ├─> master modeling table
NASA POWER ───────> raw monthly province weather ─────────────────┤
                                                                  │
Market coordinates ──> province centroids ──> k-NN graph ─────────┘
```

## Dokumen

| Dokumen | Isi |
|---|---|
| [`WORLD_BANK_RTFP.md`](WORLD_BANK_RTFP.md) | Harga pasar, quality fields, commodity mapping, dan caveat estimasi |
| [`NASA_POWER.md`](NASA_POWER.md) | Variabel agroklimat, sampling titik, satuan, missing values, dan join |
| [`SPATIAL_GRAPH.md`](SPATIAL_GRAPH.md) | Konstruksi graph provinsi, edge, distance weighting, dan batas interpretasi |
| [`DERIVED_TABLES.md`](DERIVED_TABLES.md) | Market-long, centroid, price panel, dan master modeling table |
| [`MODEL_OUTPUT_DATA.md`](MODEL_OUTPUT_DATA.md) | Prediksi, metrik, model files, figures, dan quality report |

## Struktur repository

```text
data/raw/          snapshot sumber
 data/interim/     hasil normalisasi dan reshape
 data/processed/   dataset siap analisis/training
models/            fitted pipelines
reports/           hasil evaluasi dan visualisasi
artifacts/         compressed bundle
```

## Data contract global

Primary key modeling:

```text
adm1_name × commodity × date
```

Aturan penting:

1. `date` selalu dinormalisasi menjadi awal bulan.
2. `adm1_name` dinormalisasi ke huruf kapital.
3. Harga dan target bersifat komoditas-spesifik.
4. Cuaca bersifat provinsi-spesifik dan direplikasi saat join untuk dua komoditas.
5. Semua lag dan rolling feature hanya memakai informasi sebelum target month.
6. Split evaluasi bersifat out-of-time, bukan random split.

## Status data

Dataset ini merupakan **research snapshot**, bukan data harga resmi pemerintah Indonesia dan bukan ground truth murni hasil observasi. World Bank RTFP memadukan observasi dengan estimasi model untuk mengisi gap. NASA POWER adalah data reanalysis/satellite-derived pada koordinat centroid pasar, bukan sensor kebun komoditas.