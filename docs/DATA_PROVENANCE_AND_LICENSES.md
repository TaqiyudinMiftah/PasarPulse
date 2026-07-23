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

## Derived PasarPulse files

The following files are derived transformations rather than original source products:

- province-level median price panel;
- province market centroids;
- k-nearest-province graph;
- aligned master modeling table;
- fitted models;
- predictions, metrics, plots, and reports.

Derivations performed by PasarPulse include filtering, reshaping, aggregation, temporal feature construction, distance calculation, weather joining, imputation inside training pipelines, and model fitting.

## Repository code and documentation

Unless a separate repository license is added by the repository owner, no additional software license is implied. Upstream dataset terms remain applicable to copied or derived data.

## Recommended redistribution practice

When distributing the generated bundle:

1. Keep this provenance file and `DATASET_CARD.md` with the data.
2. Preserve source identifiers and citations.
3. Record the upstream access date and source version in `data_quality.json` or the run report.
4. Do not remove trust, coverage, or interpolation metadata when making scientific claims.
5. Avoid claiming that World Bank estimates are official Indonesian price statistics.
6. State that NASA POWER values are sampled at province market-centroid coordinates.

## Reproducibility preference

The preferred distribution method is to share the pipeline and allow users to rebuild the most recent source snapshot. The repository also commits a generated snapshot for competition reproducibility and inspection; this snapshot can become stale relative to the live upstream services.
