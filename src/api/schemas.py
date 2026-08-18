"""
Pydantic Request/Response Schemas for the FastAPI REST Layer.
Provides strict validation, serialization, and OpenAPI documentation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


# ─── Request Schemas ────────────────────────────────────────────

class RecommendationRequest(BaseModel):
    """POST /recommendations request body."""

    location: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="City or locality name (e.g. 'Bangalore', 'Koramangala').",
        examples=["Bangalore"],
    )
    budget: str = Field(
        ...,
        description="Budget tier: 'low', 'medium', or 'high'.",
        examples=["medium"],
    )
    cuisine: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Preferred cuisine type (optional). Leave empty for any.",
        examples=["Italian"],
    )
    min_rating: float = Field(
        default=0.0,
        ge=0.0,
        le=5.0,
        description="Minimum restaurant rating threshold (0.0 – 5.0).",
        examples=[4.0],
    )
    additional_preferences: Optional[str] = Field(
        default=None,
        max_length=300,
        description="Free-text additional preferences (optional, max 300 chars).",
        examples=["family-friendly, outdoor seating"],
    )

    @field_validator("budget")
    @classmethod
    def validate_budget(cls, v: str) -> str:
        normalized = v.strip().lower()
        if normalized not in ("low", "medium", "high"):
            raise ValueError("Budget must be 'low', 'medium', or 'high'.")
        return normalized

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Location cannot be empty.")
        return stripped


# ─── Response Schemas ───────────────────────────────────────────

class RecommendationItem(BaseModel):
    """A single ranked restaurant recommendation."""

    restaurant_name: str = Field(..., description="Restaurant name from dataset.")
    rank: int = Field(..., ge=1, description="Rank position (1 = best match).")
    cuisine: str = Field(..., description="Cuisine types offered.")
    rating: float = Field(..., ge=0.0, le=5.0, description="Dataset rating (0.0 – 5.0).")
    estimated_cost: str = Field(..., description="Estimated cost for two persons.")
    explanation: str = Field(..., description="Why this restaurant matches user preferences.")


class RecommendationResponseSchema(BaseModel):
    """POST /recommendations response body."""

    summary: Optional[str] = Field(None, description="Brief overview of the recommendation set.")
    recommendations: List[RecommendationItem] = Field(
        default_factory=list,
        description="Ranked list of restaurant recommendations.",
    )
    filters_relaxed: Optional[List[str]] = Field(
        None,
        description="List of filter names relaxed to produce results (e.g. ['min_rating', 'budget']).",
    )
    is_fallback: bool = Field(
        False,
        description="True if LLM was unavailable and deterministic fallback was used.",
    )
    total_candidates: int = Field(
        0,
        ge=0,
        description="Total number of candidates that matched filters before ranking.",
    )


class HealthResponse(BaseModel):
    """GET /health response body."""

    status: str = Field(..., description="Service health status.", examples=["ok"])
    dataset_loaded: bool = Field(..., description="Whether restaurant dataset is loaded in memory.")
    restaurant_count: int = Field(..., ge=0, description="Number of restaurants currently loaded.")
    groq_configured: bool = Field(..., description="Whether Groq API key is configured.")


class MetadataListResponse(BaseModel):
    """Generic metadata list response (cities, cuisines, budget tiers)."""

    items: List[str] = Field(default_factory=list, description="Sorted list of available values.")
    count: int = Field(0, ge=0, description="Number of items in the list.")


class ErrorResponse(BaseModel):
    """Standard error response body."""

    error: str = Field(..., description="Error type identifier.")
    message: str = Field(..., description="Human-readable error description.")
    details: Optional[str] = Field(None, description="Additional diagnostic details.")
