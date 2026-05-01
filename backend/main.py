from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

# Load .env file — always overwrite so reloads pick up changes
def _load_dotenv() -> None:
    env_path = Path(".env")
    if env_path.exists():
        for raw_line in env_path.read_text().splitlines():
            raw_line = raw_line.strip()
            if raw_line and not raw_line.startswith("#") and "=" in raw_line:
                k, v = raw_line.split("=", 1)
                os.environ[k] = v

_load_dotenv()

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
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
    Always force-set so stale process state never blocks the LLM.
    """
    # Re-read .env on every call to pick up any changes without restart
    _load_dotenv()
    api_key = os.environ.get("GROQ_API_KEY")
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    if not api_key:
        logger.error("GROQ_API_KEY is not set — LLM will not be used!")
        return False, None
    # Force-set every time (not setdefault) so updates always propagate
    os.environ["PHASE3_LLM_BASE_URL"] = "https://api.groq.com/openai/v1"
    os.environ["PHASE3_LLM_API_KEY"] = api_key
    os.environ["PHASE3_LLM_MODEL"] = model
    return True, model


import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("backend.main")

app = FastAPI(title="Restaurant Recs API", version="1.0.0")

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Request: {request.method} {request.url.path} - Status: {response.status_code} - Latency: {process_time:.4f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request: {request.method} {request.url.path} - Error: {str(e)} - Latency: {process_time:.4f}s")
        raise

# Setup CORS to allow React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for Vercel deployment
    allow_credentials=False, # Must be False when origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api/v1")

@api_router.get("/status")
def status() -> dict[str, Any]:
    ready, model = _configure_groq_env()
    return {"llm_ready": ready, "model": model}


@api_router.post("/recommend", response_model=UIResponse)
def recommend(req: UIRequest) -> UIResponse:
    ready, model = _configure_groq_env()
    logger.info(f"LLM ready={ready}, model={model}, api_key_set={'PHASE3_LLM_API_KEY' in os.environ}")

    # Calculate paths relatively assuming backend is run from project root
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
    logger.info(f"Shortlist size={len(shortlist_resp.shortlist)}, warnings={shortlist_resp.warnings}")

    p3_shortlist = Phase3Shortlist.model_validate(shortlist_resp.model_dump())
    ranked = rank_with_llm(p3_shortlist, source_path="backend:phase2_shortlist", top_n=req.top_n)
    logger.info(f"Ranked used_llm={ranked.used_llm}, warnings={ranked.warnings}")

    warnings = []
    warnings.extend(shortlist_resp.warnings)
    warnings.extend(ranked.warnings)

    return UIResponse(
        used_llm=ranked.used_llm and ready,
        model=model if ready else None,
        warnings=warnings,
        recommendations=ranked.ranked,
    )

app.include_router(api_router)
