"""
User Preferences Entity Data Model.
Represents user search constraints and preference parameters.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Literal, Optional

BudgetTier = Literal["low", "medium", "high"]


@dataclass
class UserPreferences:
    """User preferences for restaurant recommendation filtering and ranking."""

    location: str
    budget: BudgetTier
    cuisine: Optional[str] = None
    min_rating: float = 0.0
    additional_preferences: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate and normalize user preferences."""
        self.location = str(self.location).strip()
        if not self.location:
            raise ValueError("Location is required and cannot be empty.")

        # Normalize budget
        budget_norm = str(self.budget).strip().lower()
        if budget_norm not in ("low", "medium", "high"):
            raise ValueError(f"Invalid budget tier '{self.budget}'. Must be 'low', 'medium', or 'high'.")
        self.budget = budget_norm  # type: ignore

        # Clean cuisine
        if self.cuisine:
            self.cuisine = str(self.cuisine).strip()
            if not self.cuisine:
                self.cuisine = None

        # Clean and clamp min_rating to [0.0, 5.0]
        try:
            val = float(self.min_rating)
            if val < 0.0 or val > 5.0:
                raise ValueError("min_rating must be between 0.0 and 5.0")
            self.min_rating = round(val, 1)
        except (TypeError, ValueError) as exc:
            if isinstance(exc, ValueError) and "min_rating must be between" in str(exc):
                raise
            raise ValueError(f"Invalid min_rating '{self.min_rating}'. Must be a float between 0.0 and 5.0.")

        # Clean additional_preferences (cap length to 300 per edge-case.md §3.6)
        if self.additional_preferences:
            self.additional_preferences = str(self.additional_preferences).strip()[:300]
            if not self.additional_preferences:
                self.additional_preferences = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize preferences to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPreferences":
        """Instantiate UserPreferences from a dictionary."""
        return cls(
            location=data.get("location", ""),
            budget=data.get("budget", "medium"),
            cuisine=data.get("cuisine"),
            min_rating=float(data.get("min_rating", 0.0)),
            additional_preferences=data.get("additional_preferences"),
        )
