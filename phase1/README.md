# Phase 1 — Data Ingestion

Downloads the Zomato dataset from Hugging Face, normalizes key fields, and writes a clean Parquet artifact + manifest.

## Install

```bash
./.venv/bin/pip install -r phase1/requirements.txt
```

## Run

```bash
./.venv/bin/python -m phase1.run_ingest
```

## Outputs
- `phase1/artifacts/zomato_clean.parquet`
- `phase1/artifacts/manifest.json`

