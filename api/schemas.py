from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class BudgetLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Preferences(BaseModel):
    location: str = Field(..., min_length=1, description="City/location preference.")
    budget: BudgetLevel = Field(..., description="Budget category.")
    cuisine: str = Field(..., min_length=1, description="Desired cuisine.")
    min_rating: float = Field(0.0, ge=0.0, le=5.0, description="Minimum acceptable rating (0-5).")
    additional_preferences: Optional[str] = Field(
        None, max_length=2000, description="Optional free-text preferences."
    )
    top_n: int = Field(5, ge=1, le=20, description="Number of recommendations to return.")


class Restaurant(BaseModel):
    id: str
    name: str
    location: str
    cuisines: List[str]
    cost_level: BudgetLevel
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Recommendation(BaseModel):
    restaurant: Restaurant
    score: float = Field(..., description="Deterministic score used for ranking in phase0.")
    explanation: str


class RecommendResponse(BaseModel):
    recommendations: List[Recommendation]
    applied_filters: dict[str, Any]
    warnings: List[str] = Field(default_factory=list)

