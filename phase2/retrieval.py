from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from .schemas import BudgetLevel, Preferences, ShortlistItem, ShortlistResponse


def _norm(s: Optional[str]) -> str:
    if not s:
        return ""
    return " ".join(str(s).strip().lower().split())


def _split_cuisines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        s = str(value)
        # Common shapes observed:
        # - "Italian, Chinese"
        # - "['south indian' 'north indian' 'chinese']" (stringified array)
        if s.startswith("[") and "'" in s:
            quoted = re.findall(r"'([^']+)'", s)
            items = quoted if quoted else [s]
        else:
            items = re.split(r"[,/|;]+", s)
    out: list[str] = []
    for it in items:
        t = _norm(str(it))
        if t:
            out.append(t)
    # de-dupe preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for c in out:
        if c in seen:
            continue
        seen.add(c)
        deduped.append(c)
    return deduped


def _budget_to_cost_range(level: BudgetLevel) -> tuple[float, float]:
    # Heuristic placeholder. Phase 2 will refine once we confirm the dataset's cost meaning.
    # Typical Zomato "approx_cost(for two people)" is in INR.
    if level == BudgetLevel.low:
        return (0.0, 600.0)
    if level == BudgetLevel.medium:
        return (600.0, 1500.0)
    return (1500.0, float("inf"))


def load_parquet(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    # Normalize expected columns existence
    for col in ["id", "name", "location", "cuisines", "cost", "rating"]:
        if col not in df.columns:
            df[col] = None
    # Ensure numeric columns are numeric (avoid object dtype warnings).
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    # De-duplicate obvious duplicates to make shortlist stable.
    df["_cuisines_norm"] = df["cuisines"].apply(_split_cuisines)
    # Lists are unhashable; dedupe on a deterministic string key instead.
    df["_cuisines_key"] = df["_cuisines_norm"].apply(lambda xs: "|".join(xs) if isinstance(xs, list) else "")
    df = df.drop_duplicates(subset=["id", "name", "location", "_cuisines_key"], keep="first").copy()
    return df


def _apply_filters(df: pd.DataFrame, prefs: Preferences) -> tuple[pd.DataFrame, dict[str, Any], list[str]]:
    warnings: list[str] = []
    applied: dict[str, Any] = {
        "location": prefs.location,
        "location_match": prefs.location_match,
        "budget": prefs.budget.value,
        "cuisine": prefs.cuisine,
        "min_rating": prefs.min_rating,
    }

    loc_q = _norm(prefs.location)
    if prefs.location_match == "exact":
        mask_loc = df["location"].fillna("").map(_norm) == loc_q
    else:
        mask_loc = df["location"].fillna("").map(_norm).str.contains(re.escape(loc_q), na=False)
    out = df[mask_loc].copy()

    # Cuisine filter (if cuisines column exists/usable)
    cuisine_q = _norm(prefs.cuisine)
    if "cuisines" in out.columns:
        if cuisine_q and cuisine_q.lower() != "any":
            cuisines_norm = out["cuisines"].apply(_split_cuisines)
            out["_cuisines_norm"] = cuisines_norm
            mask_cuisine = cuisines_norm.apply(lambda xs: any(cuisine_q == x or cuisine_q in x for x in xs))
            out = out[mask_cuisine].copy()
    else:
        warnings.append("Dataset missing cuisines column; skipping cuisine filter.")

    # Rating filter
    if prefs.min_rating > 0:
        if df["rating"].notna().any():
            out = out[(out["rating"].fillna(-1.0) >= float(prefs.min_rating))].copy()
        else:
            warnings.append("Dataset ratings are missing; cannot enforce min_rating filter.")

    # Budget filter via cost (if cost present)
    if df["cost"].notna().any():
        if prefs.budget:
            lo, hi = _budget_to_cost_range(prefs.budget)
            out = out[(out["cost"].fillna(-1.0) >= lo) & (out["cost"].fillna(float("inf")) < hi)].copy()
    else:
        warnings.append("Dataset cost is missing; cannot enforce budget filter.")

    return out, applied, warnings


def _score(df: pd.DataFrame, prefs: Preferences) -> pd.DataFrame:
    cuisine_q = _norm(prefs.cuisine)

    def cuisine_score(xs: list[str]) -> float:
        if not xs:
            return 0.0
        if any(cuisine_q == x for x in xs):
            return 3.0
        if any(cuisine_q in x for x in xs):
            return 2.0
        return 0.0

    if "_cuisines_norm" not in df.columns:
        df["_cuisines_norm"] = df["cuisines"].apply(_split_cuisines)

    df["_cuisine_score"] = df["_cuisines_norm"].apply(cuisine_score)
    df["_rating_score"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0).clip(lower=0.0, upper=5.0)

    # Cost proximity (soft): prefer closer to the middle of budget range when cost exists
    if df["cost"].notna().any():
        lo, hi = _budget_to_cost_range(prefs.budget)
        target = lo + (hi - lo) / 2.0 if hi != float("inf") else max(lo, 2000.0)
        # smaller distance => higher score
        df["_cost_score"] = (1.0 / (1.0 + (df["cost"].fillna(target) - target).abs() / 500.0)).clip(0.0, 1.0)
    else:
        df["_cost_score"] = 0.0

    df["_score"] = df["_cuisine_score"] * 2.0 + df["_rating_score"] + df["_cost_score"]

    # Stable ordering
    df["_name_norm"] = df["name"].fillna("").map(_norm)
    df["_id_norm"] = df["id"].fillna("").astype(str)
    df = df.sort_values(by=["_score", "_rating_score", "_name_norm", "_id_norm"], ascending=[False, False, True, True])
    return df


def build_shortlist(dataset_path: Path, prefs: Preferences) -> ShortlistResponse:
    df = load_parquet(dataset_path)

    strict_df, applied, warnings = _apply_filters(df, prefs)
    working = strict_df

    # ── Stage 1 relaxation: drop cuisine filter ───────────────────────────────
    if working.empty:
        loc_q = _norm(prefs.location)
        if prefs.location_match == "exact":
            loc_df = df[df["location"].fillna("").map(_norm) == loc_q].copy()
        else:
            loc_df = df[df["location"].fillna("").map(_norm).str.contains(re.escape(loc_q), na=False)].copy()

        # Re-apply rating + budget but without cuisine
        working = loc_df.copy()
        if prefs.min_rating > 0 and df["rating"].notna().any():
            working = working[working["rating"].fillna(-1.0) >= float(prefs.min_rating)].copy()
        if df["cost"].notna().any() and prefs.budget:
            lo, hi = _budget_to_cost_range(prefs.budget)
            working = working[(working["cost"].fillna(-1.0) >= lo) & (working["cost"].fillna(float("inf")) < hi)].copy()
        applied["relaxed_cuisine"] = True

    # ── Stage 2 relaxation: also drop rating filter ───────────────────────────
    if working.empty and prefs.min_rating > 0:
        loc_q = _norm(prefs.location)
        if prefs.location_match == "exact":
            loc_df = df[df["location"].fillna("").map(_norm) == loc_q].copy()
        else:
            loc_df = df[df["location"].fillna("").map(_norm).str.contains(re.escape(loc_q), na=False)].copy()

        working = loc_df.copy()
        if df["cost"].notna().any() and prefs.budget:
            lo, hi = _budget_to_cost_range(prefs.budget)
            working = working[(working["cost"].fillna(-1.0) >= lo) & (working["cost"].fillna(float("inf")) < hi)].copy()
        applied["relaxed_rating"] = True

    # ── Stage 3 relaxation: location-only (all filters dropped) ──────────────
    if working.empty:
        loc_q = _norm(prefs.location)
        if prefs.location_match == "exact":
            working = df[df["location"].fillna("").map(_norm) == loc_q].copy()
        else:
            working = df[df["location"].fillna("").map(_norm).str.contains(re.escape(loc_q), na=False)].copy()
        applied["relaxed_all"] = True

    scored = _score(working, prefs)
    top = scored.head(int(prefs.top_k))

    items: list[ShortlistItem] = []
    for _, row in top.iterrows():
        cuisines = row.get("_cuisines_norm")
        if not isinstance(cuisines, list):
            cuisines = _split_cuisines(row.get("cuisines"))
        items.append(
            ShortlistItem(
                id=str(row.get("id") or ""),
                name=row.get("name"),
                location=row.get("location"),
                cuisines=cuisines,
                cost=None if pd.isna(row.get("cost")) else float(row.get("cost")),
                rating=None if pd.isna(row.get("rating")) else float(row.get("rating")),
                score=float(row.get("_score") or 0.0),
            )
        )

    return ShortlistResponse(
        preferences=prefs,
        applied_filters=applied,
        warnings=warnings,
        shortlist=items,
    )

