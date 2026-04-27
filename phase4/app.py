from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from phase2.retrieval import build_shortlist
from phase2.schemas import BudgetLevel as Phase2BudgetLevel
from phase2.schemas import Preferences as Phase2Preferences
from phase3.ranker import rank_with_llm
from phase3.schemas import Phase2Shortlist as Phase3Shortlist


class UIRequest(BaseModel):
    location: str = Field(..., min_length=1)
    cuisine: str = Field(..., min_length=1)
    budget: str = Field("medium")
    min_rating: float = Field(0.0, ge=0.0, le=5.0)
    additional_preferences: Optional[str] = Field(None, max_length=2000)
    top_n: int = Field(5, ge=1, le=20)


class UIResponse(BaseModel):
    used_llm: bool
    model: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[dict[str, Any]]


def _configure_groq_env() -> tuple[bool, Optional[str]]:
    """
    Groq provides an OpenAI-compatible endpoint.
    We configure Phase 3's env vars from GROQ_* vars.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    model = os.environ.get("GROQ_MODEL", "llama-3.1-70b-versatile")
    if not api_key:
        return False, None
    os.environ.setdefault("PHASE3_LLM_BASE_URL", "https://api.groq.com/openai/v1")
    os.environ.setdefault("PHASE3_LLM_API_KEY", api_key)
    os.environ.setdefault("PHASE3_LLM_MODEL", model)
    return True, model


app = FastAPI(title="Phase 4 UI (Groq)", version="0.1.0")

_ROOT = Path(__file__).resolve().parent
_UI_DIR = _ROOT / "ui"
app.mount("/ui", StaticFiles(directory=str(_UI_DIR), html=True), name="ui")


@app.get("/")
def root() -> FileResponse:
    return FileResponse(_UI_DIR / "index.html")


@app.get("/api/status")
def status() -> dict[str, Any]:
    ready, model = _configure_groq_env()
    return {"llm_ready": ready, "model": model}


@app.post("/api/recommend", response_model=UIResponse)
def recommend(req: UIRequest) -> UIResponse:
    ready, model = _configure_groq_env()

    parquet_path = os.environ.get("PHASE1_PARQUET_PATH", "phase1/artifacts/zomato_clean.parquet")
    p2_prefs = Phase2Preferences(
        location=req.location,
        cuisine=req.cuisine,
        budget=Phase2BudgetLevel(req.budget),
        min_rating=req.min_rating,
        top_k=50,
        location_match="contains",
    )

    shortlist_resp = build_shortlist(Path(parquet_path), p2_prefs)

    # Convert Phase2 response -> Phase3 input schema (dict-based preferences is fine for prompting).
    p3_shortlist = Phase3Shortlist.model_validate(shortlist_resp.model_dump())
    ranked = rank_with_llm(p3_shortlist, source_path="phase4:phase2_shortlist", top_n=req.top_n)

    warnings = []
    warnings.extend(shortlist_resp.warnings)
    warnings.extend(ranked.warnings)

    return UIResponse(
        used_llm=ranked.used_llm and ready,
        model=model if ready else None,
        warnings=warnings,
        recommendations=ranked.ranked,
    )

