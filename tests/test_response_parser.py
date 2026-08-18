"""
Unit tests for Response Parser and Anti-Hallucination Guard (Phase 3).
"""

import json
import unittest
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.response_parser import (
    ResponseParser,
    extract_json_from_text,
    generate_fallback_explanation,
)


class TestResponseParser(unittest.TestCase):
    """Test suite for ResponseParser and fallback generator."""

    def setUp(self):
        self.preferences = UserPreferences(
            location="Bangalore",
            budget="medium",
            cuisine="Italian",
            min_rating=4.0,
        )
        self.candidates = [
            Restaurant(
                name="Truffles",
                location="Bangalore",
                cuisines=["Italian", "American", "Burger"],
                rating=4.6,
                cost_for_two="₹800 for two",
                budget_tier="medium",
                locality="Koramangala",
                votes=14000,
            ),
            Restaurant(
                name="Toit",
                location="Bangalore",
                cuisines=["Italian", "Pizza", "European"],
                rating=4.7,
                cost_for_two="₹1500 for two",
                budget_tier="medium",
                locality="Indiranagar",
                votes=16000,
            ),
            Restaurant(
                name="Onesta",
                location="Bangalore",
                cuisines=["Pizza", "Italian", "Desserts"],
                rating=4.3,
                cost_for_two="₹600 for two",
                budget_tier="medium",
                locality="Koramangala",
                votes=6100,
            ),
        ]

    def test_extract_json_from_markdown_code_block(self):
        """Verify extracting JSON enclosed in markdown code fences (docs/edge-case.md §7.1)."""
        raw_text = """
        Here are the recommendations:
        ```json
        {
          "summary": "Great Italian spots in Bangalore.",
          "recommendations": [
            {
              "restaurant_name": "Truffles",
              "rank": 1,
              "explanation": "Great burgers and pasta."
            }
          ]
        }
        ```
        Hope you enjoy!
        """
        data = extract_json_from_text(raw_text)
        self.assertEqual(data["summary"], "Great Italian spots in Bangalore.")
        self.assertEqual(len(data["recommendations"]), 1)

    def test_parse_and_validate_anti_hallucination(self):
        """Verify hallucinated restaurants are dropped and candidate truth is preserved (docs/edge-case.md §7.4)."""
        raw_llm_output = json.dumps({
            "summary": "Top choices for you",
            "recommendations": [
                {
                    "restaurant_name": "Truffles",
                    "rank": 1,
                    "rating": 5.0,  # Modified rating by LLM
                    "explanation": "Famous for burgers and Italian dishes.",
                },
                {
                    "restaurant_name": "NonExistentFakeCafe",  # Hallucination
                    "rank": 2,
                    "explanation": "Made up restaurant.",
                },
                {
                    "restaurant_name": "Toit",
                    "rank": 3,
                    "explanation": "Excellent microbrewery and Italian pizza.",
                },
            ]
        })

        response = ResponseParser.parse_and_validate(
            raw_llm_output=raw_llm_output,
            candidates=self.candidates,
            preferences=self.preferences,
            target_count=3,
        )

        names = [r.restaurant_name for r in response.recommendations]
        self.assertIn("Truffles", names)
        self.assertIn("Toit", names)
        self.assertNotIn("NonExistentFakeCafe", names)

        # Verify dataset ground truth preserved
        truffles = next(r for r in response.recommendations if r.restaurant_name == "Truffles")
        self.assertEqual(truffles.rating, 4.6)  # Corrected to real dataset rating, not 5.0
        self.assertEqual(truffles.estimated_cost, "₹800 for two")

        # Verify sequential ranks
        self.assertEqual(response.recommendations[0].rank, 1)
        self.assertEqual(response.recommendations[1].rank, 2)

    def test_deterministic_fallback_generation(self):
        """Verify fallback response generation when LLM is offline (docs/edge-case.md §8)."""
        response = ResponseParser.generate_fallback_response(
            candidates=self.candidates,
            preferences=self.preferences,
            target_count=2,
        )

        self.assertTrue(response.is_fallback)
        self.assertEqual(len(response.recommendations), 2)
        self.assertEqual(response.recommendations[0].restaurant_name, "Truffles")
        self.assertIn("4.6★", response.recommendations[0].explanation)
        self.assertIn("medium budget", response.recommendations[0].explanation)


if __name__ == "__main__":
    unittest.main()
