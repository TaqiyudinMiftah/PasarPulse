# Model Output Data and Artefacts

Artefak hasil modeling dipisahkan dari dataset sumber agar tidak tercampur dengan input training.

## Struktur

```text
models/                  fitted scikit-learn pipelines
reports/metrics/         metrik evaluasi
reports/predictions/     out-of-time predictions
reports/figures/         visualisasi
reports/                 run report, data quality, dan log
artifacts/               compressed complete bundle
```

## `reports/metrics/metrics.csv`

### Grain

```text
one row per task × model
```

### Kolom

| Kolom | Task | Penjelasan |
|---|---|---|
| `task` | semua | `regression` atau `classification` |
| `model` | semua | identifier model |
| `MAE` | regresi | mean absolute error pada nominal harga |
| `RMSE` | regresi | root mean squared error |
| `sMAPE_pct` | regresi | symmetric MAPE dalam persen |
| `directional_accuracy` | regresi | proporsi prediksi arah naik/turun yang sama dengan aktual |
| `PR_AUC` | klasifikasi | area under precision-recall curve; penting untuk target spike yang tidak seimbang |
| `ROC_AUC` | klasifikasi | ranking performance positif vs negatif |
| `F1` | klasifikasi | harmonic mean precision dan recall pada threshold yang digunakan |
| `recall` | klasifikasi | proporsi spike aktual yang terdeteksi |

Kolom yang tidak relevan terhadap task dibiarkan kosong.

## `reports/predictions/test_predictions.csv`

### Grain

```text
one row per held-out province × commodity × target month
```

Dataset ini memuat identifier row test, nilai aktual, current price, dan prediksi setiap baseline/model. Nama kolom aktual mengikuti output pipeline. Digunakan untuk:

- error analysis per provinsi/komoditas;
- plotting;
- calibration analysis;
- reproduksi metrik agregat;
- analisis false positive/false negative price spike.

Prediksi berasal dari out-of-time test dan tidak boleh dicampurkan kembali ke training tanpa penandaan split.

## `models/*.joblib`

Model files adalah serialized scikit-learn `Pipeline` yang mencakup preprocessing dan estimator. Artefak saat ini meliputi:

```text
ML_price_only.joblib
ML_price_weather.joblib
ML_price_weather_spatial.joblib
spike_price_only.joblib
spike_multimodal.joblib
```

### Persyaratan loading

Gunakan versi dependency yang kompatibel dengan `requirements.txt`:

```python
import joblib
model = joblib.load("models/ML_price_weather_spatial.joblib")
```

Input inference harus memiliki nama kolom yang sama dengan saat training. Serialized model tidak menjamin backward compatibility antarversi scikit-learn.

### Keamanan

File `joblib`/pickle hanya boleh dimuat dari repository atau sumber tepercaya karena deserialization dapat mengeksekusi kode.

## `reports/data_quality.json`

Ringkasan machine-readable mengenai:

- jumlah raw rows;
- jumlah provinsi;
- periode harga dan cuaca;
- jumlah master rows;
- missingness cuaca;
- split train/test;
- best model summary.

File ini cocok untuk dashboard run monitoring dan audit cepat, tetapi tidak menggantikan pemeriksaan row-level.

## `reports/RUN_REPORT.md`

Laporan manusia yang menjelaskan scope run, data volume, split, hasil utama, file yang dihasilkan, dan caveat interpretasi.

## `reports/run.log`

Log eksekusi pipeline untuk debugging. Log dapat memuat warning API atau retry tetapi tidak boleh memuat credential. Saat ini seluruh source API bersifat publik dan pipeline tidak memerlukan secret data credential.

## Figures

```text
reports/figures/model_comparison.png
reports/figures/forecast_plot.png
```

- `model_comparison.png`: perbandingan performa model.
- `forecast_plot.png`: contoh/aggregate actual versus prediction pada test period.

Figure adalah visual summary; angka resmi eksperimen harus dibaca dari `metrics.csv`.

## `artifacts/PasarPulse_Multimodal_Dataset_Model_Results.zip`

Bundle lengkap berisi:

```text
data/
models/
reports/
docs/datasets/
```

ZIP disediakan untuk distribusi mudah. Repository folders tetap menjadi source of truth yang lebih mudah diaudit.

## Versioning

Setiap regenerated snapshot dapat berubah karena upstream API diperbarui. Untuk hasil yang dapat dikutip:

1. catat commit SHA;
2. catat workflow run;
3. simpan `data_quality.json`;
4. gunakan file pada commit tersebut, bukan branch `main` yang dapat berubah;
5. cantumkan tanggal pengambilan data.