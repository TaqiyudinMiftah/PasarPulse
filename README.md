# PasarPulse

Multimodal early-warning pilot for regional food-price shocks in Indonesia.

PasarPulse combines four different data structures:

```text
price time series
+ agroclimate covariates
+ Sentinel-2 image tensors
+ province relations
```

The tabular contract is `province × commodity × month`. Sentinel-2 samples use `province × year × quarter` and are attached with a leakage-safe backward as-of join based on acquisition time.

## Modalities

1. World Bank Real-Time Food Prices for chili and shallot proxies.
2. NASA POWER monthly agroclimate variables.
3. Copernicus Sentinel-2 L2A four-band image tensors (`B02`, `B03`, `B04`, `B08`).
4. Province-level spatial relationships derived from georeferenced market centroids.

The existing published baseline models use price, weather, and engineered spatial features. The Sentinel-2 dataset is stored image-native so the next model can use a separate CNN or Vision Transformer encoder rather than reducing every input to one tabular feature matrix.

## Existing tabular pilot result

The out-of-time experiment used 13,872 training rows through December 2023 and 1,632 test rows covering January 2024–December 2025.

| Model | MAE | sMAPE | Directional accuracy |
|---|---:|---:|---:|
| Naive last price | 4,536.38 | 9.69% | 1.5% |
| ML price-only | 4,891.56 | 10.27% | 55.2% |
| ML price + weather | 4,693.01 | 9.91% | 56.3% |
| ML price + weather + spatial | 4,641.57 | 9.83% | 57.4% |

The strongest current product interpretation is price-shock early warning. The image modality must be evaluated through a separate temporal + vision fusion experiment before claiming an accuracy improvement from satellite data.

## Repository structure

```text
.github/workflows/              reproducible data and modeling workflows
src/                            data builders and model pipelines

data/
├── raw/                        upstream tabular snapshots
├── interim/                    normalized and reshaped tables
├── processed/                  training-ready tabular and graph datasets
└── satellite/                  image tensors, masks, metadata, and manifest

models/                         fitted tabular `.joblib` pipelines
reports/
├── metrics/                    aggregate evaluation metrics
├── predictions/                out-of-time predictions
└── figures/                    charts and satellite previews

artifacts/                      compressed dataset bundles
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
| Final tabular training table | `data/processed/master_modeling_table.csv` |
| Sentinel-2 sample metadata | `data/satellite/metadata.csv` |
| Sentinel-2 image shards | `data/satellite/chips/sentinel2_quarterly_YYYY.npz` |
| Satellite dataset manifest | `data/satellite/manifest.json` |

## Sentinel-2 image format

Each annual NPZ shard contains:

```text
images       N × 4 × 64 × 64 uint16
valid_masks  N × 64 × 64 uint8
sample_ids   N strings
```

Band order:

```text
0 B02 blue
1 B03 green
2 B04 red
3 B08 near infrared
```

The default build selects one least-cloudy scene per province per quarter from 2022–2025. Every patch covers approximately 6.4 km × 6.4 km around the province market centroid and is resampled to 64 × 64 pixels. The Scene Classification Layer is used to mask no-data, cloud shadow, cloud, cirrus, snow, and defective pixels.

These patches represent regional landscape context around market centres. They are not verified chili or shallot field imagery.

## Technical documentation

- [Dataset documentation index](docs/datasets/README.md)
- [World Bank RTFP technical notes](docs/datasets/WORLD_BANK_RTFP.md)
- [NASA POWER technical notes](docs/datasets/NASA_POWER.md)
- [Sentinel-2 image dataset](docs/datasets/SENTINEL2_IMAGERY.md)
- [Spatial graph technical notes](docs/datasets/SPATIAL_GRAPH.md)
- [Derived tables and master schema](docs/datasets/DERIVED_TABLES.md)
- [Model output data and artefacts](docs/datasets/MODEL_OUTPUT_DATA.md)
- [Dataset card](docs/DATASET_CARD.md)
- [Data provenance and attribution](docs/DATA_PROVENANCE_AND_LICENSES.md)
- [Model card](docs/MODEL_CARD.md)
- [Experimental results](docs/RESULTS.md)

## Run locally

Tabular pipeline:

```bash
python -m pip install -r requirements.txt
python src/run_pipeline.py
```

Satellite image dataset:

```bash
python -m pip install -r requirements-satellite.txt
python src/download_sentinel2_chips.py
```

## Data caveats

World Bank RTFP combines observed public price records with model-estimated missing prices. Results must not be described as forecasts trained only on directly observed prices or as official Indonesian price forecasts.

NASA POWER values and Sentinel-2 patches are anchored to province market-centroid coordinates. They do not directly measure commodity-specific production fields.

## Sources

- World Bank Microdata Library: `IDN_2021_RTFP_v02_M`, DOI `10.48529/2ZH0-JF55`
- NASA POWER Monthly Point API
- Copernicus Sentinel-2 Level-2A, accessed through the Microsoft Planetary Computer STAC API
