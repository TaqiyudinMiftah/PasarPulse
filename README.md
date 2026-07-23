# PasarPulse

Multimodal early-warning pilot for regional food-price shocks in Indonesia.

PasarPulse aligns market prices, agroclimate observations, and spatial-neighbor information on:

```text
province × commodity × month
```

The current pilot forecasts the next month's provincial median price and classifies whether the next month increases by at least 10%.

## Modalities

- World Bank Real-Time Food Prices for chili and shallot proxies
- NASA POWER monthly agroclimate variables
- Province-level spatial graph derived from georeferenced market centroids

## Actual pilot result

The out-of-time experiment used 13,872 training rows through December 2023 and 1,632 test rows covering January 2024–December 2025.

| Model | MAE | sMAPE | Directional accuracy |
|---|---:|---:|---:|
| Naive last price | 4,536.38 | 9.69% | 1.5% |
| ML price-only | 4,891.56 | 10.27% | 55.2% |
| ML price + weather | 4,693.01 | 9.91% | 56.3% |
| ML price + weather + spatial | 4,641.57 | 9.83% | 57.4% |

For price-spike classification, multimodal features improved PR-AUC and recall relative to the price-only classifier. The strongest current product interpretation is multimodal **price-shock early warning**, not guaranteed superiority in nominal-price forecasting.

## Repository structure

```text
.github/workflows/              reproducible data/model workflow
src/                            end-to-end pipeline

data/
├── raw/                        upstream query snapshots
├── interim/                    normalized and reshaped datasets
└── processed/                  training-ready and graph datasets

models/                         fitted `.joblib` pipelines
reports/
├── metrics/                    aggregate evaluation metrics
├── predictions/                out-of-time predictions
└── figures/                    charts and diagnostics

artifacts/                      complete ZIP bundle
docs/datasets/                  technical documentation per dataset
docs/                           dataset card, model card, provenance, results
```

## Dataset locations

| Dataset | Path |
|---|---|
| World Bank RTFP Indonesia subset | `data/raw/world_bank_rtfp_indonesia_selected.csv` |
| NASA POWER monthly province weather | `data/raw/nasa_power_monthly_province.csv` |
| Market-level long price table | `data/interim/rtfp_market_long.csv` |
| Province market centroids | `data/interim/province_market_centroids.csv` |
| Province-commodity price panel | `data/processed/province_commodity_price_panel.csv` |
| Province spatial graph | `data/processed/province_knn_graph.csv` |
| Final training table | `data/processed/master_modeling_table.csv` |

## Technical documentation

- [Dataset documentation index](docs/datasets/README.md)
- [World Bank RTFP technical notes](docs/datasets/WORLD_BANK_RTFP.md)
- [NASA POWER technical notes](docs/datasets/NASA_POWER.md)
- [Spatial graph technical notes](docs/datasets/SPATIAL_GRAPH.md)
- [Derived tables and master schema](docs/datasets/DERIVED_TABLES.md)
- [Model output data and artefacts](docs/datasets/MODEL_OUTPUT_DATA.md)
- [Dataset card](docs/DATASET_CARD.md)
- [Data provenance and attribution](docs/DATA_PROVENANCE_AND_LICENSES.md)
- [Model card](docs/MODEL_CARD.md)
- [Experimental results](docs/RESULTS.md)

## Run locally

```bash
python -m pip install -r requirements.txt
python src/run_pipeline.py
```

The source script initially writes generated files to a temporary `outputs/` staging directory. GitHub Actions then reorganizes them into `data/`, `models/`, `reports/`, and `artifacts/` before committing the snapshot.

## Data caveats

World Bank RTFP combines observed public price records with model-estimated missing prices. Trust, coverage, confidence, and interpolation indicators are retained as model features. Results must not be described as training only on directly observed prices or as official Indonesian price forecasts.

NASA POWER values are sampled at province market-centroid coordinates and do not directly measure commodity-growing areas.

## Sources

- World Bank Microdata Library: `IDN_2021_RTFP_v02_M`, DOI `10.48529/2ZH0-JF55`
- NASA POWER Monthly Point API