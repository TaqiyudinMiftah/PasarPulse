# Data Provenance, Attribution, and Redistribution Notes

PasarPulse combines data from independent upstream providers. The repository's code and documentation do not replace upstream terms. Users are responsible for checking the latest terms before redistribution or publication.

## World Bank Real-Time Food Prices

**Dataset**: *Monthly food price estimates by product and market*  
**Reference ID**: `IDN_2021_RTFP_v02_M`  
**DOI**: `10.48529/2ZH0-JF55`  
**Provider**: World Bank Microdata Library

The study description states that the price-estimate dataset is published as open data and is based on publicly available data. It is a live dataset and historical values may be revised when additional information becomes available.

Recommended citation:

> Andrée, B. P. J. (2021). Monthly food price estimates by product and market. IDN_2021_RTFP_v02_M. Washington, DC: World Bank Microdata Library. https://doi.org/10.48529/2ZH0-JF55

Important source characteristics:

- RTFP combines direct price measurement with machine-learning estimation of missing observations.
- The PasarPulse copy is a derived subset focused on Indonesia, chili, and shallot.
- Source reliability, coverage, confidence, and interpolation fields are retained.
- Users should not present the derived table as a fully observed government transaction-price series.

Official catalogue:

- `https://microdata.worldbank.org/catalog/6166`

## NASA POWER

**Dataset/service**: NASA Prediction Of Worldwide Energy Resources, Monthly Point API  
**Provider**: NASA Langley Research Center POWER Project

NASA POWER requests that publications include both the POWER acknowledgement and a data reference identifying the service, version, and access date.

Recommended acknowledgement:

> The data was obtained from the NASA Langley Research Center Prediction Of Worldwide Energy Resources (POWER) Project funded through the NASA Earth Science Division.

For a publication, add the exact service/version and the retrieval date from the run metadata.

Official documentation:

- `https://power.larc.nasa.gov/docs/referencing/`
- `https://power.larc.nasa.gov/docs/services/api/temporal/monthly/`

## Copernicus Sentinel-2 Level-2A

**Dataset**: Copernicus Sentinel-2 Level-2A bottom-of-atmosphere surface reflectance  
**Provider**: European Union Copernicus Programme / ESA Sentinel mission  
**Access layer used by PasarPulse**: Microsoft Planetary Computer STAC API  
**STAC collection**: `sentinel-2-l2a`

Copernicus Sentinel data are available on a free, full, and open basis subject to the Legal Notice on the use of Copernicus Sentinel Data and Service Information. PasarPulse creates modified and spatially cropped products rather than redistributing full original scenes.

Required downstream attribution should include a statement equivalent to:

> Contains modified Copernicus Sentinel data [year or acquisition-year range].

For this snapshot, an appropriate repository-level statement is:

> Contains modified Copernicus Sentinel data 2022–2025, accessed through the Microsoft Planetary Computer.

Important source characteristics:

- source pixels are Sentinel-2 L2A surface reflectance;
- PasarPulse selects one scene per province per quarter;
- images are spatially cropped and downsampled;
- cloud and invalid pixels are masked using the Sentinel-2 Scene Classification Layer;
- patches are anchored to market centroids and are not verified commodity fields.

Official terms and documentation:

- `https://dataspace.copernicus.eu/terms-and-conditions`
- `https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice`
- `https://planetarycomputer.microsoft.com/docs/quickstarts/reading-stac/`

The Planetary Computer is an access and processing platform. The scientific provenance of the image pixels remains Copernicus Sentinel-2.

## Derived PasarPulse files

The following files are derived transformations rather than original source products:

- province-level median price panel;
- province market centroids;
- k-nearest-province graph;
- aligned master modeling table;
- quarterly Sentinel-2 four-band image chips and local valid-pixel masks;
- fitted models;
- predictions, metrics, plots, and reports.

Derivations performed by PasarPulse include filtering, reshaping, aggregation, temporal feature construction, distance calculation, weather joining, satellite scene selection, spatial cropping, raster resampling, SCL masking, imputation inside training pipelines, and model fitting.

## Repository code and documentation

Unless a separate repository license is added by the repository owner, no additional software license is implied. Upstream dataset terms remain applicable to copied or derived data.

## Recommended redistribution practice

When distributing generated bundles:

1. Keep this provenance file and `DATASET_CARD.md` with the data.
2. Preserve source identifiers, STAC item IDs, acquisition timestamps, and citations.
3. Record upstream access dates and source versions in manifests or run reports.
4. Do not remove World Bank trust, coverage, or interpolation metadata when making scientific claims.
5. Avoid claiming that World Bank estimates are official Indonesian price statistics.
6. State that NASA POWER values are sampled at province market-centroid coordinates.
7. Include the Copernicus Sentinel attribution notice when sharing satellite chips or derived previews.
8. Do not describe the satellite patches as verified chili or shallot fields.

## Reproducibility preference

The preferred distribution method is to share the pipelines and allow users to rebuild recent source snapshots. The repository also commits generated research snapshots for competition reproducibility and inspection; these snapshots can become stale relative to live upstream services.
