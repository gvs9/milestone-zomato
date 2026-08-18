"""
Integration and End-to-End tests for RecommendationService (Phase 3).
Tests recommendation orchestration, LLM integration with mocks, and fallback paths.
"""

import json
import unittest
from typing import List

from src.data.loader import DatasetLoader
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.filter import RestaurantFilter
from src.services.llm_client import LLMInferenceError, LLMProvider
from src.services.recommendation import RecommendationService


class MockSuccessfulLLMClient(LLMProvider):
    """Mock LLM client returning valid structured JSON recommendations."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return json.dumps({
            "summary": "Here are the best Italian restaurants in Bangalore matching your medium budget.",
            "recommendations": [
                {
                    "restaurant_name": "Truffles",
                    "rank": 1,
                    "explanation": "Top-rated spot with delicious Italian pasta and burgers within budget.",
                },
                {
                    "restaurant_name": "Toit",
                    "rank": 2,
                    "explanation": "Iconic venue renowned for authentic wood-fired Italian pizzas.",
                },
            ]
        })


class MockFailingLLMClient(LLMProvider):
    """Mock LLM client simulating rate limit or network timeout errors."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise LLMInferenceError("Groq 429 Too Many Requests: Rate limit exceeded.")


class TestRecommendationService(unittest.TestCase):
    """Test suite for RecommendationService."""

    def setUp(self):
        self.sample_restaurants = [
            Restaurant(
                name="Truffles",
                location="Bangalore",
                city="Bangalore",
                locality="Koramangala",
                cuisines=["Italian", "American", "Burger"],
                rating=4.6,
                cost_for_two="₹800 for two",
                budget_tier="medium",
                votes=14000,
            ),
            Restaurant(
                name="Toit",
                location="Bangalore",
                city="Bangalore",
                locality="Indiranagar",
                cuisines=["Italian", "Pizza", "European"],
                rating=4.7,
                cost_for_two="₹1500 for two",
                budget_tier="medium",
                votes=16000,
            ),
            Restaurant(
                name="Vidyarthi Bhavan",
                location="Bangalore",
                city="Bangalore",
                locality="Basavanagudi",
                cuisines=["South Indian"],
                rating=4.4,
                cost_for_two="₹200 for two",
                budget_tier="low",
                votes=8000,
            ),
        ]

        # Mock loader returning sample dataset
        class MockLoader:
            def load(self):
                return self.restaurants
            def __init__(self, data):
                self.restaurants = data

        self.mock_loader = MockLoader(self.sample_restaurants)
        self.preferences = UserPreferences(
            location="Bangalore",
            budget="medium",
            cuisine="Italian",
            min_rating=4.0,
        )

    def test_recommendation_with_mock_llm_success(self):
        """Verify successful end-to-end recommendation flow with LLM."""
        service = RecommendationService(
            loader=self.mock_loader,  # type: ignore
            filter_service=RestaurantFilter(),
            llm_client=MockSuccessfulLLMClient(),
        )

        response = service.recommend(self.preferences, target_count=2)

        self.assertFalse(response.is_fallback)
        self.assertEqual(len(response.recommendations), 2)
        self.assertEqual(response.recommendations[0].restaurant_name, "Truffles")
        self.assertEqual(response.recommendations[1].restaurant_name, "Toit")
        self.assertEqual(response.recommendations[0].rank, 1)
        self.assertEqual(response.recommendations[1].rank, 2)
        self.assertIn("Italian", response.summary)

    def test_recommendation_automatic_fallback_on_llm_failure(self):
        """Verify automatic graceful degradation to deterministic fallback when LLM fails."""
        service = RecommendationService(
            loader=self.mock_loader,  # type: ignore
            filter_service=RestaurantFilter(),
            llm_client=MockFailingLLMClient(),
        )

        response = service.recommend(self.preferences, target_count=2)

        # Fallback should activate without raising exceptions to user
        self.assertTrue(response.is_fallback)
        self.assertEqual(len(response.recommendations), 2)
        # Fallback sorts by rating: Toit (4.7) then Truffles (4.6)
        self.assertEqual(response.recommendations[0].restaurant_name, "Toit")
        self.assertEqual(response.recommendations[1].restaurant_name, "Truffles")

    def test_recommendation_unknown_location_returns_empty(self):
        """Verify unknown location returns empty recommendations list cleanly."""
        service = RecommendationService(
            loader=self.mock_loader,  # type: ignore
            filter_service=RestaurantFilter(),
            llm_client=MockSuccessfulLLMClient(),
        )
        unknown_prefs = UserPreferences(location="Paris", budget="medium")
        response = service.recommend(unknown_prefs)

        self.assertEqual(len(response.recommendations), 0)
        self.assertIn("No restaurants found", response.summary)


if __name__ == "__main__":
    unittest.main()
