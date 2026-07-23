# NASA POWER Monthly Agroclimate Data

## File repository

```text
data/raw/nasa_power_monthly_province.csv
```

## Peran dalam PasarPulse

NASA POWER menjadi modalitas exogenous untuk merepresentasikan kondisi agroklimat bulanan di sekitar pusat aktivitas pasar suatu provinsi. Data ini dipakai untuk menguji apakah cuaca menambah sinyal di luar riwayat harga.

## Sumber dan endpoint

Sumber: NASA Prediction Of Worldwide Energy Resources (POWER), Monthly Point API, community `AG`.

Query pipeline dilakukan untuk setiap koordinat centroid pasar provinsi dengan parameter:

```text
community=AG
longitude=<median market longitude>
latitude=<median market latitude>
start=<first price year>
end=<last complete weather year>
format=JSON
```

## Grain

```text
province market centroid × month
```

Primary key:

```text
adm1_name × date
```

Cuaca tidak memiliki dimensi komoditas. Saat membangun master table, row cuaca digabungkan ke seluruh komoditas pada provinsi dan bulan yang sama.

## Lokasi sampling

`weather_lat` dan `weather_lon` berasal dari median koordinat pasar yang tersedia pada World Bank RTFP untuk setiap provinsi. Ini adalah **market-centroid proxy**, bukan centroid administratif dan bukan centroid lahan produksi komoditas.

Implikasi:

- cocok untuk pilot multimodal yang membutuhkan join konsisten;
- belum cukup untuk menyatakan cuaca yang dialami sentra produksi;
- provinsi luas atau kepulauan dapat terwakili secara kasar oleh satu titik.

## Variabel

| Kolom | Makna teknis | Unit umum NASA POWER* |
|---|---|---|
| `T2M` | suhu udara rata-rata pada 2 meter | °C |
| `T2M_MAX` | suhu maksimum pada 2 meter | °C |
| `T2M_MIN` | suhu minimum pada 2 meter | °C |
| `PRECTOTCORR` | presipitasi terkoreksi | mm/day untuk agregasi bulanan API |
| `RH2M` | relative humidity pada 2 meter | % |
| `WS2M` | wind speed pada 2 meter | m/s |
| `ALLSKY_SFC_SW_DWN` | downward shortwave radiation pada permukaan, all-sky | kWh/m²/day |
| `weather_lat`, `weather_lon` | koordinat query | decimal degrees |
| `adm1_name` | provinsi yang diwakili | string |
| `date` | awal bulan | datetime |

\* Unit harus tetap diverifikasi dari metadata response NASA POWER apabila parameter atau endpoint berubah. Pipeline mempertahankan angka sebagaimana dikembalikan API dan tidak melakukan konversi unit.

## Parsing temporal

NASA POWER monthly response dapat memuat key dengan pola `YYYYMM`. Beberapa response juga menyertakan `YYYY13` sebagai ringkasan tahunan. Pipeline hanya menerima bulan 1–12:

```text
len(key) == 6
key numeric
1 <= int(key[4:]) <= 12
```

Seluruh tanggal dinormalisasi ke hari pertama bulan.

## Missing values

Nilai numeric `<= -900` diperlakukan sebagai sentinel missing dan diubah menjadi `NaN`.

Pada master table dibuat:

- `weather_missing_count`: jumlah variabel cuaca raw yang kosong;
- median-imputation indicator melalui scikit-learn pipeline;
- lag 1 bulan untuk setiap parameter;
- anomali terhadap rolling mean 12 bulan sebelumnya.

## Feature engineering

Untuk setiap parameter `X`:

```text
X_lag_1      = X pada bulan t-1
X_anom_12    = X_t - mean(X_{t-12..t-1})
```

Rolling mean menggunakan `shift(1)`, sehingga tidak melihat target masa depan.

## Join ke harga

```text
price panel LEFT JOIN weather
ON adm1_name, date
```

Join bersifat left join agar price rows tetap tersedia ketika cuaca hilang. Karena price panel memiliki dua komoditas, satu row cuaca dapat muncul dua kali pada master table—sekali per komoditas.

## Risiko dan keterbatasan

1. Satu titik tidak mewakili seluruh provinsi.
2. Koordinat pasar belum tentu dekat sentra produksi.
3. Monthly aggregation dapat kehilangan shock harian atau mingguan.
4. NASA POWER adalah produk gridded/reanalysis/satellite-derived, bukan pengukuran stasiun lokal langsung.
5. Cuaca bulan berjalan dapat mengandung informasi yang belum tersedia pada awal bulan. Untuk deployment real-time yang ketat, gunakan hanya cuaca sampai tanggal inference atau weather forecast yang terpisah.
6. Efek cuaca terhadap harga dapat memiliki lag berbeda antar komoditas dan wilayah.

## Validasi minimum

```text
unique(adm1_name, date)
month in 1..12
plausible T2M range
RH2M between 0 and 100 when present
PRECTOTCORR non-negative when present
coordinates match province centroid table
```

## Peningkatan berikutnya

Untuk versi ilmiah yang lebih kuat:

- sampling pada cropland/sentra produksi, bukan market centroid;
- area-weighted aggregation dari beberapa grid;
- daily AgERA5/ERA5-Land features;
- rainfall extremes dan dry-spell features;
- explicit data-availability timestamp untuk mencegah operational leakage.