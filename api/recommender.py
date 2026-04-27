from __future__ import annotations

from dataclasses import dataclass

from .schemas import Preferences, Restaurant


def _norm(s: str) -> str:
    return " ".join(s.strip().lower().split())


@dataclass(frozen=True)
class ScoredRestaurant:
    restaurant: Restaurant
    score: float


def filter_and_rank(restaurants: list[Restaurant], prefs: Preferences) -> tuple[list[ScoredRestaurant], dict, list[str]]:
    """
    Phase 0 deterministic recommender.
    - Hard filters: location match, min_rating threshold (if rating present), budget exact match.
    - Soft boosts: cuisine match strength, rating presence/value, simple tag match from additional_preferences.
    """

    warnings: list[str] = []

    location_q = _norm(prefs.location)
    cuisine_q = _norm(prefs.cuisine)
    addl_q = _norm(prefs.additional_preferences or "")

    def location_match(r: Restaurant) -> bool:
        return _norm(r.location) == location_q

    def budget_match(r: Restaurant) -> bool:
        return r.cost_level == prefs.budget

    def rating_match(r: Restaurant) -> bool:
        if r.rating is None:
            return False if prefs.min_rating > 0 else True
        return r.rating >= prefs.min_rating

    filtered = [r for r in restaurants if location_match(r) and budget_match(r) and rating_match(r)]

    # If strict budget causes empties, relax budget as a transparent fallback (Phase 0 usability).
    if not filtered:
        warnings.append("No matches found with strict budget; relaxing budget constraint for phase0 fallback.")
        filtered = [r for r in restaurants if location_match(r) and rating_match(r)]

    # If still none, relax to location only.
    if not filtered:
        warnings.append("No matches found with rating constraint; relaxing rating constraint for phase0 fallback.")
        filtered = [r for r in restaurants if location_match(r)]

    # If location itself yields none, return empty list (caller will surface suggestions later).
    applied_filters = {
        "location": prefs.location,
        "budget": prefs.budget,
        "cuisine": prefs.cuisine,
        "min_rating": prefs.min_rating,
        "additional_preferences": prefs.additional_preferences,
        "shortlist_source": "stub",
    }

    scored: list[ScoredRestaurant] = []
    for r in filtered:
        score = 0.0

        # Cuisine match: exact token contains.
        cuisines_norm = [_norm(c) for c in r.cuisines]
        if any(cuisine_q == c for c in cuisines_norm):
            score += 3.0
        elif any(cuisine_q in c for c in cuisines_norm):
            score += 2.0

        # Rating boost (if present).
        if r.rating is not None:
            score += min(max(r.rating, 0.0), 5.0)  # 0..5
        else:
            score += 0.5  # small credit so unrated can appear in relaxed flows

        # Additional preference crude tag match (phase0).
        tags = [str(t).lower() for t in (r.metadata.get("tags") or [])] if r.metadata else []
        if addl_q:
            if any(t in addl_q for t in tags):
                score += 1.0

        scored.append(ScoredRestaurant(restaurant=r, score=score))

    scored.sort(key=lambda x: (-x.score, _norm(x.restaurant.name), x.restaurant.id))
    return scored[: prefs.top_n], applied_filters, warnings


def build_explanation(r: Restaurant, prefs: Preferences) -> str:
    parts: list[str] = []
    parts.append(f"Matches your location preference for {prefs.location}.")
    parts.append(f"Budget category: {r.cost_level.value}.")

    if r.rating is not None:
        parts.append(f"Rated {r.rating:.1f}.")
    else:
        parts.append("Rating not available; included due to relaxed filters.")

    cuisine_q = _norm(prefs.cuisine)
    cuisines_norm = [_norm(c) for c in r.cuisines]
    if any(cuisine_q == c for c in cuisines_norm) or any(cuisine_q in c for c in cuisines_norm):
        parts.append(f"Includes {prefs.cuisine} cuisine.")

    if prefs.additional_preferences:
        tags = [str(t).lower() for t in (r.metadata.get('tags') or [])] if r.metadata else []
        if any(t in _norm(prefs.additional_preferences) for t in tags):
            parts.append(f"Aligns with your preference: {prefs.additional_preferences}.")

    return " ".join(parts)

