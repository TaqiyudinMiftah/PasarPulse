# PasarPulse

Multimodal early-warning pilot for regional food-price shocks in Indonesia.

## Modalities

- World Bank Real-Time Food Prices for chili and shallot
- NASA POWER monthly agroclimate variables
- Province-level spatial graph derived from market coordinates

All modalities are aligned on `province × commodity × month`. The pipeline forecasts the next month's price and classifies a price spike of at least 10%.

## Actual pilot result

The out-of-time experiment used 13,872 training rows through December 2023 and 1,632 test rows covering January 2024–December 2025.

| Model | MAE | sMAPE | Directional accuracy |
|---|---:|---:|---:|
| Naive last price | 4,536.38 | 9.69% | 1.5% |
| ML price-only | 4,891.56 | 10.27% | 55.2% |
| ML price + weather | 4,693.01 | 9.91% | 56.3% |
| ML price + weather + spatial | 4,641.57 | 9.83% | 57.4% |

For price-spike classification, multimodal features improved PR-AUC from 0.251 to 0.292 and recall from 0.461 to 0.566.

## Run

```bash
python -m pip install -r requirements.txt
python src/run_pipeline.py
```

The pipeline downloads open data, builds the aligned table, trains all baselines and multimodal models, and writes datasets, models, metrics, predictions, plots, and a report to `outputs/`.

## Data caveat

World Bank RTFP combines observed survey records with model-estimated missing prices. Trust, coverage, confidence, and interpolation indicators are retained as features. Results must not be described as training only on directly observed prices.

## Sources

- World Bank Microdata Library: `IDN_2021_RTFP_v02_M`, DOI `10.48529/2ZH0-JF55`
- NASA POWER Monthly Point API
