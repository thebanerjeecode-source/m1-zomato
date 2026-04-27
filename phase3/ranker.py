from __future__ import annotations

import json
from typing import Any

from .llm_client import chat_completions, load_llm_config
from .prompting import SYSTEM_PROMPT, build_user_prompt
from .schemas import LLMRankResponse, Phase2Shortlist, Phase3Result


def _safe_json_loads(text: str) -> Any:
    """
    Try parsing as JSON. If model returned extra text, attempt to extract the first JSON object.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _validate_no_hallucinations(resp: LLMRankResponse, shortlist: Phase2Shortlist) -> tuple[LLMRankResponse, list[str]]:
    warnings: list[str] = []
    allowed_ids = {r.id for r in shortlist.shortlist}

    deduped_items = []
    seen: set[str] = set()
    for item in resp.items:
        if item.id not in allowed_ids:
            warnings.append(f"LLM returned unknown id '{item.id}'.")
            continue
        if item.id in seen:
            continue
        seen.add(item.id)
        deduped_items.append(item)

    # Re-rank sequentially (1..N) after validation
    for idx, item in enumerate(deduped_items, start=1):
        item.rank = idx

    return LLMRankResponse(items=deduped_items), warnings


def _fallback_rank(shortlist: Phase2Shortlist, top_n: int) -> tuple[list[dict[str, Any]], list[str]]:
    warnings = ["LLM not used or failed; returning deterministic shortlist order with templated explanations."]
    ranked = []
    for i, r in enumerate(shortlist.shortlist[:top_n], start=1):
        explanation_parts = []
        if r.location:
            explanation_parts.append(f"Located in {r.location}.")
        if r.cuisines:
            explanation_parts.append(f"Cuisines: {', '.join(r.cuisines[:4])}.")
        if r.rating is not None:
            explanation_parts.append(f"Rating: {r.rating}.")
        if r.cost is not None:
            explanation_parts.append(f"Cost: {r.cost}.")
        explanation = " ".join(explanation_parts) or "Matches the deterministic shortlist filters."

        ranked.append(
            {
                "rank": i,
                "id": r.id,
                "name": r.name,
                "location": r.location,
                "cuisines": r.cuisines,
                "cost": r.cost,
                "rating": r.rating,
                "explanation": explanation[:600],
            }
        )
    return ranked, warnings


def rank_with_llm(shortlist: Phase2Shortlist, source_path: str, top_n: int = 5) -> Phase3Result:
    cfg = load_llm_config()
    warnings: list[str] = []

    if cfg is None:
        ranked, w = _fallback_rank(shortlist, top_n)
        warnings.extend(w)
        return Phase3Result(
            source_shortlist_path=source_path,
            used_llm=False,
            model=None,
            warnings=warnings,
            ranked=ranked,
        )

    # Guard: don't call LLM with an empty shortlist
    if not shortlist.shortlist:
        return Phase3Result(
            source_shortlist_path=source_path,
            used_llm=False,
            model=cfg.model,
            warnings=warnings + ["No restaurants found for the given location."],
            ranked=[],
        )

    user_prompt = build_user_prompt(shortlist, top_n=top_n)

    try:
        raw = chat_completions(cfg, SYSTEM_PROMPT, user_prompt)
        data = _safe_json_loads(raw)
        parsed = LLMRankResponse.model_validate(data)
        parsed, v_warnings = _validate_no_hallucinations(parsed, shortlist)
        warnings.extend(v_warnings)

        # Join back onto restaurant metadata
        by_id = {r.id: r for r in shortlist.shortlist}
        ranked: list[dict[str, Any]] = []
        for item in parsed.items[:top_n]:
            r = by_id[item.id]
            ranked.append(
                {
                    "rank": item.rank,
                    "id": r.id,
                    "name": r.name,
                    "location": r.location,
                    "cuisines": r.cuisines,
                    "cost": r.cost,
                    "rating": r.rating,
                    "explanation": item.explanation,
                }
            )

        if not ranked:
            fb, w = _fallback_rank(shortlist, top_n)
            warnings.extend(["LLM returned no valid items; using fallback."] + w)
            return Phase3Result(
                source_shortlist_path=source_path,
                used_llm=False,
                model=cfg.model,
                warnings=warnings,
                ranked=fb,
            )

        return Phase3Result(
            source_shortlist_path=source_path,
            used_llm=True,
            model=cfg.model,
            warnings=warnings,
            ranked=ranked,
        )
    except Exception as e:
        fb, w = _fallback_rank(shortlist, top_n)
        warnings.extend([f"LLM call/parse failed: {e}"] + w)
        return Phase3Result(
            source_shortlist_path=source_path,
            used_llm=False,
            model=cfg.model if cfg else None,
            warnings=warnings,
            ranked=fb,
        )

