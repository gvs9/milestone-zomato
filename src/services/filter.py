"""
Restaurant Filtering and Candidate Selection Service.
Deterministically narrows the restaurant corpus before LLM ranking.
"""

from dataclasses import dataclass, field
import logging
import re
from typing import Dict, List, Optional, Set, Tuple

from src.config import settings
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    """Result of deterministic filtering and candidate selection."""

    candidates: List[Restaurant]
    total_matched: int
    filters_relaxed: List[str] = field(default_factory=list)
    is_relaxed: bool = False


class RestaurantFilter:
    """
    Deterministic filtering pipeline with ordered rules, tie-breaking,
    brand deduplication, and sequential filter relaxation.
    """

    def __init__(self, max_candidates: Optional[int] = None) -> None:
        self.max_candidates = max_candidates or settings.max_candidates

    @staticmethod
    def matches_location(restaurant: Restaurant, user_location: str) -> bool:
        """
        Check if restaurant matches user location query (case-insensitive).
        Matches against location, city, locality, or address.
        """
        if not user_location:
            return True

        query = user_location.strip().lower()

        # Check canonical location
        if restaurant.location and query in restaurant.location.lower():
            return True

        # Check explicit city
        if restaurant.city and query in restaurant.city.lower():
            return True

        # Check locality (e.g. Koramangala, Indiranagar)
        if restaurant.locality and query in restaurant.locality.lower():
            return True

        # Check address
        if restaurant.address and query in restaurant.address.lower():
            return True

        return False

    @staticmethod
    def matches_rating(restaurant: Restaurant, min_rating: float) -> bool:
        """Check if restaurant meets the minimum rating threshold."""
        if min_rating <= 0.0:
            return True
        return restaurant.rating >= min_rating

    @staticmethod
    def matches_cuisine(restaurant: Restaurant, requested_cuisine: Optional[str]) -> bool:
        """
        Check if restaurant offers the requested cuisine (case-insensitive substring match).
        """
        if not requested_cuisine or not requested_cuisine.strip():
            return True

        target = requested_cuisine.strip().lower()
        for cuisine in restaurant.cuisines:
            if target in cuisine.lower() or cuisine.lower() in target:
                return True

        return False

    @staticmethod
    def matches_budget(restaurant: Restaurant, user_budget: str) -> bool:
        """Check if restaurant cost tier matches requested budget tier."""
        if not user_budget:
            return True
        return restaurant.budget_tier.lower() == user_budget.strip().lower()

    def apply_hard_filters(
        self,
        restaurants: List[Restaurant],
        preferences: UserPreferences,
        ignore_rating: bool = False,
        ignore_budget: bool = False,
        ignore_cuisine: bool = False,
    ) -> List[Restaurant]:
        """
        Apply filter pipeline in order:
        1. Location (always required)
        2. Rating (unless ignored during relaxation)
        3. Cuisine (unless ignored during relaxation)
        4. Budget (unless ignored during relaxation)
        """
        results: List[Restaurant] = []

        for r in restaurants:
            # 1. Location match (mandatory)
            if not self.matches_location(r, preferences.location):
                continue

            # 2. Rating match
            if not ignore_rating and not self.matches_rating(r, preferences.min_rating):
                continue

            # 3. Cuisine match
            if not ignore_cuisine and preferences.cuisine and not self.matches_cuisine(r, preferences.cuisine):
                continue

            # 4. Budget match
            if not ignore_budget and not self.matches_budget(r, preferences.budget):
                continue

            results.append(r)

        return results

    def relax_filters_waterfall(
        self,
        restaurants: List[Restaurant],
        preferences: UserPreferences,
    ) -> Tuple[List[Restaurant], List[str]]:
        """
        Sequential filter relaxation waterfall (docs/edge-case.md §4.1):
        Step 1: Relax min_rating
        Step 2: Relax budget
        Step 3: Relax cuisine
        Note: Location is strictly non-negotiable (docs/edge-case.md §4.2).
        """
        relaxed_steps: List[str] = []

        # Step 1: Drop/relax min_rating threshold
        if preferences.min_rating > 0.0:
            relaxed_steps.append("min_rating")
            matched = self.apply_hard_filters(restaurants, preferences, ignore_rating=True)
            if matched:
                logger.info(f"Filter relaxation Step 1 succeeded (relaxed min_rating, found {len(matched)})")
                return matched, relaxed_steps

        # Step 2: Relax budget tier
        relaxed_steps.append("budget")
        matched = self.apply_hard_filters(
            restaurants, preferences, ignore_rating=True, ignore_budget=True
        )
        if matched:
            logger.info(f"Filter relaxation Step 2 succeeded (relaxed min_rating + budget, found {len(matched)})")
            return matched, relaxed_steps

        # Step 3: Relax cuisine
        if preferences.cuisine:
            relaxed_steps.append("cuisine")
            matched = self.apply_hard_filters(
                restaurants,
                preferences,
                ignore_rating=True,
                ignore_budget=True,
                ignore_cuisine=True,
            )
            if matched:
                logger.info(f"Filter relaxation Step 3 succeeded (relaxed all filters except location, found {len(matched)})")
                return matched, relaxed_steps

        # No restaurants found in location even after full relaxation
        return [], relaxed_steps

    @staticmethod
    def _normalize_brand_name(name: str) -> str:
        """Normalize restaurant brand name for franchise deduplication."""
        base = name.strip().lower()
        # Remove common branch designations e.g. "Domino's Pizza - Koramangala" -> "domino's pizza"
        base = re.split(r"[-–—,:]", base)[0].strip()
        return base

    def select_candidates(
        self,
        filtered_restaurants: List[Restaurant],
        max_n: Optional[int] = None,
        max_per_brand: int = 1,
    ) -> List[Restaurant]:
        """
        Rank candidates deterministically by (rating DESC, votes DESC, name ASC)
        and apply brand and exact outlet deduplication (docs/edge-case.md §2.7 and §4.6).
        """
        limit = max_n if max_n is not None else self.max_candidates

        # Multi-key deterministic sorting
        sorted_restaurants = sorted(
            filtered_restaurants,
            key=lambda r: (r.rating, r.votes or 0, -(len(r.name))),
            reverse=True,
        )

        candidates: List[Restaurant] = []
        brand_counts: Dict[str, int] = {}
        seen_entities: Set[Tuple[str, str]] = set()

        for r in sorted_restaurants:
            entity_key = (r.name.strip().lower(), (r.locality or r.location).strip().lower())
            if entity_key in seen_entities:
                continue
            seen_entities.add(entity_key)

            brand = self._normalize_brand_name(r.name)
            count = brand_counts.get(brand, 0)
            if count < max_per_brand:
                candidates.append(r)
                brand_counts[brand] = count + 1

            if len(candidates) >= limit:
                break

        return candidates

    def filter(
        self,
        restaurants: List[Restaurant],
        preferences: UserPreferences,
        max_candidates: Optional[int] = None,
    ) -> FilterResult:
        """
        Execute end-to-end filtering pipeline:
        1. Apply hard filters.
        2. If 0 matches, run relaxation waterfall.
        3. Select and deduplicate top candidates up to MAX_CANDIDATES.
        """
        limit = max_candidates or self.max_candidates

        # 1. Apply hard filters
        matched = self.apply_hard_filters(restaurants, preferences)
        filters_relaxed: List[str] = []
        is_relaxed = False

        # 2. Relax if 0 matches found
        if not matched:
            matched, filters_relaxed = self.relax_filters_waterfall(restaurants, preferences)
            is_relaxed = len(filters_relaxed) > 0

        total_matched = len(matched)

        # 3. Select top candidates
        candidates = self.select_candidates(matched, max_n=limit)

        return FilterResult(
            candidates=candidates,
            total_matched=total_matched,
            filters_relaxed=filters_relaxed,
            is_relaxed=is_relaxed,
        )
