# Derived and Modeling Tables

Dokumen ini menjelaskan dataset turunan yang dibentuk oleh pipeline PasarPulse.

## 1. `data/interim/rtfp_market_long.csv`

### Grain

```text
market × commodity × month
```

### Tujuan

Mengubah struktur raw World Bank yang memiliki kolom terpisah untuk chili dan onions menjadi format long yang konsisten.

### Primary key konseptual

```text
date × geo_id × commodity
```

### Kolom

| Kolom | Penjelasan |
|---|---|
| `date` | awal bulan |
| `adm1_name` | provinsi uppercase |
| `mkt_name`, `geo_id` | identitas pasar |
| `lat`, `lon` | koordinat pasar |
| `commodity` | `CHILI_RED` atau `SHALLOT` |
| `price` | harga komoditas |
| `trust` | quality/trust field komoditas |
| `data_coverage` | coverage historis |
| `data_coverage_recent` | coverage terbaru |
| `index_confidence_score` | confidence source |
| `spatially_interpolated` | indikator/proxy interpolasi spasial |

Dataset ini belum siap training karena masih memiliki beberapa pasar pada provinsi dan bulan yang sama.

---

## 2. `data/interim/province_market_centroids.csv`

### Grain

```text
province
```

### Kolom

| Kolom | Penjelasan |
|---|---|
| `adm1_name` | nama provinsi |
| `lat` | median latitude seluruh pasar provinsi |
| `lon` | median longitude seluruh pasar provinsi |
| `market_locations` | jumlah `geo_id` unik |

### Digunakan untuk

- query titik NASA POWER;
- membangun graph k-nearest province;
- audit coverage spasial.

Centroid ini bukan centroid administratif.

---

## 3. `data/processed/province_commodity_price_panel.csv`

### Grain dan primary key

```text
adm1_name × commodity × date
```

Satu row merepresentasikan satu provinsi, satu komoditas, dan satu bulan.

### Kolom utama

| Kolom | Penjelasan |
|---|---|
| `date` | awal bulan |
| `adm1_name` | provinsi |
| `commodity` | komoditas |
| `price` | median harga seluruh pasar yang valid |
| `trust` | median trust |
| `market_count` | jumlah pasar unik |
| `lat`, `lon` | median koordinat pasar pada group |
| `data_coverage` | median coverage |
| `data_coverage_recent` | median recent coverage |
| `index_confidence_score` | median confidence |
| `spatially_interpolated` | mean indikator interpolasi |
| `neighbor_price` | weighted mean harga tiga provinsi terdekat, komoditas dan bulan yang sama |
| `neighbor_price_ratio` | `neighbor_price / price` |

Catatan: source pipeline menambahkan spatial features sebelum membentuk master. Snapshot price panel yang dihasilkan pipeline dapat merepresentasikan panel sebelum atau sesudah spatial enrichment bergantung versi. Untuk training, referensi final selalu `master_modeling_table.csv`.

---

## 4. `data/processed/master_modeling_table.csv`

### Tujuan

Dataset tunggal yang telah menyelaraskan harga, quality metadata, cuaca, temporal features, spatial features, dan target.

### Grain

```text
province × commodity × month
```

### Kelompok kolom

#### A. Identifier

| Kolom | Penjelasan |
|---|---|
| `date` | feature month |
| `target_date` | bulan berikutnya |
| `adm1_name` | provinsi |
| `commodity` | komoditas |

#### B. Current price and quality

```text
price
trust
market_count
data_coverage
data_coverage_recent
index_confidence_score
spatially_interpolated
lat
lon
```

#### C. Price history

```text
price_lag_1
price_lag_2
price_lag_3
price_lag_6
price_lag_12
price_roll_mean_3
price_roll_mean_6
price_roll_mean_12
price_roll_std_3
price_roll_std_6
price_roll_std_12
price_return_1
```

Rolling features memakai `shift(1)` sebelum rolling calculation. Dengan demikian, rolling statistic untuk row bulan `t` tidak memasukkan `price_t`.

#### D. Spatial features

```text
neighbor_price
neighbor_price_ratio
neighbor_gap
```

`neighbor_gap = neighbor_price / price - 1`.

#### E. Raw weather

```text
T2M
T2M_MAX
T2M_MIN
PRECTOTCORR
RH2M
WS2M
ALLSKY_SFC_SW_DWN
weather_lat
weather_lon
```

#### F. Weather temporal features

Untuk setiap parameter cuaca `X`:

```text
X_lag_1
X_anom_12
```

`X_anom_12` adalah nilai bulan berjalan dikurangi rolling mean 12 bulan sebelumnya.

Tambahan:

```text
weather_missing_count
```

#### G. Calendar features

```text
month_sin
month_cos
year
```

Sine/cosine merepresentasikan seasonality siklik bulanan.

#### H. Targets

| Kolom | Definisi |
|---|---|
| `target_price` | harga provinsi-komoditas pada bulan berikutnya |
| `target_spike_10pct` | 1 bila `target_price / price - 1 >= 0.10`, selain itu 0 |

Row terakhir suatu series tidak memiliki target dan tidak digunakan untuk supervised evaluation.

## Aturan temporal dan leakage

1. `target_price` dibentuk dengan `shift(-1)` hanya setelah seluruh feature historis dibuat.
2. Price rolling features memakai `shift(1)`.
3. Weather anomalies menggunakan rolling mean yang juga di-shift satu bulan.
4. Evaluation split berdasarkan waktu.
5. Current-month price dan current-month weather diasumsikan telah tersedia pada inference month-end. Untuk deployment lebih awal dalam bulan, availability timestamp perlu ditambahkan.

## Missing values

Model pipeline menggunakan:

```text
SimpleImputer(strategy="median", add_indicator=True)
```

untuk numeric features dan `OneHotEncoder(handle_unknown="ignore")` untuk categorical features.

Missingness tidak dihapus secara massal agar quality gaps tetap dapat dipelajari melalui missing indicators.

## Integritas dataset

Pemeriksaan yang disarankan:

```text
no duplicate(adm1_name, commodity, date)
target_date == date + 1 month
price > 0
target_price > 0 when present
target_spike_10pct in {0,1,NA}
lag columns do not use future observations
```

## Dataset untuk training

Gunakan `master_modeling_table.csv` sebagai sumber tunggal modeling. Dataset raw dan interim digunakan untuk audit, reproducibility, dan alternative feature engineering—not direct training tanpa preprocessing.