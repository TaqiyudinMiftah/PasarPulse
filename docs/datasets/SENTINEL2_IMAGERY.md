# Sentinel-2 L2A Image Dataset

## Status

This dataset adds a **real image modality** to PasarPulse. Unlike the price and weather tables, the main input is a four-channel raster tensor that can be consumed by a CNN or Vision Transformer.

## Repository paths

```text
data/satellite/metadata.csv
data/satellite/manifest.json
data/satellite/chips/sentinel2_quarterly_2022.npz
data/satellite/chips/sentinel2_quarterly_2023.npz
data/satellite/chips/sentinel2_quarterly_2024.npz
data/satellite/chips/sentinel2_quarterly_2025.npz
reports/figures/satellite_previews/*.png
```

The compressed bundle is stored at:

```text
artifacts/PasarPulse_Sentinel2_Quarterly_Chips.zip
```

## Upstream source

- Collection: `sentinel-2-l2a`
- Catalogue: Microsoft Planetary Computer STAC API
- Product: Copernicus Sentinel-2 Level-2A bottom-of-atmosphere surface reflectance
- Query geometry: point at each PasarPulse province market centroid
- Query period: 2022-01-01 through 2025-12-31

The Planetary Computer catalogue is used as a cloud-native access layer. The underlying imagery is Copernicus Sentinel-2 L2A.

## Sampling design

### Spatial anchor

Each province uses the median market coordinate already present in:

```text
data/interim/province_market_centroids.csv
```

The image therefore represents the landscape around a province's observed market centre. It is **not** guaranteed to be located on a shallot or chili production field.

### Temporal sampling

One image is selected per province per calendar quarter:

```text
Q1: January-March
Q2: April-June
Q3: July-September
Q4: October-December
```

Within each quarter, the pipeline selects the scene with the lowest STAC `eo:cloud_cover`. Ties are resolved by acquisition time closest to the quarter midpoint.

### Spatial extent and resolution

Each sample covers approximately:

```text
6.4 km x 6.4 km
```

The output is resampled to:

```text
64 x 64 pixels
```

The effective output grid is therefore approximately 100 metres per pixel. This is a deliberate downsampling choice to keep the research dataset small enough for version control and rapid prototyping. It does not preserve the native 10-metre detail.

## Image tensor

Each sample contains:

```text
images[sample, channel, y, x]
```

with shape:

```text
N x 4 x 64 x 64
```

The channel order is fixed:

| Channel | Sentinel-2 asset | Meaning |
|---:|---|---|
| 0 | `B02` | Blue reflectance |
| 1 | `B03` | Green reflectance |
| 2 | `B04` | Red reflectance |
| 3 | `B08` | Near-infrared reflectance |

The arrays are stored as `uint16`, retaining the source reflectance integer representation returned by the L2A COG assets. No global normalization is applied in the stored dataset.

## Valid-pixel mask

Each shard also contains:

```text
valid_masks[sample, y, x]
```

with shape:

```text
N x 64 x 64
```

The mask is derived from the Sentinel-2 Scene Classification Layer (`SCL`). The following SCL codes are excluded:

```text
0  no data
1  saturated or defective
3  cloud shadow
8  medium-probability cloud
9  high-probability cloud
10 thin cirrus
11 snow or ice
```

A pixel is also marked invalid when any of the four reflectance channels is zero.

Invalid reflectance pixels are written as zero. Models must still use `valid_masks`; zero alone is not a sufficient validity indicator after normalization.

## NPZ shard schema

Each annual `.npz` file contains:

| Array | Dtype | Shape | Description |
|---|---|---|---|
| `images` | `uint16` | `N x 4 x 64 x 64` | Four-band image tensors |
| `valid_masks` | `uint8` | `N x 64 x 64` | Valid-pixel masks |
| `sample_ids` | Unicode | `N` | Stable IDs matching `metadata.csv` |

Example loader:

```python
import numpy as np

shard = np.load("data/satellite/chips/sentinel2_quarterly_2024.npz")
images = shard["images"]
masks = shard["valid_masks"]
sample_ids = shard["sample_ids"]

image = images[0].astype("float32") / 10000.0
mask = masks[0].astype(bool)
```

The divisor `10000` is a common Sentinel-2 reflectance scaling convention, but users must verify value ranges and clipping in their own training pipeline rather than assuming every pixel lies in `[0, 10000]`.

## Metadata schema

`data/satellite/metadata.csv` contains one row per image sample.

| Column | Type | Description |
|---|---|---|
| `sample_id` | string | Stable province-year-quarter identifier |
| `adm1_name` | string | Province key matching PasarPulse tables |
| `reference_date` | date | First day of the represented quarter |
| `quarter` | integer | Calendar quarter 1-4 |
| `acquisition_datetime` | timestamp | Actual Sentinel-2 acquisition time |
| `stac_item_id` | string | Source STAC item identifier |
| `scene_cloud_cover` | float | Scene-level cloud percentage from STAC metadata |
| `center_lat` | float | Market-centroid latitude |
| `center_lon` | float | Market-centroid longitude |
| `patch_meters` | float | Requested patch width and height in metres |
| `patch_pixels` | integer | Output width and height in pixels |
| `valid_fraction` | float | Fraction of pixels surviving the local SCL mask |
| `ndvi_mean` | float | Mean NDVI over valid pixels |
| `ndvi_std` | float | NDVI standard deviation over valid pixels |
| `shard_file` | string | Relative NPZ shard path |
| `array_index` | integer | Row index inside the shard arrays |
| `source_collection` | string | STAC collection name |
| `source_platform` | string | Access platform used by the pipeline |

## Join with the monthly price table

The image sample is quarterly while PasarPulse prices are monthly. The safe join is a backward as-of join:

```text
satellite.reference_date <= price.date
```

For every monthly price row, use the most recent available satellite sample from the same province. Add:

```text
satellite_age_months
```

so the model knows how old the image is.

Do not join a Q2 image to an April prediction if the selected Sentinel acquisition occurred after the April forecast cutoff. A production implementation should use `acquisition_datetime`, not merely `reference_date`, and enforce an as-of timestamp based on the prediction run time.

## Image-model usage

A genuine multimodal architecture can use separate encoders:

```text
price sequence -> temporal encoder
Sentinel-2 tensor -> CNN or ViT
weather table -> tabular encoder
province graph -> GNN
                -> gated fusion -> price-shock probability
```

The image encoder should receive both the reflectance tensor and the valid mask. Recommended augmentations are modest spatial flips and rotations; aggressive colour augmentation is inappropriate for calibrated reflectance.

## Quality filters

Recommended minimum filters before model training:

```text
valid_fraction >= 0.50
scene_cloud_cover <= 70
all four bands present
sample_id unique
array_index valid inside shard
```

The local `valid_fraction` is more informative than scene-level cloud cover because a globally cloudy tile may still have a clear local patch, and vice versa.

## Limitations

1. The patch is centred on a market centroid, not a verified crop field.
2. The image is not commodity-specific; the same province image may be joined to chili and shallot rows.
3. Quarterly sampling can miss short-lived crop stress or flood events.
4. A single least-cloudy scene is not equivalent to a cloud-free temporal composite.
5. Resampling to 64 x 64 sacrifices native spatial detail.
6. Cloud-mask errors and haze remain possible.
7. Satellite imagery supports association and early warning; it does not establish a causal effect on price.

The correct claim is:

> PasarPulse includes a four-band Sentinel-2 image modality representing quarterly regional landscape context around observed market centres.

The incorrect claim is:

> The images directly observe shallot and chili fields for every province.

## Rebuild

```bash
python -m pip install -r requirements-satellite.txt
python src/download_sentinel2_chips.py
```

Environment variables can override the default scope:

```text
SAT_START_YEAR
SAT_END_YEAR
SAT_PATCH_PIXELS
SAT_PATCH_METERS
SAT_MAX_SCENE_CLOUD
SAT_MAX_BAND_WORKERS
```
