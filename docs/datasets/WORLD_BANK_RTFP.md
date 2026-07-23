# World Bank Real-Time Food Prices — Indonesia

## File repository

```text
data/raw/world_bank_rtfp_indonesia_selected.csv
data/interim/rtfp_market_long.csv
data/processed/province_commodity_price_panel.csv
```

## Peran dalam PasarPulse

Dataset ini menjadi modalitas utama dan menyediakan:

- harga bulanan komoditas;
- lokasi pasar;
- identitas provinsi;
- indikator coverage dan confidence;
- indikator apakah nilai dihasilkan melalui interpolasi spasial;
- trust score per komoditas.

Harga saat bulan `t` digunakan sebagai observed feature. Harga bulan `t+1` dibentuk sebagai target forecasting.

## Sumber

World Bank Microdata Library, Real-Time Food Prices, Indonesia subset dari tabel global `wld_2021_rtfp_v02_m`, katalog `IDN_2021_RTFP_v02_M`, DOI `10.48529/2ZH0-JF55`.

Pipeline mengambil hanya baris dengan `ISO3=IDN` serta field yang diperlukan, sehingga file raw repository adalah subset analitis dan bukan dump penuh tabel global.

## Grain raw

```text
market location × month
```

Satu baris dapat memuat beberapa kolom komoditas. PasarPulse memilih dua komoditas:

| Kolom sumber | Commodity ID PasarPulse | Interpretasi operasional |
|---|---|---|
| `c_chili` | `CHILI_RED` | seri harga chili pada RTFP; tidak boleh dipersempit menjadi varietas Indonesia tertentu tanpa validasi tambahan |
| `c_onions` | `SHALLOT` | seri onions yang dipakai sebagai proxy shallot dalam pilot |

## Kolom raw yang dipertahankan

| Kolom | Tipe | Penjelasan |
|---|---|---|
| `ISO3` | string | kode negara; harus `IDN` |
| `country` | string | nama negara |
| `adm1_name` | string | provinsi/administrative level 1 |
| `adm2_name` | string | administrative level 2 jika tersedia |
| `mkt_name` | string | nama pasar |
| `geo_id` | string | identifier lokasi pasar |
| `lat`, `lon` | float | koordinat pasar |
| `year`, `month`, `DATES` | temporal | waktu observasi/estimasi bulanan |
| `c_chili`, `c_onions` | float | harga komoditas yang dipilih |
| `trust_chili`, `trust_onions` | float | trust/quality indicator komoditas |
| `data_coverage` | float | coverage data historis lokasi |
| `data_coverage_recent` | float | coverage pada periode terbaru |
| `index_confidence_score` | float | confidence score seri indeks |
| `spatially_interpolated` | numeric/bool | indikator nilai terkait interpolasi spasial |
| `inflation_chili`, `inflation_onions` | float | field perubahan harga sumber; dipertahankan pada raw tetapi tidak menjadi target utama |

Nilai dan rentang quality fields mengikuti definisi sumber. Pipeline tidak mengubahnya menjadi probabilitas.

## Transformasi `rtfp_market_long.csv`

Raw wide table diubah ke long format:

```text
date × adm1_name × market × commodity
```

Kolom utama:

| Kolom | Penjelasan |
|---|---|
| `date` | `DATES` yang dinormalisasi ke awal bulan |
| `adm1_name` | nama provinsi dalam uppercase |
| `mkt_name`, `geo_id` | identitas pasar |
| `lat`, `lon` | koordinat pasar |
| `commodity` | `CHILI_RED` atau `SHALLOT` |
| `price` | nilai dari `c_chili` atau `c_onions` |
| `trust` | nilai trust yang sesuai komoditas |
| quality fields | coverage, confidence, interpolation |

Filtering:

- hanya `ISO3=IDN`;
- tanggal valid;
- provinsi bukan kosong, `NAN`, atau `MARKET AVERAGE`;
- harga harus numerik dan lebih besar dari nol.

## Agregasi `province_commodity_price_panel.csv`

Grain:

```text
province × commodity × month
```

Agregasi yang digunakan:

| Output | Agregasi |
|---|---|
| `price` | median harga seluruh pasar pada provinsi-komoditas-bulan |
| `trust` | median trust |
| `market_count` | jumlah `geo_id` unik |
| `lat`, `lon` | median koordinat pasar |
| `data_coverage` | median |
| `data_coverage_recent` | median |
| `index_confidence_score` | median |
| `spatially_interpolated` | mean; dapat dibaca sebagai proporsi record yang ditandai interpolated bila input biner |

Median dipilih agar lebih robust terhadap pasar dengan nilai ekstrem.

## Missing values

- Harga nonpositif dibuang sebelum agregasi.
- Bulan yang tidak memiliki harga valid tidak menghasilkan row panel.
- Quality fields dapat kosong dan kemudian ditangani oleh median imputation di pipeline model.
- Gap bulan tidak diisi secara manual pada price panel.

## Risiko dan keterbatasan

1. RTFP memadukan observasi dan model-estimated values. Dataset tidak boleh disebut sebagai kumpulan harga survei murni.
2. `CHILI_RED` dan `SHALLOT` adalah mapping operasional pilot, bukan harmonisasi resmi nomenklatur komoditas Indonesia.
3. Harga merupakan estimasi bulanan pada jaringan pasar yang tersedia, bukan sensus seluruh pasar.
4. Median provinsi menyembunyikan variasi antarkota/pasar.
5. `spatially_interpolated`, trust, dan coverage harus dipertahankan agar model mengetahui kualitas input.
6. Perbandingan nominal antartahun perlu mempertimbangkan perubahan level harga dan inflasi; pilot memprediksi nilai seri sebagaimana tersedia.

## Validasi minimum

Sebelum training, pipeline atau audit manual sebaiknya memeriksa:

```text
ISO3 == IDN
price > 0
date is monthly and unique after province-commodity aggregation
coordinates within plausible Indonesia bounds
no duplicate primary key in processed panel
market_count >= 1
```

## Penggunaan yang tepat

- eksperimen forecasting bulanan;
- deteksi risiko price spike;
- ablation quality-aware modeling;
- analisis propagasi antardaerah pada level penelitian.

Tidak tepat untuk menetapkan harga resmi, intervensi perdagangan otomatis, atau klaim causal effect.