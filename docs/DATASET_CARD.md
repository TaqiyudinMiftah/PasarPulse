# PasarPulse Dataset Card

## Summary

PasarPulse is a multimodal monthly panel for early warning of regional food-price shocks in Indonesia. The current pilot aligns three modalities on the key:

```text
province × commodity × month
```

The generated dataset covers red chili and shallot across 34 Indonesian provinces. It combines market-price estimates, agroclimate observations, and spatial-neighbor features.

## Dataset scope

| Item | Value |
|---|---|
| Geographic scope | 34 Indonesian provinces represented in the World Bank RTFP source |
| Commodities | `CHILI_RED`, `SHALLOT` |
| Price period | January 2007–July 2026 in the downloaded source snapshot |
| Weather period used by the pilot | January 2007–December 2025 |
| Modeling frequency | Monthly |
| Raw selected World Bank rows | 52,405 |
| Master modeling rows | 15,980 |
| Train period | January 2007–December 2023 |
| Test period | January 2024–December 2025 |
| Train rows | 13,872 |
| Test rows | 1,632 |

The exact counts may change when the upstream live datasets are updated.

## Modalities

### 1. Food-price modality

Source: World Bank Microdata Library, *Monthly food price estimates by product and market*, reference `IDN_2021_RTFP_v02_M`, DOI `10.48529/2ZH0-JF55`.

The RTFP source is updated over time and combines directly measured public price records with machine-learning estimates of missing values. The pilot uses:

- `c_chili`: monthly closing price estimate for chili;
- `c_onions`: monthly closing price estimate for onions/shallot;
- `trust_chili` and `trust_onions`;
- market coordinates;
- data-coverage and interpolation indicators.

The model must not be described as trained exclusively on directly observed prices.

### 2. Agroclimate modality

Source: NASA POWER Monthly Point API, agricultural community.

Variables:

- `T2M`: temperature at 2 metres;
- `T2M_MAX`: maximum temperature at 2 metres;
- `T2M_MIN`: minimum temperature at 2 metres;
- `PRECTOTCORR`: corrected precipitation;
- `RH2M`: relative humidity at 2 metres;
- `WS2M`: wind speed at 2 metres;
- `ALLSKY_SFC_SW_DWN`: all-sky surface shortwave irradiance.

Weather observations are downloaded at the median coordinate of markets in each province. This is a province-level approximation, not a crop-field measurement.

### 3. Spatial modality

A directed k-nearest-neighbor graph is derived from province market-centroid coordinates. Each province is connected to its three geographically nearest province centroids using haversine distance.

Derived features include the distance-weighted price of neighboring provinces and its difference or ratio relative to the focal province.

## Generated files

The GitHub Actions pipeline writes the following files to `outputs/`:

| File | Description |
|---|---|
| `IDN_RTFP_selected.csv` | Selected Indonesia rows from the World Bank table |
| `IDN_RTFP_market_long.csv` | Long market-level chili and shallot table |
| `province_commodity_price_panel.csv` | Province–commodity monthly median price panel |
| `province_market_centroids.csv` | Province market-centroid coordinates |
| `NASA_POWER_monthly_province.csv` | Monthly agroclimate modality |
| `province_knn_graph.csv` | Spatial graph edge list |
| `master_modeling_table.csv` | Leakage-aware aligned modeling table |
| `metrics.csv` | Regression and classification metrics |
| `test_predictions.csv` | Out-of-time test predictions |
| `*.joblib` | Fitted scikit-learn pipelines |
| `model_comparison.png` | Regression comparison plot |
| `forecast_plot.png` | Example forecast visualization |
| `data_quality.json` | Dataset coverage and split summary |
| `RUN_REPORT.md` | Automatically generated run report |

A compressed copy is generated as `PasarPulse_Multimodal_Dataset_Model_Results.zip`.

## Targets

### Regression target

The next month's provincial median commodity price:

```text
target_price = price(t + 1 month)
```

### Classification target

A next-month price spike:

```text
spike = 1 when target_price / price(t) - 1 >= 0.10
```

## Temporal leakage controls

- Train and test sets are separated chronologically.
- Price lags and rolling statistics use historical values only.
- Weather is joined by the same observation month for this retrospective pilot.
- Neighbor-price features use contemporaneous prices and are therefore appropriate for same-month monitoring and one-month-ahead forecasting after the current monthly observations are available.
- Preprocessing is fitted on the training period only through scikit-learn pipelines.

## Intended use

The dataset is intended for:

- research on multimodal food-price forecasting;
- early warning of regional price shocks;
- ablation studies comparing price-only, weather, and spatial features;
- educational and competition prototypes.

## Out-of-scope use

The dataset should not be used as:

- an official replacement for BPS, Bank Indonesia, or Badan Pangan Nasional statistics;
- proof that a weather event caused a price change;
- a fully observed transaction-price database;
- a basis for automated market intervention without expert review;
- a daily or real-time forecasting benchmark.

## Known limitations

1. The source price series includes model-estimated missing values.
2. Commodity labels are broad; chili is not separated into every Indonesian market variety.
3. NASA POWER is sampled at province market centroids, not weighted by crop production areas.
4. The spatial graph encodes proximity, not verified logistics or trade flows.
5. Monthly aggregation can hide short-lived weekly shocks.
6. Upstream datasets are live and may revise historical observations.
7. Province definitions and coverage follow the source snapshot and may not reflect the newest administrative subdivisions.

## Reproducibility

Run:

```bash
python -m pip install -r requirements.txt
python src/run_pipeline.py
```

The pipeline downloads the upstream sources and recreates the aligned data, fitted models, predictions, plots, metrics, and run report.

## Citation

Price source:

> Andrée, B. P. J. (2021). Monthly food price estimates by product and market. `IDN_2021_RTFP_v02_M`. World Bank Microdata Library. https://doi.org/10.48529/2ZH0-JF55

NASA POWER acknowledgement:

> The data was obtained from the NASA Langley Research Center POWER Project funded through the NASA Earth Science Division. Include the service name, version, and access date in publications.
