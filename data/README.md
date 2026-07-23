# Data Directory

The reproducible pipeline writes generated data to `outputs/` rather than this directory. This folder documents the data contract and prevents confusion between source data, derived data, and model artefacts.

## Source data

The pipeline downloads source records directly from:

1. World Bank Real-Time Food Prices, Indonesia market-level monthly estimates.
2. NASA POWER Monthly Point API at province market-centroid coordinates.

No manually edited raw dataset is required to reproduce the current pilot.

## Derived data

Generated CSV files are committed under `outputs/` after the GitHub Actions pipeline succeeds. See:

- `docs/DATASET_CARD.md`
- `docs/DATA_DICTIONARY.md`
- `docs/DATA_PROVENANCE_AND_LICENSES.md`

## Common key

All modalities are transformed to:

```text
province × commodity × month
```

The identifiers in machine-readable files are:

```text
adm1_name × commodity × date
```

## Rebuild

```bash
python -m pip install -r requirements.txt
python src/run_pipeline.py
```

The pipeline is intentionally responsible for obtaining and transforming the upstream sources so that the generated snapshot can be audited and refreshed.
