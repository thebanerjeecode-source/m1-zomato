from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class BudgetLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Preferences(BaseModel):
    location: str = Field(..., min_length=1)
    budget: BudgetLevel = BudgetLevel.medium
    cuisine: str = Field(..., min_length=1)
    min_rating: float = Field(0.0, ge=0.0, le=5.0)
    top_k: int = Field(25, ge=1, le=200)
    location_match: str = Field("contains", description="contains|exact")


class RestaurantRow(BaseModel):
    id: str
    name: Optional[str] = None
    location: Optional[str] = None
    cuisines: List[str] = Field(default_factory=list)
    cost: Optional[float] = None
    rating: Optional[float] = None

    # keep extra fields if present in parquet
    extra: dict[str, Any] = Field(default_factory=dict)


class ShortlistItem(BaseModel):
    id: str
    name: Optional[str]
    location: Optional[str]
    cuisines: List[str]
    cost: Optional[float]
    rating: Optional[float]
    score: float


class ShortlistResponse(BaseModel):
    preferences: Preferences
    applied_filters: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)
    shortlist: list[ShortlistItem]

