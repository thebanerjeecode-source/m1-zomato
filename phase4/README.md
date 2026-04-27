# Phase 4 — UI / UX (Groq-backed LLM)

Phase 4 provides a basic web UI that collects user preferences and calls a Phase 4 API which orchestrates:
- Phase 2 deterministic retrieval (shortlist)
- Phase 3 LLM ranking + explanations (**Groq** via OpenAI-compatible endpoint)

## Run

```bash
./.venv/bin/uvicorn phase4.app:app --reload --port 8010
```

Open:
- `http://127.0.0.1:8010/`

## Groq configuration

Set:
- `GROQ_API_KEY`
- `GROQ_MODEL` (example: `llama-3.1-70b-versatile`)

Optional:
- `PHASE1_PARQUET_PATH` (defaults to `phase1/artifacts/zomato_clean.parquet`)

## Notes
- If Groq is not configured, the server will fall back to deterministic ordering + templated explanations.

