# PasarPulse Multimodal Pilot — Actual Run

## Scope

This run uses three train-compatible modalities at a common **province × commodity × month** key:

1. World Bank Real-Time Food Prices: chili and shallot market-price estimates.
2. NASA POWER monthly agroclimate variables at province market-centroid coordinates.
3. A spatial k-nearest-province graph derived from georeferenced markets.

The experiment forecasts the next month's provincial median price and classifies a >=10% next-month price spike.

## Data

- World Bank selected raw rows: 52,405
- Provinces in model: 34
- Price period: 2007-01-01 to 2026-07-01
- Weather period: 2007-01-01 to 2025-12-01
- Master rows: 15,980
- Mean missing fraction across raw weather fields after join: 0.030

The World Bank RTFP series combines observed survey records with machine-learning estimates of missing prices. Trust and coverage fields are retained as model inputs; results must not be described as forecasts trained only on directly observed prices.

## Out-of-time split

- Train: 2007-01-01 to 2023-12-01 (13,872 rows)
- Test: 2024-01-01 to 2025-12-01 (1,632 rows)

## Best regression result

- Model: naive_last
- MAE: 4,536.38
- RMSE: 5,991.67
- sMAPE: 9.69%
- Directional accuracy: 0.015

See `metrics.csv`, `test_predictions.csv`, and the PNG plots for the complete comparison. The important scientific comparison is the ablation from price-only → price+weather → price+weather+spatial graph.

## Files

- `IDN_RTFP_selected.csv`: selected World Bank raw API rows.
- `IDN_RTFP_market_long.csv`: chili/shallot long market table.
- `NASA_POWER_monthly_province.csv`: downloaded weather modality.
- `province_knn_graph.csv`: spatial graph edges.
- `master_modeling_table.csv`: leakage-aware aligned training table.
- `metrics.csv`: baseline and model metrics.
- `test_predictions.csv`: out-of-time predictions.
- `*.joblib`: fitted scikit-learn pipelines.
- `model_comparison.png`, `forecast_plot.png`: result visualizations.

## Sources

- World Bank Microdata Library, IDN_2021_RTFP_v02_M, DOI 10.48529/2ZH0-JF55.
- NASA POWER Monthly Point API.
