from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .data_stub import get_stub_restaurants
from .recommender import build_explanation, filter_and_rank
from .schemas import Preferences, RecommendResponse, Recommendation


app = FastAPI(title="Zomato-style Recommender (Phase 0)", version="0.1.0")

_ROOT = Path(__file__).resolve().parents[1]
_UI_DIR = _ROOT / "ui"

if _UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(_UI_DIR), html=True), name="ui")


@app.get("/")
def root() -> FileResponse:
    return FileResponse(_UI_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/recommendations", response_model=RecommendResponse)
def recommend(prefs: Preferences) -> RecommendResponse:
    restaurants = get_stub_restaurants()
    scored, applied_filters, warnings = filter_and_rank(restaurants, prefs)

    recs = [
        Recommendation(
            restaurant=s.restaurant,
            score=s.score,
            explanation=build_explanation(s.restaurant, prefs),
        )
        for s in scored
    ]

    if not recs:
        warnings.append(
            "No restaurants found for the given location. Try a different city (e.g., Delhi, Bangalore, Mumbai, Hyderabad)."
        )

    return RecommendResponse(recommendations=recs, applied_filters=applied_filters, warnings=warnings)

