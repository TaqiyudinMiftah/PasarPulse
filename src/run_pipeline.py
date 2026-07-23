from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

OUT = Path("outputs")
OUT.mkdir(parents=True, exist_ok=True)

WB_API = "https://microdata.worldbank.org/api/tables/data/fcv/wld_2021_rtfp_v02_m"
NASA_API = "https://power.larc.nasa.gov/api/temporal/monthly/point"
WB_FIELDS = [
    "ISO3", "country", "adm1_name", "adm2_name", "mkt_name", "lat", "lon", "geo_id",
    "year", "month", "DATES", "data_coverage", "data_coverage_recent",
    "index_confidence_score", "spatially_interpolated",
    "c_chili", "c_onions", "trust_chili", "trust_onions",
    "inflation_chili", "inflation_onions",
]
WEATHER_PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN"]

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "PasarPulse-research-pilot/1.0"})


def get_json(url: str, params: dict[str, Any] | None = None, attempts: int = 5, timeout: int = 90) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = SESSION.get(url, params=params, timeout=timeout)
            if response.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Request failed after {attempts} attempts: {url} params={params}") from last_error


def wb_page(offset: int, limit: int = 1000, fields: list[str] | None = None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if fields:
        params["fields"] = ",".join(fields)
    if extra:
        params.update(extra)
    return get_json(WB_API, params=params)


def try_filtered_world_bank() -> pd.DataFrame | None:
    # The data explorer documents a filter option but deployments have used different syntaxes.
    # Try several server-side variants and validate that every returned row is Indonesia.
    candidates = [
        {"ISO3": "IDN"},
        {"filter": "ISO3:IDN"},
        {"filter": "ISO3=IDN"},
        {"filter": 'ISO3="IDN"'},
    ]
    for candidate in candidates:
        try:
            probe = wb_page(0, limit=10, fields=WB_FIELDS, extra=candidate)
            data = probe.get("data", [])
            found = int(probe.get("found", probe.get("total", 0)) or 0)
            if data and found and found < 100_000 and all(str(row.get("ISO3", "")).upper() == "IDN" for row in data):
                rows: list[dict[str, Any]] = []
                for offset in range(0, found, 1000):
                    page = wb_page(offset, limit=1000, fields=WB_FIELDS, extra=candidate)
                    rows.extend(page.get("data", []))
                frame = pd.DataFrame(rows)
                if not frame.empty and (frame["ISO3"].astype(str).str.upper() == "IDN").all():
                    return frame
        except Exception:
            continue
    return None


def download_world_bank_indonesia() -> pd.DataFrame:
    cached = OUT / "IDN_RTFP_selected.csv"
    if cached.exists() and cached.stat().st_size > 1000:
        return pd.read_csv(cached)

    filtered = try_filtered_world_bank()
    if filtered is not None:
        filtered.to_csv(cached, index=False)
        return filtered

    # Robust fallback: the global table is ordered by ISO3. Locate the Indonesia block
    # with binary search, then download only that contiguous range.
    first = wb_page(0, limit=1, fields=["ISO3"])
    total = int(first.get("total", first.get("found", 0)))
    if total <= 0:
        raise RuntimeError("World Bank API returned no rows")

    iso_cache: dict[int, str] = {}

    def iso_at(index: int) -> str:
        if index not in iso_cache:
            payload = wb_page(index, limit=1, fields=["ISO3"])
            data = payload.get("data", [])
            if not data:
                raise RuntimeError(f"No row at World Bank offset {index}")
            iso_cache[index] = str(data[0].get("ISO3", "")).upper()
        return iso_cache[index]

    def lower_bound(target: str, inclusive_upper: bool = False) -> int:
        lo, hi = 0, total
        while lo < hi:
            mid = (lo + hi) // 2
            current = iso_at(mid)
            move_right = current <= target if inclusive_upper else current < target
            if move_right:
                lo = mid + 1
            else:
                hi = mid
        return lo

    start = lower_bound("IDN", inclusive_upper=False)
    end = lower_bound("IDN", inclusive_upper=True)
    if start >= end or iso_at(start) != "IDN":
        raise RuntimeError("Could not locate Indonesia rows in the World Bank global table")

    rows: list[dict[str, Any]] = []
    for offset in range(start, end, 1000):
        limit = min(1000, end - offset)
        page = wb_page(offset, limit=limit, fields=WB_FIELDS)
        batch = [row for row in page.get("data", []) if str(row.get("ISO3", "")).upper() == "IDN"]
        rows.extend(batch)
        print(f"World Bank rows: {len(rows):,}/{end-start:,}")

    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("Downloaded Indonesia block is empty")
    frame.to_csv(cached, index=False)
    return frame


def make_price_panel(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = raw.copy()
    frame["date"] = pd.to_datetime(frame["DATES"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    for col in [
        "lat", "lon", "data_coverage", "data_coverage_recent", "index_confidence_score",
        "spatially_interpolated", "c_chili", "c_onions", "trust_chili", "trust_onions",
    ]:
        frame[col] = pd.to_numeric(frame.get(col), errors="coerce")
    frame["adm1_name"] = frame["adm1_name"].astype(str).str.strip().str.upper()
    frame = frame[(frame["ISO3"].astype(str).str.upper() == "IDN") & frame["date"].notna()]
    frame = frame[~frame["adm1_name"].isin(["", "NAN", "MARKET AVERAGE"])]

    pieces = []
    for commodity, price_col, trust_col in [
        ("CHILI_RED", "c_chili", "trust_chili"),
        ("SHALLOT", "c_onions", "trust_onions"),
    ]:
        part = frame[[
            "date", "adm1_name", "mkt_name", "geo_id", "lat", "lon", price_col, trust_col,
            "data_coverage", "data_coverage_recent", "index_confidence_score", "spatially_interpolated",
        ]].copy()
        part = part.rename(columns={price_col: "price", trust_col: "trust"})
        part["commodity"] = commodity
        part = part[(part["price"] > 0) & part["price"].notna()]
        pieces.append(part)

    long = pd.concat(pieces, ignore_index=True)
    long.to_csv(OUT / "IDN_RTFP_market_long.csv", index=False)

    panel = (
        long.groupby(["date", "adm1_name", "commodity"], as_index=False)
        .agg(
            price=("price", "median"),
            trust=("trust", "median"),
            market_count=("geo_id", "nunique"),
            lat=("lat", "median"),
            lon=("lon", "median"),
            data_coverage=("data_coverage", "median"),
            data_coverage_recent=("data_coverage_recent", "median"),
            index_confidence_score=("index_confidence_score", "median"),
            spatially_interpolated=("spatially_interpolated", "mean"),
        )
        .sort_values(["adm1_name", "commodity", "date"])
    )
    centroids = (
        long.groupby("adm1_name", as_index=False)
        .agg(lat=("lat", "median"), lon=("lon", "median"), market_locations=("geo_id", "nunique"))
        .dropna(subset=["lat", "lon"])
    )
    return panel, centroids


def download_nasa_weather(centroids: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    cached = OUT / "NASA_POWER_monthly_province.csv"
    if cached.exists() and cached.stat().st_size > 1000:
        return pd.read_csv(cached, parse_dates=["date"])

    rows: list[dict[str, Any]] = []
    for idx, rec in centroids.reset_index(drop=True).iterrows():
        params = {
            "parameters": ",".join(WEATHER_PARAMS),
            "community": "AG",
            "longitude": round(float(rec["lon"]), 4),
            "latitude": round(float(rec["lat"]), 4),
            "start": start_year,
            "end": end_year,
            "format": "JSON",
        }
        try:
            payload = get_json(NASA_API, params=params, attempts=6, timeout=120)
            values = payload.get("properties", {}).get("parameter", {})
            keys: set[str] = set()
            for param_values in values.values():
                keys.update(str(k) for k in param_values.keys() if len(str(k)) == 6 and str(k).isdigit() and 1 <= int(str(k)[4:]) <= 12)
            for key in sorted(keys):
                row: dict[str, Any] = {
                    "adm1_name": rec["adm1_name"],
                    "date": pd.Timestamp(year=int(key[:4]), month=int(key[4:]), day=1),
                    "weather_lat": float(rec["lat"]),
                    "weather_lon": float(rec["lon"]),
                }
                for parameter in WEATHER_PARAMS:
                    value = values.get(parameter, {}).get(key, np.nan)
                    try:
                        value = float(value)
                    except (TypeError, ValueError):
                        value = np.nan
                    if value <= -900:
                        value = np.nan
                    row[parameter] = value
                rows.append(row)
            print(f"NASA POWER: {idx+1}/{len(centroids)} provinces")
            time.sleep(0.35)
        except Exception as exc:  # noqa: BLE001
            print(f"WARNING: NASA POWER failed for {rec['adm1_name']}: {exc}")

    weather = pd.DataFrame(rows)
    if weather.empty:
        raise RuntimeError("No NASA POWER weather data could be downloaded")
    weather.to_csv(cached, index=False)
    return weather


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def add_spatial_graph_features(panel: pd.DataFrame, centroids: pd.DataFrame, k: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    coords = centroids.set_index("adm1_name")[["lat", "lon"]].to_dict("index")
    neighbor_rows = []
    neighbor_map: dict[str, list[tuple[str, float]]] = {}
    for province, coord in coords.items():
        distances = []
        for other, other_coord in coords.items():
            if other == province:
                continue
            distance = haversine(coord["lat"], coord["lon"], other_coord["lat"], other_coord["lon"])
            distances.append((other, distance))
        nearest = sorted(distances, key=lambda item: item[1])[:k]
        neighbor_map[province] = nearest
        for rank, (other, distance) in enumerate(nearest, start=1):
            neighbor_rows.append({"adm1_name": province, "neighbor": other, "rank": rank, "distance_km": distance})
    graph = pd.DataFrame(neighbor_rows)
    graph.to_csv(OUT / "province_knn_graph.csv", index=False)

    result = panel.copy()
    lookup = result.set_index(["date", "commodity", "adm1_name"])["price"].to_dict()

    def neighbor_mean(row: pd.Series) -> float:
        vals, weights = [], []
        for neighbor, distance in neighbor_map.get(row["adm1_name"], []):
            value = lookup.get((row["date"], row["commodity"], neighbor))
            if value is not None and pd.notna(value):
                vals.append(float(value))
                weights.append(1.0 / max(distance, 1.0))
        return float(np.average(vals, weights=weights)) if vals else np.nan

    result["neighbor_price"] = result.apply(neighbor_mean, axis=1)
    result["neighbor_price_ratio"] = result["neighbor_price"] / result["price"]
    return result, graph


def build_master(panel: pd.DataFrame, weather: pd.DataFrame, centroids: pd.DataFrame) -> pd.DataFrame:
    panel, _ = add_spatial_graph_features(panel, centroids)
    weather = weather.copy()
    weather["date"] = pd.to_datetime(weather["date"]).dt.to_period("M").dt.to_timestamp()
    master = panel.merge(weather, on=["adm1_name", "date"], how="left")
    master = master.sort_values(["adm1_name", "commodity", "date"]).reset_index(drop=True)

    group = master.groupby(["adm1_name", "commodity"], group_keys=False)
    for lag in [1, 2, 3, 6, 12]:
        master[f"price_lag_{lag}"] = group["price"].shift(lag)
    for window in [3, 6, 12]:
        master[f"price_roll_mean_{window}"] = group["price"].transform(lambda s: s.shift(1).rolling(window, min_periods=max(2, window // 2)).mean())
        master[f"price_roll_std_{window}"] = group["price"].transform(lambda s: s.shift(1).rolling(window, min_periods=max(2, window // 2)).std())
    master["price_return_1"] = master["price"] / master["price_lag_1"] - 1
    master["neighbor_gap"] = master["neighbor_price"] / master["price"] - 1

    for parameter in WEATHER_PARAMS:
        if parameter in master.columns:
            province_group = master.groupby("adm1_name", group_keys=False)
            master[f"{parameter}_lag_1"] = province_group[parameter].shift(1)
            master[f"{parameter}_anom_12"] = master[parameter] - province_group[parameter].transform(
                lambda s: s.shift(1).rolling(12, min_periods=6).mean()
            )
    master["weather_missing_count"] = master[WEATHER_PARAMS].isna().sum(axis=1)
    master["month_sin"] = np.sin(2 * np.pi * master["date"].dt.month / 12)
    master["month_cos"] = np.cos(2 * np.pi * master["date"].dt.month / 12)
    master["year"] = master["date"].dt.year
    master["target_price"] = group["price"].shift(-1)
    master["target_date"] = master["date"] + pd.offsets.MonthBegin(1)
    master["target_spike_10pct"] = (master["target_price"] / master["price"] - 1 >= 0.10).astype(float)
    master.loc[master["target_price"].isna(), "target_spike_10pct"] = np.nan
    master.to_csv(OUT / "master_modeling_table.csv", index=False)
    return master


def smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denominator = np.abs(y_true) + np.abs(y_pred)
    return float(np.mean(200 * np.abs(y_pred - y_true) / np.maximum(denominator, 1e-9)))


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray, current: np.ndarray) -> dict[str, float]:
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "sMAPE_pct": smape(y_true, y_pred),
        "directional_accuracy": float(np.mean(np.sign(y_pred - current) == np.sign(y_true - current))),
    }


def make_regression_pipeline(numeric_features: list[str], categorical_features: list[str]) -> Pipeline:
    preprocess = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median", add_indicator=True), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
        ],
        remainder="drop",
    )
    model = HistGradientBoostingRegressor(
        learning_rate=0.05,
        max_iter=350,
        max_leaf_nodes=31,
        min_samples_leaf=25,
        l2_regularization=1.0,
        random_state=42,
    )
    return Pipeline([("preprocess", preprocess), ("model", model)])


def make_classifier_pipeline(numeric_features: list[str], categorical_features: list[str]) -> Pipeline:
    preprocess = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median", add_indicator=True), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
        ],
        remainder="drop",
    )
    model = HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=300,
        max_leaf_nodes=31,
        min_samples_leaf=25,
        l2_regularization=1.0,
        class_weight="balanced",
        random_state=42,
    )
    return Pipeline([("preprocess", preprocess), ("model", model)])


def train_and_evaluate(master: pd.DataFrame, weather: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    data = master[master["target_price"].notna() & (master["price"] > 0)].copy()
    weather_max = pd.to_datetime(weather["date"]).max()
    data = data[data["date"] <= weather_max].copy()
    if data.empty:
        raise RuntimeError("No rows remain after aligning price and weather dates")

    max_date = data["date"].max()
    test_start = max_date - pd.DateOffset(months=23)
    if (data["date"] < test_start).sum() < 1000:
        test_start = max_date - pd.DateOffset(months=11)
    train = data[data["date"] < test_start].copy()
    test = data[data["date"] >= test_start].copy()
    if len(train) < 500 or len(test) < 100:
        raise RuntimeError(f"Insufficient split: train={len(train)}, test={len(test)}")

    categorical = ["adm1_name", "commodity"]
    core_price = [
        "price", "price_lag_1", "price_lag_2", "price_lag_3", "price_lag_6", "price_lag_12",
        "price_roll_mean_3", "price_roll_mean_6", "price_roll_mean_12",
        "price_roll_std_3", "price_roll_std_6", "price_roll_std_12", "price_return_1",
        "trust", "market_count", "data_coverage", "data_coverage_recent", "index_confidence_score",
        "spatially_interpolated", "month_sin", "month_cos", "year",
    ]
    weather_features = []
    for parameter in WEATHER_PARAMS:
        weather_features.extend([parameter, f"{parameter}_lag_1", f"{parameter}_anom_12"])
    weather_features.append("weather_missing_count")
    spatial_features = ["lat", "lon", "neighbor_price", "neighbor_price_ratio", "neighbor_gap"]

    model_specs = {
        "ML_price_only": core_price,
        "ML_price_weather": core_price + weather_features,
        "ML_price_weather_spatial": core_price + weather_features + spatial_features,
    }

    predictions = test[["date", "target_date", "adm1_name", "commodity", "price", "target_price"]].copy()
    predictions["naive_last"] = test["price"].to_numpy()
    predictions["seasonal_naive"] = test["price_lag_12"].fillna(test["price"]).to_numpy()

    metrics_rows: list[dict[str, Any]] = []
    y_true = test["target_price"].to_numpy(float)
    current = test["price"].to_numpy(float)
    for baseline in ["naive_last", "seasonal_naive"]:
        met = regression_metrics(y_true, predictions[baseline].to_numpy(float), current)
        metrics_rows.append({"task": "regression", "model": baseline, **met})

    fitted_models: dict[str, Pipeline] = {}
    for name, numeric in model_specs.items():
        pipeline = make_regression_pipeline(numeric, categorical)
        pipeline.fit(train[numeric + categorical], np.log1p(train["target_price"].to_numpy(float)))
        pred = np.expm1(pipeline.predict(test[numeric + categorical]))
        pred = np.maximum(pred, 0)
        predictions[name] = pred
        met = regression_metrics(y_true, pred, current)
        metrics_rows.append({"task": "regression", "model": name, **met})
        fitted_models[name] = pipeline
        joblib.dump(pipeline, OUT / f"{name}.joblib")

    # Spike classification: compare price-only against the full multimodal feature set.
    classifier_specs = {
        "spike_price_only": core_price,
        "spike_multimodal": core_price + weather_features + spatial_features,
    }
    y_train_cls = train["target_spike_10pct"].astype(int)
    y_test_cls = test["target_spike_10pct"].astype(int)
    classification_summary: dict[str, Any] = {
        "train_positive_rate": float(y_train_cls.mean()),
        "test_positive_rate": float(y_test_cls.mean()),
    }
    if y_train_cls.nunique() == 2 and y_test_cls.nunique() == 2 and y_train_cls.sum() >= 20:
        for name, numeric in classifier_specs.items():
            pipeline = make_classifier_pipeline(numeric, categorical)
            pipeline.fit(train[numeric + categorical], y_train_cls)
            probability = pipeline.predict_proba(test[numeric + categorical])[:, 1]
            label = (probability >= 0.5).astype(int)
            predictions[f"{name}_prob"] = probability
            row = {
                "task": "classification",
                "model": name,
                "PR_AUC": float(average_precision_score(y_test_cls, probability)),
                "ROC_AUC": float(roc_auc_score(y_test_cls, probability)),
                "F1": float(f1_score(y_test_cls, label, zero_division=0)),
                "recall": float(recall_score(y_test_cls, label, zero_division=0)),
            }
            metrics_rows.append(row)
            joblib.dump(pipeline, OUT / f"{name}.joblib")

    metrics = pd.DataFrame(metrics_rows)
    metrics.to_csv(OUT / "metrics.csv", index=False)
    predictions.to_csv(OUT / "test_predictions.csv", index=False)

    split_info = {
        "train_start": str(train["date"].min().date()),
        "train_end": str(train["date"].max().date()),
        "test_start": str(test["date"].min().date()),
        "test_end": str(test["date"].max().date()),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "province_count": int(data["adm1_name"].nunique()),
        "commodities": sorted(data["commodity"].unique().tolist()),
        "classification": classification_summary,
    }
    return metrics, predictions, split_info


def make_plots(metrics: pd.DataFrame, predictions: pd.DataFrame) -> None:
    reg = metrics[metrics["task"] == "regression"].copy()
    plt.figure(figsize=(10, 5.5))
    plt.bar(reg["model"], reg["sMAPE_pct"])
    plt.ylabel("Test sMAPE (%) — lower is better")
    plt.xticks(rotation=20, ha="right")
    plt.title("PasarPulse Pilot: Model Comparison")
    plt.tight_layout()
    plt.savefig(OUT / "model_comparison.png", dpi=180)
    plt.close()

    monthly = (
        predictions.groupby("target_date", as_index=False)
        .agg(actual=("target_price", "median"), proposed=("ML_price_weather_spatial", "median"), naive=("naive_last", "median"))
    )
    plt.figure(figsize=(10, 5.5))
    plt.plot(monthly["target_date"], monthly["actual"], label="Actual")
    plt.plot(monthly["target_date"], monthly["proposed"], label="Multimodal")
    plt.plot(monthly["target_date"], monthly["naive"], label="Naive", alpha=0.75)
    plt.ylabel("Median price (IDR/kg, across province–commodity nodes)")
    plt.title("Out-of-Time Test: Actual vs Predicted")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / "forecast_plot.png", dpi=180)
    plt.close()


def write_report(raw: pd.DataFrame, panel: pd.DataFrame, weather: pd.DataFrame, master: pd.DataFrame, metrics: pd.DataFrame, split_info: dict[str, Any]) -> None:
    quality = {
        "world_bank_rows_downloaded": int(len(raw)),
        "market_count": int(raw["geo_id"].nunique()) if "geo_id" in raw else None,
        "province_count": int(panel["adm1_name"].nunique()),
        "price_date_min": str(panel["date"].min().date()),
        "price_date_max": str(panel["date"].max().date()),
        "weather_rows": int(len(weather)),
        "weather_date_min": str(pd.to_datetime(weather["date"]).min().date()),
        "weather_date_max": str(pd.to_datetime(weather["date"]).max().date()),
        "master_rows": int(len(master)),
        "weather_missing_fraction": float(master[WEATHER_PARAMS].isna().mean().mean()),
        "split": split_info,
    }
    (OUT / "data_quality.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")

    reg = metrics[metrics["task"] == "regression"].sort_values("sMAPE_pct")
    best = reg.iloc[0].to_dict() if not reg.empty else {}
    report = f"""# PasarPulse Multimodal Pilot — Actual Run

## Scope

This run uses three train-compatible modalities at a common **province × commodity × month** key:

1. World Bank Real-Time Food Prices: chili and shallot market-price estimates.
2. NASA POWER monthly agroclimate variables at province market-centroid coordinates.
3. A spatial k-nearest-province graph derived from georeferenced markets.

The experiment forecasts the next month's provincial median price and classifies a >=10% next-month price spike.

## Data

- World Bank selected raw rows: {quality['world_bank_rows_downloaded']:,}
- Provinces in model: {quality['province_count']}
- Price period: {quality['price_date_min']} to {quality['price_date_max']}
- Weather period: {quality['weather_date_min']} to {quality['weather_date_max']}
- Master rows: {quality['master_rows']:,}
- Mean missing fraction across raw weather fields after join: {quality['weather_missing_fraction']:.3f}

The World Bank RTFP series combines observed survey records with machine-learning estimates of missing prices. Trust and coverage fields are retained as model inputs; results must not be described as forecasts trained only on directly observed prices.

## Out-of-time split

- Train: {split_info['train_start']} to {split_info['train_end']} ({split_info['train_rows']:,} rows)
- Test: {split_info['test_start']} to {split_info['test_end']} ({split_info['test_rows']:,} rows)

## Best regression result

- Model: {best.get('model')}
- MAE: {best.get('MAE', float('nan')):,.2f}
- RMSE: {best.get('RMSE', float('nan')):,.2f}
- sMAPE: {best.get('sMAPE_pct', float('nan')):.2f}%
- Directional accuracy: {best.get('directional_accuracy', float('nan')):.3f}

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
"""
    (OUT / "RUN_REPORT.md").write_text(report, encoding="utf-8")


def main() -> None:
    print("1/6 Downloading World Bank RTFP data")
    raw = download_world_bank_indonesia()
    print(f"Downloaded {len(raw):,} selected Indonesia rows")

    print("2/6 Creating province–commodity price panel")
    panel, centroids = make_price_panel(raw)
    panel.to_csv(OUT / "province_commodity_price_panel.csv", index=False)
    centroids.to_csv(OUT / "province_market_centroids.csv", index=False)

    print("3/6 Downloading NASA POWER monthly weather")
    start_year = int(panel["date"].dt.year.min())
    # NASA POWER monthly meteorological products are stable through the previous year.
    end_year = min(2025, int(panel["date"].dt.year.max()))
    weather = download_nasa_weather(centroids, start_year=start_year, end_year=end_year)

    print("4/6 Building aligned multimodal table")
    master = build_master(panel, weather, centroids)

    print("5/6 Training and evaluating models")
    metrics, predictions, split_info = train_and_evaluate(master, weather)
    make_plots(metrics, predictions)

    print("6/6 Writing report")
    write_report(raw, panel, weather, master, metrics, split_info)
    print(metrics.to_string(index=False))


if __name__ == "__main__":
    main()
