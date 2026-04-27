from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class Phase2ShortlistItem(BaseModel):
    id: str
    name: Optional[str] = None
    location: Optional[str] = None
    cuisines: List[str] = Field(default_factory=list)
    cost: Optional[float] = None
    rating: Optional[float] = None
    score: float = 0.0


class Phase2Shortlist(BaseModel):
    preferences: dict[str, Any]
    applied_filters: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    shortlist: list[Phase2ShortlistItem]


class LLMRankedItem(BaseModel):
    id: str
    rank: int = Field(..., ge=1)
    explanation: str = Field(..., min_length=1, max_length=600)


class LLMRankResponse(BaseModel):
    items: list[LLMRankedItem]


class Phase3Result(BaseModel):
    source_shortlist_path: str
    used_llm: bool
    model: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    ranked: list[dict[str, Any]]  # restaurant fields + explanation + rank

