# AI‑Powered Restaurant Recommendation System (Milestone 1)

This repo contains Phase 0 of a Zomato-inspired restaurant recommendation system: a minimal API with a stable schema, a small in-memory dataset, and deterministic filtering/ranking.

## Quickstart (Phase 0)

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

Run the API:

```bash
./.venv/bin/uvicorn api.main:app --reload
```

Open the basic web UI:

- `http://127.0.0.1:8000/`

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Example recommendations request:

```bash
curl -X POST http://127.0.0.1:8000/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Delhi",
    "budget": "low",
    "cuisine": "Chinese",
    "min_rating": 3.8,
    "additional_preferences": "quick service",
    "top_n": 5
  }'
```

## Notes
- Phase 0 uses a **stub dataset** in `api/data_stub.py`.
- Phase 1/2 will replace this with ingestion + retrieval over the Hugging Face Zomato dataset.

