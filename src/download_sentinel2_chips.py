from __future__ import annotations

import calendar
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import planetary_computer
import rasterio
from PIL import Image
from pystac import Item
from pystac_client import Client
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
from rasterio.warp import transform

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "sentinel-2-l2a"
BANDS = ["B02", "B03", "B04", "B08"]
SCL_ASSET = "SCL"
INVALID_SCL = {0, 1, 3, 8, 9, 10, 11}

CENTROIDS_PATH = Path("data/interim/province_market_centroids.csv")
OUT_DIR = Path("data/satellite")
CHIP_DIR = OUT_DIR / "chips"
PREVIEW_DIR = Path("reports/figures/satellite_previews")

START_YEAR = int(os.getenv("SAT_START_YEAR", "2022"))
END_YEAR = int(os.getenv("SAT_END_YEAR", "2025"))
PATCH_PIXELS = int(os.getenv("SAT_PATCH_PIXELS", "64"))
PATCH_METERS = float(os.getenv("SAT_PATCH_METERS", "6400"))
MAX_SCENE_CLOUD = float(os.getenv("SAT_MAX_SCENE_CLOUD", "85"))
MAX_BAND_WORKERS = int(os.getenv("SAT_MAX_BAND_WORKERS", "5"))


@dataclass
class SampleMetadata:
    sample_id: str
    adm1_name: str
    reference_date: str
    quarter: int
    acquisition_datetime: str
    stac_item_id: str
    scene_cloud_cover: float | None
    center_lat: float
    center_lon: float
    patch_meters: float
    patch_pixels: int
    valid_fraction: float
    ndvi_mean: float | None
    ndvi_std: float | None
    shard_file: str
    array_index: int
    source_collection: str = COLLECTION
    source_platform: str = "Microsoft Planetary Computer STAC"


def quarter_bounds(year: int, quarter: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    start_month = 1 + (quarter - 1) * 3
    end_month = start_month + 2
    start = pd.Timestamp(year=year, month=start_month, day=1, tz="UTC")
    end_day = calendar.monthrange(year, end_month)[1]
    end = pd.Timestamp(year=year, month=end_month, day=end_day, hour=23, minute=59, second=59, tz="UTC")
    return start, end


def get_catalog() -> Client:
    return Client.open(STAC_URL, modifier=planetary_computer.sign_inplace)


def search_items_for_province(catalog: Client, lon: float, lat: float) -> list[Item]:
    start = f"{START_YEAR}-01-01T00:00:00Z"
    end = f"{END_YEAR}-12-31T23:59:59Z"
    search = catalog.search(
        collections=[COLLECTION],
        intersects={"type": "Point", "coordinates": [lon, lat]},
        datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": MAX_SCENE_CLOUD}},
    )
    return list(search.items())


def choose_quarterly_items(items: list[Item]) -> dict[tuple[int, int], Item]:
    chosen: dict[tuple[int, int], Item] = {}
    for year in range(START_YEAR, END_YEAR + 1):
        for quarter in range(1, 5):
            q_start, q_end = quarter_bounds(year, quarter)
            midpoint = q_start + (q_end - q_start) / 2
            candidates: list[Item] = []
            for item in items:
                if item.datetime is None:
                    continue
                timestamp = pd.Timestamp(item.datetime)
                if q_start <= timestamp <= q_end:
                    if all(asset in item.assets for asset in BANDS + [SCL_ASSET]):
                        candidates.append(item)
            if not candidates:
                continue

            def ranking(item: Item) -> tuple[float, float]:
                cloud = item.properties.get("eo:cloud_cover")
                cloud_score = float(cloud) if cloud is not None else 999.0
                distance_days = abs((pd.Timestamp(item.datetime) - midpoint).total_seconds()) / 86400.0
                return cloud_score, distance_days

            chosen[(year, quarter)] = min(candidates, key=ranking)
    return chosen


def read_asset_patch(
    href: str,
    lon: float,
    lat: float,
    *,
    resampling: Resampling,
) -> np.ndarray:
    env_options = {
        "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
        "GDAL_HTTP_MULTIRANGE": "YES",
        "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif,.TIF",
    }
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with rasterio.Env(**env_options):
                with rasterio.open(href) as src:
                    xs, ys = transform("EPSG:4326", src.crs, [lon], [lat])
                    half = PATCH_METERS / 2.0
                    window = from_bounds(
                        xs[0] - half,
                        ys[0] - half,
                        xs[0] + half,
                        ys[0] + half,
                        transform=src.transform,
                    ).round_offsets().round_lengths()
                    data = src.read(
                        1,
                        window=window,
                        out_shape=(PATCH_PIXELS, PATCH_PIXELS),
                        boundless=True,
                        fill_value=0,
                        resampling=resampling,
                    )
                    return data
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"Unable to read asset after retries: {href[:120]}") from last_error


def read_item(item: Item, lon: float, lat: float) -> tuple[np.ndarray, np.ndarray]:
    futures: dict[Any, str] = {}
    arrays: dict[str, np.ndarray] = {}
    with ThreadPoolExecutor(max_workers=MAX_BAND_WORKERS) as executor:
        for band in BANDS:
            futures[
                executor.submit(
                    read_asset_patch,
                    item.assets[band].href,
                    lon,
                    lat,
                    resampling=Resampling.bilinear,
                )
            ] = band
        futures[
            executor.submit(
                read_asset_patch,
                item.assets[SCL_ASSET].href,
                lon,
                lat,
                resampling=Resampling.nearest,
            )
        ] = SCL_ASSET

        for future in as_completed(futures):
            arrays[futures[future]] = future.result()

    image = np.stack([arrays[band] for band in BANDS]).astype(np.uint16, copy=False)
    scl = arrays[SCL_ASSET].astype(np.uint8, copy=False)
    valid = np.ones_like(scl, dtype=bool)
    for code in INVALID_SCL:
        valid &= scl != code
    valid &= np.all(image > 0, axis=0)
    image[:, ~valid] = 0
    return image, valid.astype(np.uint8)


def calculate_ndvi(image: np.ndarray, valid_mask: np.ndarray) -> tuple[float | None, float | None]:
    red = image[2].astype(np.float32)
    nir = image[3].astype(np.float32)
    valid = valid_mask.astype(bool) & ((nir + red) > 0)
    if not np.any(valid):
        return None, None
    ndvi = (nir[valid] - red[valid]) / (nir[valid] + red[valid])
    return float(np.mean(ndvi)), float(np.std(ndvi))


def make_rgb_preview(image: np.ndarray, valid_mask: np.ndarray) -> Image.Image:
    rgb = image[[2, 1, 0]].transpose(1, 2, 0).astype(np.float32)
    valid = valid_mask.astype(bool)
    if np.any(valid):
        values = rgb[valid]
        low = np.percentile(values, 2, axis=0)
        high = np.percentile(values, 98, axis=0)
    else:
        low = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        high = np.array([3000.0, 3000.0, 3000.0], dtype=np.float32)
    scaled = (rgb - low) / np.maximum(high - low, 1.0)
    scaled = np.clip(scaled, 0.0, 1.0)
    scaled[~valid] = 0.0
    return Image.fromarray((scaled * 255).astype(np.uint8), mode="RGB").resize((256, 256))


def safe_name(value: str) -> str:
    return "_".join(value.strip().lower().replace("/", " ").split())


def process_province(catalog: Client, province: str, lat: float, lon: float) -> list[dict[str, Any]]:
    print(f"Searching Sentinel-2 items for {province}")
    items = search_items_for_province(catalog, lon, lat)
    selected = choose_quarterly_items(items)
    records: list[dict[str, Any]] = []

    for (year, quarter), item in sorted(selected.items()):
        sample_id = f"{safe_name(province)}_{year}_q{quarter}"
        try:
            image, mask = read_item(item, lon, lat)
        except Exception as exc:  # noqa: BLE001
            print(f"WARNING {sample_id}: {exc}")
            continue

        ndvi_mean, ndvi_std = calculate_ndvi(image, mask)
        records.append(
            {
                "sample_id": sample_id,
                "adm1_name": province,
                "reference_date": f"{year}-{1 + (quarter - 1) * 3:02d}-01",
                "quarter": quarter,
                "acquisition_datetime": pd.Timestamp(item.datetime).isoformat() if item.datetime else "",
                "stac_item_id": item.id,
                "scene_cloud_cover": item.properties.get("eo:cloud_cover"),
                "center_lat": lat,
                "center_lon": lon,
                "patch_meters": PATCH_METERS,
                "patch_pixels": PATCH_PIXELS,
                "valid_fraction": float(mask.mean()),
                "ndvi_mean": ndvi_mean,
                "ndvi_std": ndvi_std,
                "year": year,
                "image": image,
                "mask": mask,
            }
        )

        if year == END_YEAR and quarter == 4:
            PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
            make_rgb_preview(image, mask).save(PREVIEW_DIR / f"{safe_name(province)}.png")
        print(f"  {sample_id}: valid={mask.mean():.3f}, cloud={item.properties.get('eo:cloud_cover')}")

    return records


def write_shards(records: list[dict[str, Any]]) -> pd.DataFrame:
    CHIP_DIR.mkdir(parents=True, exist_ok=True)
    metadata_rows: list[SampleMetadata] = []

    for year in range(START_YEAR, END_YEAR + 1):
        year_records = [row for row in records if row["year"] == year]
        if not year_records:
            continue
        year_records.sort(key=lambda row: row["sample_id"])
        images = np.stack([row["image"] for row in year_records]).astype(np.uint16)
        masks = np.stack([row["mask"] for row in year_records]).astype(np.uint8)
        sample_ids = np.asarray([row["sample_id"] for row in year_records], dtype="U96")
        shard_name = f"sentinel2_quarterly_{year}.npz"
        np.savez_compressed(CHIP_DIR / shard_name, images=images, valid_masks=masks, sample_ids=sample_ids)

        for index, row in enumerate(year_records):
            metadata_rows.append(
                SampleMetadata(
                    sample_id=row["sample_id"],
                    adm1_name=row["adm1_name"],
                    reference_date=row["reference_date"],
                    quarter=int(row["quarter"]),
                    acquisition_datetime=row["acquisition_datetime"],
                    stac_item_id=row["stac_item_id"],
                    scene_cloud_cover=(
                        float(row["scene_cloud_cover"]) if row["scene_cloud_cover"] is not None else None
                    ),
                    center_lat=float(row["center_lat"]),
                    center_lon=float(row["center_lon"]),
                    patch_meters=float(row["patch_meters"]),
                    patch_pixels=int(row["patch_pixels"]),
                    valid_fraction=float(row["valid_fraction"]),
                    ndvi_mean=row["ndvi_mean"],
                    ndvi_std=row["ndvi_std"],
                    shard_file=f"chips/{shard_name}",
                    array_index=index,
                )
            )

    metadata = pd.DataFrame([asdict(row) for row in metadata_rows])
    metadata.to_csv(OUT_DIR / "metadata.csv", index=False)
    return metadata


def write_manifest(metadata: pd.DataFrame) -> None:
    manifest = {
        "collection": COLLECTION,
        "source_stac": STAC_URL,
        "years": [START_YEAR, END_YEAR],
        "temporal_resolution": "quarterly",
        "spatial_anchor": "province market centroid from PasarPulse price data",
        "patch_pixels": PATCH_PIXELS,
        "patch_meters": PATCH_METERS,
        "bands": BANDS,
        "band_order": {str(i): band for i, band in enumerate(BANDS)},
        "cloud_mask_source": SCL_ASSET,
        "invalid_scl_codes": sorted(INVALID_SCL),
        "sample_count": int(len(metadata)),
        "province_count": int(metadata["adm1_name"].nunique()) if not metadata.empty else 0,
        "mean_valid_fraction": float(metadata["valid_fraction"].mean()) if not metadata.empty else None,
        "minimum_valid_fraction": float(metadata["valid_fraction"].min()) if not metadata.empty else None,
        "created_by": "src/download_sentinel2_chips.py",
        "important_caveat": (
            "Patches are centered on market centroids, not verified commodity production fields. "
            "They represent regional visual context and must not be described as crop-specific imagery."
        ),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    if not CENTROIDS_PATH.exists():
        raise FileNotFoundError(f"Missing required centroid table: {CENTROIDS_PATH}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    centroids = pd.read_csv(CENTROIDS_PATH)
    required = {"adm1_name", "lat", "lon"}
    missing = required - set(centroids.columns)
    if missing:
        raise ValueError(f"Centroid table missing columns: {sorted(missing)}")

    catalog = get_catalog()
    records: list[dict[str, Any]] = []
    for row in centroids.sort_values("adm1_name").itertuples(index=False):
        records.extend(process_province(catalog, str(row.adm1_name), float(row.lat), float(row.lon)))

    if not records:
        raise RuntimeError("No Sentinel-2 chips were created")
    metadata = write_shards(records)
    write_manifest(metadata)
    print(f"Created {len(metadata):,} image samples across {metadata['adm1_name'].nunique()} provinces")


if __name__ == "__main__":
    main()
