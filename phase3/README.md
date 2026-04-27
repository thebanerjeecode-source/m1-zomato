# Phase 3 — LLM Ranking + Explanations (bounded, non-hallucinating)

Phase 3 takes a deterministic shortlist (from Phase 2) and uses an LLM to:
- **Rank** restaurants
- Generate **concise explanations**

Hard constraint: the final output must reference **only restaurants present in the provided shortlist**.

## Install

```bash
./.venv/bin/pip install -r phase3/requirements.txt
```

## Run (CLI)

Use a Phase 2 shortlist JSON as input:

```bash
./.venv/bin/python -m phase3.run_rank \
  --shortlist phase2/artifacts/shortlist.json \
  --out phase3/artifacts/llm_ranked.json
```

## LLM configuration (optional)

By default, Phase 3 runs in **fallback mode** (deterministic ranking + templated explanations) unless you provide an LLM endpoint.

Set these environment variables to enable LLM calls (OpenAI-compatible API):
- `PHASE3_LLM_BASE_URL` (e.g. `https://api.openai.com/v1`)
- `PHASE3_LLM_API_KEY`
- `PHASE3_LLM_MODEL` (e.g. `gpt-4.1-mini` or any model your endpoint supports)

## Output
- `phase3/artifacts/llm_ranked.json` containing:
  - ranked restaurants (subset of shortlist)
  - explanations
  - validation status and any warnings/fallback reasons

