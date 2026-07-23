# Data Directory

Folder `data/` hanya berisi dataset. Model, metrik, prediksi, visualisasi, dan arsip dipisahkan agar provenance dan penggunaan setiap artefak jelas.

## Struktur

```text
data/
├── raw/          Snapshot sumber yang diunduh tanpa feature engineering
├── interim/      Data hasil normalisasi/reshape yang belum siap untuk training final
└── processed/    Dataset turunan yang siap dianalisis atau dipakai modeling
```

## `data/raw/`

| File | Sumber | Grain |
|---|---|---|
| `world_bank_rtfp_indonesia_selected.csv` | World Bank Real-Time Food Prices | market × month |
| `nasa_power_monthly_province.csv` | NASA POWER Monthly Point API | province centroid × month |

Raw berarti belum melalui feature engineering PasarPulse. File ini tetap merupakan subset atau hasil query dari sumber upstream, bukan salinan penuh seluruh database sumber.

## `data/interim/`

| File | Fungsi | Grain |
|---|---|---|
| `rtfp_market_long.csv` | Mengubah kolom harga komoditas menjadi format long | market × commodity × month |
| `province_market_centroids.csv` | Koordinat median pasar per provinsi | province |

## `data/processed/`

| File | Fungsi | Grain |
|---|---|---|
| `province_commodity_price_panel.csv` | Harga median provinsi dan metadata kualitas | province × commodity × month |
| `province_knn_graph.csv` | Tiga tetangga spasial terdekat setiap provinsi | directed province edge |
| `master_modeling_table.csv` | Harga, cuaca, lag, rolling features, spatial features, dan target | province × commodity × month |

## Kunci bersama

Semua modalitas training disejajarkan pada:

```text
adm1_name × commodity × date
```

- `adm1_name`: nama provinsi yang dinormalisasi menjadi huruf kapital.
- `commodity`: `CHILI_RED` atau `SHALLOT`.
- `date`: hari pertama bulan yang merepresentasikan periode bulanan.

Cuaca tidak memiliki dimensi komoditas. Nilainya digabungkan ke setiap komoditas melalui `adm1_name × date`.

## Artefak non-dataset

```text
models/             fitted `.joblib`
reports/            metrics, predictions, figures, quality report, run log
artifacts/          ZIP bundle lengkap
```

Dokumentasi teknis per dataset tersedia pada [`docs/datasets/`](../docs/datasets/README.md).

## Rebuild

```bash
python -m pip install -r requirements.txt
python src/run_pipeline.py
```

GitHub Actions kemudian menata hasil pipeline ke struktur di atas secara otomatis.