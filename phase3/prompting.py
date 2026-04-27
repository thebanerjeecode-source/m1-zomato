from __future__ import annotations

import json
from typing import Any

from .schemas import Phase2Shortlist


SYSTEM_PROMPT = """You are a restaurant recommendation assistant.

You MUST obey these rules:
1) Only recommend restaurants from the provided shortlist. Do not invent new restaurants.
2) Output must be VALID JSON only (no markdown, no backticks).
3) The JSON must match the schema exactly.
4) Rank items best-to-worst for the given preferences.
5) Explanations must be concise and must not make up numeric facts (rating/cost) that aren't provided.
"""


def build_user_prompt(shortlist: Phase2Shortlist, top_n: int = 5) -> str:
    prefs = shortlist.preferences
    # Include only essential fields to reduce token usage.
    candidates: list[dict[str, Any]] = []
    for r in shortlist.shortlist[:50]:  # hard cap to avoid overlong contexts
        candidates.append(
            {
                "id": r.id,
                "name": r.name,
                "location": r.location,
                "cuisines": r.cuisines,
                "cost": r.cost,
                "rating": r.rating,
            }
        )

    schema = {
        "items": [
            {
                "id": "string (must be one of candidate ids)",
                "rank": "integer starting at 1",
                "explanation": "short string (<=600 chars)",
            }
        ]
    }

    return (
        "User preferences:\n"
        f"{json.dumps(prefs, ensure_ascii=False)}\n\n"
        f"Return the top {top_n} recommendations.\n\n"
        "Candidate shortlist (ONLY source of truth):\n"
        f"{json.dumps(candidates, ensure_ascii=False)}\n\n"
        "Output JSON schema:\n"
        f"{json.dumps(schema, ensure_ascii=False)}\n"
    )

