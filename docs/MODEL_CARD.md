# PasarPulse Model Card

## Model purpose

PasarPulse is an experimental multimodal early-warning system for regional food-price shocks in Indonesia. The pilot performs two tasks:

1. one-month-ahead regression of provincial median commodity prices;
2. classification of a next-month price increase of at least 10%.

The current model is a research baseline, not an operational policy engine.

## Inputs

The model consumes features aligned on `province × commodity × month`:

- current and lagged food prices;
- rolling price statistics and source-quality indicators;
- monthly NASA POWER agroclimate variables;
- geographically neighboring province prices;
- province, commodity, and calendar variables.

## Output

Regression output:

```text
predicted price for month t+1
```

Classification output:

```text
probability that price(t+1) / price(t) - 1 >= 10%
```

## Algorithms

The pilot compares:

- last-value naive baseline;
- 12-month seasonal naive baseline;
- price-only histogram gradient boosting;
- price plus weather histogram gradient boosting;
- price plus weather plus spatial features histogram gradient boosting;
- price-only and multimodal histogram gradient-boosting classifiers.

Categorical variables are one-hot encoded. Numeric variables use training-period median imputation inside the fitted scikit-learn pipeline.

## Evaluation design

The successful pilot used an out-of-time split:

| Split | Period | Rows |
|---|---|---:|
| Train | January 2007–December 2023 | 13,872 |
| Test | January 2024–December 2025 | 1,632 |

Random splitting is intentionally avoided.

## Actual pilot results

### Regression

| Model | MAE | RMSE | sMAPE | Directional accuracy |
|---|---:|---:|---:|---:|
| Naive last price | 4,536.38 | 5,991.67 | 9.69% | 1.5% |
| Seasonal naive | 8,987.07 | 11,619.53 | 19.74% | 51.9% |
| ML price-only | 4,891.56 | 6,391.53 | 10.27% | 55.2% |
| ML price + weather | 4,693.01 | 6,287.29 | 9.91% | 56.3% |
| ML price + weather + spatial | 4,641.57 | 6,189.13 | 9.83% | 57.4% |

The last-value baseline remains best for absolute price error. The multimodal model improves on the price-only machine-learning model but does not beat persistence on MAE or sMAPE.

### Price-spike classification

| Model | PR-AUC | ROC-AUC | F1 | Recall |
|---|---:|---:|---:|---:|
| Price-only | 0.251 | 0.517 | 0.286 | 0.461 |
| Multimodal | 0.292 | 0.554 | 0.330 | 0.566 |

The multimodal classifier improves price-spike recall and PR-AUC over the price-only classifier. Absolute performance is still modest and requires further validation.

## Recommended interpretation

The most defensible current claim is:

> Agroclimate and spatial features add useful signal for regional price-shock early warning relative to a price-only machine-learning baseline.

Avoid claiming:

- that the multimodal model is the best nominal price forecaster;
- causal effects of weather on prices;
- production-ready accuracy;
- daily early warning;
- official price forecasts.

## Known limitations

- The price source includes machine-learning-estimated missing observations.
- Monthly data provide relatively few rare shock examples.
- Weather is represented by province market-centroid point samples.
- The spatial graph represents proximity, not verified supply routes.
- Threshold-dependent F1 and recall can change with class imbalance and decision thresholds.
- No external validation against PIHPS, Bapanas, or BPS price series is included yet.
- No Sentinel-2 or BPS production modality is included in the successful pilot snapshot.

## Appropriate uses

- benchmark and ablation experiments;
- competition prototypes;
- exploratory regional monitoring;
- identification of high-risk province–commodity months for analyst review.

## Inappropriate uses

- automatic trade or stockpiling decisions;
- direct allocation of public budgets;
- claims of manipulation or wrongdoing by a region or market;
- replacing official government statistics;
- high-stakes forecasts without human review and external data validation.

## Next validation steps

1. Add a rolling-origin backtest rather than a single test window.
2. Report performance separately by commodity and province.
3. Tune and calibrate spike probabilities.
4. Compare with class-weighted logistic regression and stronger time-series baselines.
5. Validate against an independently sourced official Indonesian price series.
6. Replace geographic k-nearest neighbors with empirically learned or logistics-informed graph edges.
7. Test whether production and vegetation modalities improve rare-shock detection.
