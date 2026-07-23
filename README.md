# PasarPulse

Multimodal early-warning pilot for regional food-price shocks in Indonesia.

PasarPulse aligns market prices, agroclimate observations, and spatial-neighbor information on:

```text
province × commodity × month
```

The current pilot forecasts the next month's provincial median price and classifies whether the next month increases by at least 10%.

## Modalities

- World Bank Real-Time Food Prices for red chili and shallot
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

For price-spike classification, multimodal features improved PR-AUC from 0.251 to 0.292 and recall from 0.461 to 0.566 relative to the price-only classifier.

The last-value baseline still has the lowest absolute forecasting error. The strongest current product interpretation is therefore multimodal **price-shock early warning**, not superior nominal-price forecasting.

## Repository structure

```text
.github/workflows/pasarpulse-pipeline.yml  Reproducible data/model workflow
data/README.md                              Data directory contract
docs/DATASET_CARD.md                       Dataset scope and limitations
docs/DATA_DICTIONARY.md                    Column-level documentation
docs/DATA_PROVENANCE_AND_LICENSES.md       Sources and attribution
docs/MODEL_CARD.md                         Model results and appropriate use
docs/RESULTS.md                            Concise experimental results
outputs/                                   Generated datasets, models, and reports
src/run_pipeline.py                        End-to-end pipeline
requirements.txt                           Python dependencies
```

## Run locally

```bash
python -m pip install -r requirements.txt
python src/run_pipeline.py
```

The pipeline downloads open upstream data, builds the aligned multimodal table, trains baselines and multimodal models, and writes datasets, fitted models, metrics, predictions, plots, and a run report to `outputs/`.

## Generated bundle

A successful workflow creates:

```text
PasarPulse_Multimodal_Dataset_Model_Results.zip
```

The ZIP contains the source subsets used by the pilot, derived tables, spatial graph, master modeling table, fitted models, predictions, metrics, figures, data-quality summary, and run report.

## Documentation

- [Dataset card](docs/DATASET_CARD.md)
- [Data dictionary](docs/DATA_DICTIONARY.md)
- [Data provenance and attribution](docs/DATA_PROVENANCE_AND_LICENSES.md)
- [Model card](docs/MODEL_CARD.md)
- [Experimental results](docs/RESULTS.md)

## Data caveat

World Bank RTFP combines observed public price records with model-estimated missing prices. Trust, coverage, confidence, and interpolation indicators are retained as features. Results must not be described as training only on directly observed prices or as official Indonesian price forecasts.

NASA POWER values are sampled at province market-centroid coordinates and do not directly measure commodity-growing areas.

## Sources

- World Bank Microdata Library: `IDN_2021_RTFP_v02_M`, DOI `10.48529/2ZH0-JF55`
- NASA POWER Monthly Point API
