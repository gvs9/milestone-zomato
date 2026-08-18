"""
LLM Response Parser and Anti-Hallucination Guard.
Validates structured JSON output against the candidate whitelist and dataset ground truth.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from src.models.preferences import UserPreferences
from src.models.recommendation import Recommendation, RecommendationResponse
from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


def extract_json_from_text(raw_text: str) -> Dict[str, Any]:
    """
    Robust JSON extraction from LLM text responses.
    Handles raw JSON, markdown code blocks (```json ... ```), and surrounded text.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Empty LLM response received.")

    text = raw_text.strip()

    # 1. Strip markdown code fences if present
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            text = match.group(1).strip()

    # 2. Extract outermost JSON object { ... }
    brace_match = re.search(r"\{[\s\S]*\}", text)
    if brace_match:
        text = brace_match.group(0)

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse valid JSON from LLM response: {exc}") from exc


def generate_fallback_explanation(restaurant: Restaurant, preferences: UserPreferences) -> str:
    """
    Generate a high-quality deterministic explanation based on matched restaurant attributes
    (see docs/edge-case.md §8.3).
    """
    reasons = []

    # Cuisine match
    if preferences.cuisine and any(
        preferences.cuisine.lower() in c.lower() for c in restaurant.cuisines
    ):
        reasons.append(f"offers authentic {preferences.cuisine} cuisine")
    elif restaurant.cuisines:
        reasons.append(f"known for {', '.join(restaurant.cuisines[:2])}")

    # Rating highlight
    if restaurant.rating >= 4.5:
        reasons.append(f"boasts an outstanding {restaurant.rating}★ rating")
    elif restaurant.rating >= 4.0:
        reasons.append(f"has a strong {restaurant.rating}★ customer rating")

    # Budget match
    if restaurant.budget_tier == preferences.budget:
        reasons.append(f"fits your {preferences.budget} budget preference ({restaurant.cost_for_two})")

    locality = restaurant.locality or restaurant.location
    reason_str = ", ".join(reasons) if reasons else "matches your filter criteria"
    return f"Top-rated dining spot in {locality} that {reason_str}."


class ResponseParser:
    """
    Validates, sanitizes, and enriches LLM responses with anti-hallucination guarantees.
    """

    @classmethod
    def match_candidate(
        cls, restaurant_name: str, candidates: List[Restaurant]
    ) -> Optional[Restaurant]:
        """
        Match an LLM-returned restaurant name to the verified candidate list.
        Supports exact match and substring/fuzzy match.
        """
        if not restaurant_name or not candidates:
            return None

        target = restaurant_name.strip().lower()

        # 1. Exact match
        for c in candidates:
            if c.name.strip().lower() == target:
                return c

        # 2. Substring match (e.g. "Truffles" vs "Truffles - Koramangala")
        for c in candidates:
            c_name = c.name.strip().lower()
            if target in c_name or c_name in target:
                return c

        # 3. Clean punctuation match
        clean_target = re.sub(r"[^\w\s]", "", target)
        for c in candidates:
            clean_c = re.sub(r"[^\w\s]", "", c.name.lower())
            if clean_target == clean_c or clean_target in clean_c or clean_c in clean_target:
                return c

        return None

    @classmethod
    def parse_and_validate(
        cls,
        raw_llm_output: str,
        candidates: List[Restaurant],
        preferences: UserPreferences,
        filters_relaxed: Optional[List[str]] = None,
        target_count: int = 5,
    ) -> RecommendationResponse:
        """
        Parse raw LLM response, perform anti-hallucination whitelist verification,
        and guarantee dataset ground truth for numeric fields.
        """
        data = extract_json_from_text(raw_llm_output)
        summary = data.get("summary")
        raw_recs = data.get("recommendations", [])

        valid_recommendations: List[Recommendation] = []
        seen_names = set()

        for idx, item in enumerate(raw_recs):
            if not isinstance(item, dict):
                continue

            raw_name = str(item.get("restaurant_name", "")).strip()
            matched = cls.match_candidate(raw_name, candidates)

            if matched:
                if matched.name.lower() in seen_names:
                    continue  # Deduplicate
                seen_names.add(matched.name.lower())

                # Ground-truth enrichment from dataset (docs/edge-case.md §7.3, §7.4)
                explanation = str(item.get("explanation", "")).strip()
                if not explanation:
                    explanation = generate_fallback_explanation(matched, preferences)

                rec = Recommendation(
                    restaurant_name=matched.name,
                    rank=len(valid_recommendations) + 1,  # Sequential rank
                    cuisine=", ".join(matched.cuisines),
                    rating=matched.rating,
                    estimated_cost=matched.cost_for_two,
                    explanation=explanation,
                )
                valid_recommendations.append(rec)
            else:
                logger.warning(f"Rejected hallucinated restaurant from LLM output: '{raw_name}'")

            if len(valid_recommendations) >= target_count:
                break

        # If LLM returned fewer than 3 valid items or failed whitelist, backfill from candidates
        if len(valid_recommendations) < min(3, len(candidates)):
            logger.info("Backfilling recommendations from candidate list...")
            for c in candidates:
                if c.name.lower() not in seen_names:
                    seen_names.add(c.name.lower())
                    valid_recommendations.append(
                        Recommendation(
                            restaurant_name=c.name,
                            rank=len(valid_recommendations) + 1,
                            cuisine=", ".join(c.cuisines),
                            rating=c.rating,
                            estimated_cost=c.cost_for_two,
                            explanation=generate_fallback_explanation(c, preferences),
                        )
                    )
                if len(valid_recommendations) >= target_count:
                    break

        if not summary:
            cuisine_part = f"{preferences.cuisine} " if preferences.cuisine else ""
            summary = (
                f"Here are top-ranked {cuisine_part}restaurants in {preferences.location} "
                f"matching your {preferences.budget} budget."
            )

        return RecommendationResponse(
            summary=summary,
            recommendations=valid_recommendations,
            filters_relaxed=filters_relaxed,
            is_fallback=False,
            total_candidates=len(candidates),
        )

    @classmethod
    def generate_fallback_response(
        cls,
        candidates: List[Restaurant],
        preferences: UserPreferences,
        filters_relaxed: Optional[List[str]] = None,
        target_count: int = 5,
    ) -> RecommendationResponse:
        """
        Generate a complete deterministic fallback response when LLM inference is unavailable
        (docs/edge-case.md §8).
        """
        selected = candidates[:target_count]
        recs = [
            Recommendation(
                restaurant_name=r.name,
                rank=idx + 1,
                cuisine=", ".join(r.cuisines),
                rating=r.rating,
                estimated_cost=r.cost_for_two,
                explanation=generate_fallback_explanation(r, preferences),
            )
            for idx, r in enumerate(selected)
        ]

        cuisine_str = f"{preferences.cuisine} " if preferences.cuisine else ""
        summary = (
            f"Showing top-rated {cuisine_str}restaurants in {preferences.location} "
            f"for {preferences.budget} budget (Sorted by rating & popularity)."
        )

        return RecommendationResponse(
            summary=summary,
            recommendations=recs,
            filters_relaxed=filters_relaxed,
            is_fallback=True,
            total_candidates=len(candidates),
        )
