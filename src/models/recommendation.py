"""
Recommendation Entity Models.
Defines structured data structures for recommendations and LLM responses.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class Recommendation:
    """A single recommended restaurant item with explanation and ranking."""

    restaurant_name: str
    rank: int
    cuisine: str
    rating: float
    estimated_cost: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize recommendation to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Recommendation":
        """Instantiate a Recommendation entity from dictionary."""
        return cls(
            restaurant_name=str(data.get("restaurant_name", "")).strip(),
            rank=int(data.get("rank", 1)),
            cuisine=str(data.get("cuisine", "")).strip(),
            rating=float(data.get("rating", 0.0)),
            estimated_cost=str(data.get("estimated_cost", "Price on request")).strip(),
            explanation=str(data.get("explanation", "")).strip(),
        )


@dataclass
class RecommendationResponse:
    """Full recommendation response containing summary and ranked restaurants."""

    summary: Optional[str]
    recommendations: List[Recommendation]
    filters_relaxed: Optional[List[str]] = None
    is_fallback: bool = False
    total_candidates: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize response to dictionary."""
        return {
            "summary": self.summary,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "filters_relaxed": self.filters_relaxed,
            "is_fallback": self.is_fallback,
            "total_candidates": self.total_candidates,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecommendationResponse":
        """Instantiate RecommendationResponse from dictionary."""
        recs_raw = data.get("recommendations", [])
        recommendations = [
            Recommendation.from_dict(r) if isinstance(r, dict) else r
            for r in recs_raw
        ]
        return cls(
            summary=data.get("summary"),
            recommendations=recommendations,
            filters_relaxed=data.get("filters_relaxed"),
            is_fallback=bool(data.get("is_fallback", False)),
            total_candidates=int(data.get("total_candidates", len(recommendations))),
        )
