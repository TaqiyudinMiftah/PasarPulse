# PasarPulse Data Dictionary

This document describes the principal columns written by the reproducible pilot. The upstream live sources can add fields, but the modeling contract below is stable.

## `outputs/IDN_RTFP_selected.csv`

| Column | Type | Description |
|---|---|---|
| `ISO3` | string | ISO-3 country code; filtered to `IDN` |
| `country` | string | Country name |
| `adm1_name` | string | First-level administrative area from the World Bank source |
| `adm2_name` | string | Second-level administrative area when available |
| `mkt_name` | string | Market name |
| `lat`, `lon` | float | Georeferenced market coordinate |
| `geo_id` | string/integer | Market-location identifier |
| `year`, `month`, `DATES` | temporal | Observation month |
| `data_coverage` | float | Source coverage indicator |
| `data_coverage_recent` | float | Recent coverage indicator |
| `index_confidence_score` | float | Source confidence measure |
| `spatially_interpolated` | numeric/binary | Indicates spatial interpolation in the upstream series |
| `c_chili` | float | Chili monthly closing-price estimate in local currency per source unit |
| `c_onions` | float | Onion/shallot monthly closing-price estimate in local currency per source unit |
| `trust_chili` | float | Chili reliability score supplied by the source |
| `trust_onions` | float | Onion/shallot reliability score supplied by the source |
| `inflation_chili` | float | Upstream chili inflation estimate |
| `inflation_onions` | float | Upstream onion inflation estimate |

## `outputs/IDN_RTFP_market_long.csv`

| Column | Type | Description |
|---|---|---|
| `date` | date | Month normalized to the first day |
| `adm1_name` | string | Upper-case province/source administrative name |
| `mkt_name` | string | Market name |
| `geo_id` | string/integer | Market identifier |
| `lat`, `lon` | float | Market coordinate |
| `price` | float | Commodity closing-price estimate |
| `trust` | float | Commodity-specific reliability score |
| `data_coverage` | float | Coverage measure |
| `data_coverage_recent` | float | Recent coverage measure |
| `index_confidence_score` | float | Source confidence measure |
| `spatially_interpolated` | float | Interpolation indicator |
| `commodity` | category | `CHILI_RED` or `SHALLOT` |

## `outputs/province_commodity_price_panel.csv`

| Column | Type | Description |
|---|---|---|
| `date` | date | Month |
| `adm1_name` | string | Province/source administrative name |
| `commodity` | category | Commodity identifier |
| `price` | float | Median market price within province and commodity |
| `trust` | float | Median trust score |
| `market_count` | integer | Number of distinct market locations contributing |
| `lat`, `lon` | float | Median coordinate of contributing markets |
| `data_coverage` | float | Median source coverage |
| `data_coverage_recent` | float | Median recent coverage |
| `index_confidence_score` | float | Median confidence score |
| `spatially_interpolated` | float | Mean interpolation indicator across contributing records |
| `neighbor_price` | float | Distance-weighted contemporaneous price of nearest provinces |
| `neighbor_price_ratio` | float | Ratio of focal to neighboring price, when generated |
| `neighbor_gap` | float | Difference between focal and neighboring price, when generated |

## `outputs/province_market_centroids.csv`

| Column | Type | Description |
|---|---|---|
| `adm1_name` | string | Province/source administrative name |
| `lat`, `lon` | float | Median coordinate of markets in the province |
| `market_locations` | integer | Count of unique market locations |

## `outputs/NASA_POWER_monthly_province.csv`

| Column | Type | Description |
|---|---|---|
| `adm1_name` | string | Province/source administrative name |
| `date` | date | Month |
| `weather_lat`, `weather_lon` | float | Coordinate sent to NASA POWER |
| `T2M` | float | Mean air temperature at 2 m |
| `T2M_MAX` | float | Maximum air temperature at 2 m |
| `T2M_MIN` | float | Minimum air temperature at 2 m |
| `PRECTOTCORR` | float | Corrected precipitation |
| `RH2M` | float | Relative humidity at 2 m |
| `WS2M` | float | Wind speed at 2 m |
| `ALLSKY_SFC_SW_DWN` | float | All-sky surface shortwave irradiance |

NASA POWER units follow the API's agricultural-community response. Consult the NASA POWER parameter dictionary for the exact service-version units used by a particular run.

## `outputs/province_knn_graph.csv`

| Column | Type | Description |
|---|---|---|
| `adm1_name` | string | Source node province |
| `neighbor` | string | Neighbor node province |
| `rank` | integer | Neighbor rank from 1 to 3 |
| `distance_km` | float | Haversine distance between province market centroids |

The graph is directed because each province stores its own three nearest neighbors.

## `outputs/master_modeling_table.csv`

Core identifiers and targets:

| Column | Type | Description |
|---|---|---|
| `date` | date | Feature month |
| `adm1_name` | category | Province/source administrative area |
| `commodity` | category | Commodity identifier |
| `price` | float | Price observed/estimated for the feature month |
| `target_price` | float | Next-month price |
| `target_return` | float | Next-month proportional price change |
| `spike` | binary | 1 when next-month return is at least 10% |

Typical historical and quality features:

| Feature family | Example columns | Meaning |
|---|---|---|
| Price lags | `price_lag_1`, `price_lag_2`, `price_lag_3`, `price_lag_6`, `price_lag_12` | Historical monthly prices |
| Returns | lagged/rolling return fields | Historical price changes |
| Rolling level | rolling means/medians | Recent price level |
| Volatility | rolling standard deviation | Recent price variability |
| Source quality | `trust`, coverage, confidence, interpolation | Upstream data reliability |
| Calendar | month encodings | Seasonality |
| Agroclimate | NASA POWER variables and lagged/rolling variants | Environmental context |
| Spatial | neighbor price, gap, ratio | Cross-province price context |

The exact feature list is generated by `src/run_pipeline.py`. Use the CSV header from a run as the authoritative machine-readable schema.

## `outputs/metrics.csv`

| Column | Description |
|---|---|
| `task` | `regression` or `classification` |
| `model` | Model/baseline name |
| `MAE` | Mean absolute error for regression |
| `RMSE` | Root mean squared error |
| `sMAPE_pct` | Symmetric mean absolute percentage error in percent |
| `directional_accuracy` | Fraction of correctly predicted price directions |
| `PR_AUC` | Area under the precision-recall curve for spike detection |
| `ROC_AUC` | Area under the ROC curve |
| `F1` | F1 score at the configured decision threshold |
| `recall` | Recall for the spike class |

## `outputs/test_predictions.csv`

This table includes identifying columns, actual targets, and one prediction column per trained model. It is the principal file for error analysis by province, commodity, and month.

## Missing values

- Missing upstream numeric fields are retained until model preprocessing.
- Numeric model inputs use median imputation fitted on the training period.
- Categorical inputs use the pipeline's categorical preprocessing.
- NASA sentinel values at or below approximately `-900` are converted to missing values.
- The annual NASA monthly key `13` is excluded because it is not a calendar month.
