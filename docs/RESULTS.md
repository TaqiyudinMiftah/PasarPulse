# PasarPulse Multimodal Pilot Results

## Aligned training design

Primary key: `province × commodity × month`.

- Price modality: World Bank Real-Time Food Prices, chili and shallot.
- Weather modality: NASA POWER monthly temperature, precipitation, humidity, wind, and solar radiation.
- Spatial modality: a three-nearest-province graph computed from market coordinates.

## Dataset coverage

- Selected World Bank rows: 52,405
- Provinces: 34
- Price period: January 2007–July 2026
- Weather period: January 2007–December 2025
- Modeling rows: 15,980
- Mean raw-weather missing fraction after join: 3.0%

## Temporal evaluation

- Training: January 2007–December 2023, 13,872 rows
- Testing: January 2024–December 2025, 1,632 rows

Random splitting was not used.

## Next-month price forecasting

| Model | MAE | RMSE | sMAPE | Directional accuracy |
|---|---:|---:|---:|---:|
| Naive last | 4,536.38 | 5,991.67 | 9.69% | 1.47% |
| Seasonal naive | 8,987.07 | 11,619.53 | 19.74% | 51.90% |
| ML price-only | 4,891.56 | 6,391.53 | 10.27% | 55.21% |
| ML price + weather | 4,693.01 | 6,287.29 | 9.91% | 56.25% |
| ML price + weather + spatial | 4,641.57 | 6,189.13 | 9.83% | 57.35% |

The persistence baseline remains best for absolute price error. Within the machine-learning ablation, weather and spatial context consistently improve MAE, RMSE, sMAPE, and directional accuracy.

## Price-spike early warning

Spike definition: next-month price increase of at least 10%.

| Model | PR-AUC | ROC-AUC | F1 | Recall |
|---|---:|---:|---:|---:|
| Price-only | 0.251 | 0.517 | 0.286 | 0.461 |
| Multimodal | 0.292 | 0.554 | 0.330 | 0.566 |

The strongest evidence for multimodality is on early-warning classification rather than exact nominal-price prediction.

## Interpretation boundary

The World Bank RTFP dataset includes observed records and model-estimated missing prices. These experiments therefore evaluate forecasting over the RTFP series, not over purely observed market-survey prices.
