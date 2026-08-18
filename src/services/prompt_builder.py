"""
Prompt Builder Service.
Constructs structured system and user prompts with sandboxing and schema enforcement.
"""

import json
from typing import Any, Dict, List

from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant


class PromptBuilder:
    """Builds prompts for Groq LLM inference with anti-injection protections."""

    SYSTEM_PROMPT: str = (
        "You are an expert AI restaurant recommendation assistant for a Zomato-like platform.\n"
        "Your task is to rank and explain restaurant recommendations strictly based on user preferences "
        "and a provided verified list of candidate restaurants.\n\n"
        "CRITICAL RULES:\n"
        "1. You MUST ONLY recommend restaurants from the provided 'Candidate Restaurants' list.\n"
        "2. NEVER fabricate, invent, or recommend any restaurant not in the candidate list.\n"
        "3. Rank the restaurants in order of best match to the user's preferences.\n"
        "4. For each restaurant, provide a concise 1-2 sentence explanation connecting its features "
        "(cuisine, rating, cost, ambiance, specialties) to the user's specific request.\n"
        "5. Output MUST be valid JSON adhering strictly to the required schema with no extra text outside the JSON."
    )

    @classmethod
    def build_system_prompt(cls) -> str:
        """Return canonical system prompt."""
        return cls.SYSTEM_PROMPT

    @classmethod
    def build_user_prompt(
        cls,
        preferences: UserPreferences,
        candidates: List[Restaurant],
        target_count: int = 5,
    ) -> str:
        """
        Build structured user prompt containing user preferences and candidate JSON.
        
        Args:
            preferences: User search preferences.
            candidates: Verified list of candidate restaurants.
            target_count: Desired number of top recommendations.
            
        Returns:
            Formatted prompt string.
        """
        count = min(target_count, len(candidates)) if candidates else 0

        # Serialize candidate restaurants into compact format (docs/edge-case.md §5.1, §5.2)
        candidates_payload: List[Dict[str, Any]] = [
            {
                "name": r.name,
                "cuisines": ", ".join(r.cuisines),
                "rating": r.rating,
                "cost": r.cost_for_two,
                "budget_tier": r.budget_tier,
                "locality": r.locality or r.location,
                "votes": r.votes,
            }
            for r in candidates
        ]
        candidates_json = json.dumps(candidates_payload, ensure_ascii=False, indent=2)

        user_notes = (
            preferences.additional_preferences
            if preferences.additional_preferences
            else "None provided"
        )

        prompt = (
            f"### USER PREFERENCES\n"
            f"- Location: {preferences.location}\n"
            f"- Budget Tier: {preferences.budget}\n"
            f"- Cuisine: {preferences.cuisine or 'Any / All'}\n"
            f"- Minimum Rating: {preferences.min_rating}★\n"
            f"- Additional Notes: <user_notes>{user_notes}</user_notes>\n\n"
            f"### CANDIDATE RESTAURANTS (VERIFIED DATASET - CHOOSE FROM HERE ONLY)\n"
            f"```json\n"
            f"{candidates_json}\n"
            f"```\n\n"
            f"### INSTRUCTIONS\n"
            f"Select the top {count} best restaurants from the Candidate Restaurants above.\n"
            f"Return a single JSON object with this exact schema:\n"
            f"{{\n"
            f'  "summary": "Brief 1-2 sentence overview of your recommendations based on the preferences",\n'
            f'  "recommendations": [\n'
            f"    {{\n"
            f'      "restaurant_name": "Exact Name of Restaurant from Candidates",\n'
            f'      "rank": 1,\n'
            f'      "cuisine": "Cuisine string",\n'
            f'      "rating": 4.5,\n'
            f'      "estimated_cost": "₹... for two",\n'
            f'      "explanation": "Why this matches the user preferences..."\n'
            f"    }}\n"
            f"  ]\n"
            f"}}"
        )
        return prompt
