# Generated Outputs

This directory is populated by the PasarPulse GitHub Actions workflow and by local runs of `src/run_pipeline.py`.

Expected files:

```text
IDN_RTFP_selected.csv
IDN_RTFP_market_long.csv
province_commodity_price_panel.csv
province_market_centroids.csv
NASA_POWER_monthly_province.csv
province_knn_graph.csv
master_modeling_table.csv
metrics.csv
test_predictions.csv
ML_price_only.joblib
ML_price_weather.joblib
ML_price_weather_spatial.joblib
spike_price_only.joblib
spike_multimodal.joblib
model_comparison.png
forecast_plot.png
data_quality.json
RUN_REPORT.md
run.log
```

## Source versus derived files

- `IDN_RTFP_selected.csv` is a filtered copy of fields obtained from the World Bank data service.
- `NASA_POWER_monthly_province.csv` is a downloaded point-sample weather table.
- All other files are PasarPulse-derived transformations, models, predictions, or reports.

## Large generated snapshot

The workflow also creates:

```text
PasarPulse_Multimodal_Dataset_Model_Results.zip
```

at the repository root and uploads the same bundle as a GitHub Actions artifact.

## Do not edit manually

Generated outputs should be changed by rerunning the pipeline. Manual edits make the snapshot irreproducible.

See `docs/DATASET_CARD.md`, `docs/DATA_DICTIONARY.md`, and `docs/MODEL_CARD.md` before using the files.
