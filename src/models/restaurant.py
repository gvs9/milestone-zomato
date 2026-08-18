"""
Restaurant Entity Data Model.
Represents a normalized restaurant record in the recommendation system.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class Restaurant:
    """Canonical domain representation of a restaurant."""

    name: str
    location: str
    cuisines: List[str]
    rating: float
    cost_for_two: str
    budget_tier: str  # "low" | "medium" | "high"
    city: Optional[str] = None
    locality: Optional[str] = None
    address: Optional[str] = None
    rest_type: Optional[str] = None
    votes: Optional[int] = None
    is_unrated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize restaurant entity to dictionary."""
        return asdict(self)

    def __repr__(self) -> str:
        return (
            f"Restaurant(name='{self.name}', location='{self.location}', "
            f"rating={self.rating}, budget_tier='{self.budget_tier}', "
            f"cuisines={self.cuisines})"
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Restaurant":
        """Instantiate a Restaurant entity from a dictionary."""
        return cls(
            name=str(data.get("name", "")).strip(),
            location=str(data.get("location", "")).strip(),
            cuisines=list(data.get("cuisines", [])),
            rating=float(data.get("rating", 0.0)),
            cost_for_two=str(data.get("cost_for_two", "₹500 for two")),
            budget_tier=str(data.get("budget_tier", "medium")),
            city=data.get("city"),
            locality=data.get("locality"),
            address=data.get("address"),
            rest_type=data.get("rest_type"),
            votes=int(data["votes"]) if data.get("votes") is not None else None,
            is_unrated=bool(data.get("is_unrated", False)),
        )
