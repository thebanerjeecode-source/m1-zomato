# Phase 2 — Retrieval & Rule‑Based Filtering

Loads the normalized dataset produced in Phase 1 and builds a deterministic shortlist using rule-based filtering and scoring.

## Install

```bash
./.venv/bin/pip install -r phase2/requirements.txt
```

## Run (CLI)

```bash
./.venv/bin/python -m phase2.run_retrieve \
  --location "BTM" \
  --budget low \
  --cuisine "Chinese" \
  --min-rating 3.5 \
  --top-k 25 \
  --out phase2/artifacts/shortlist.json
```

## Inputs / Outputs
- **Input dataset** (default): `phase1/artifacts/zomato_clean.parquet`
- **Output**: a JSON file containing:
  - `shortlist`: top \(K\) restaurants with scores
  - `warnings`: any constraint relaxations or missing-field notes

## Notes
- The Phase 1 dataset has `cost` and `rating` columns, but they may be null depending on upstream schema. Phase 2 handles missing `cost`/`rating` safely and will warn when it cannot enforce those constraints.

