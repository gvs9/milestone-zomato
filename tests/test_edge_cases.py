"""
Comprehensive edge-case and error scenario tests for Phase 5 backend hardening.
Covers error scenarios from architecture §14 and edge-case.md, including:
- JSON extraction edge cases
- Empty/malformed LLM responses
- Duplicate restaurant deduplication in parser
- Candidate backfill when LLM returns too few
- Fallback explanation quality
- Preference validation boundaries
- LLM client configuration checks
- Recommendation model serialization round-trips
"""

import json
import unittest
from unittest.mock import MagicMock

from src.models.preferences import UserPreferences
from src.models.recommendation import Recommendation, RecommendationResponse
from src.models.restaurant import Restaurant
from src.services.filter import RestaurantFilter, FilterResult
from src.services.llm_client import GroqLLMClient, LLMInferenceError, LLMProvider
from src.services.prompt_builder import PromptBuilder
from src.services.recommendation import RecommendationService
from src.services.response_parser import (
    ResponseParser,
    extract_json_from_text,
    generate_fallback_explanation,
)


# ────────────────────────────────────────────────────────────────
#  Test Fixtures
# ────────────────────────────────────────────────────────────────

def _sample_restaurants():
    return [
        Restaurant(
            name="Truffles", location="Bangalore", city="Bangalore",
            locality="Koramangala", cuisines=["Italian", "American"],
            rating=4.6, cost_for_two="₹800 for two", budget_tier="medium", votes=14000,
        ),
        Restaurant(
            name="Toit", location="Bangalore", city="Bangalore",
            locality="Indiranagar", cuisines=["Italian", "Pizza"],
            rating=4.7, cost_for_two="₹1500 for two", budget_tier="medium", votes=16000,
        ),
        Restaurant(
            name="Vidyarthi Bhavan", location="Bangalore", city="Bangalore",
            locality="Basavanagudi", cuisines=["South Indian"],
            rating=4.4, cost_for_two="₹200 for two", budget_tier="low", votes=8000,
        ),
        Restaurant(
            name="Meghana Foods", location="Bangalore", city="Bangalore",
            locality="Koramangala", cuisines=["Biryani", "Andhra"],
            rating=4.5, cost_for_two="₹500 for two", budget_tier="medium", votes=12000,
        ),
    ]


class MockLoader:
    def __init__(self, data):
        self.restaurants = data
    def load(self):
        return self.restaurants


class MockEmptyLoader:
    def load(self):
        return []


# ────────────────────────────────────────────────────────────────
#  JSON Extraction Edge Cases
# ────────────────────────────────────────────────────────────────

class TestJSONExtractionEdgeCases(unittest.TestCase):
    """Edge cases for extract_json_from_text (edge-case.md §7.1)."""

    def test_raw_json_without_fences(self):
        """Plain JSON string without markdown wrapping."""
        raw = '{"summary": "ok", "recommendations": []}'
        result = extract_json_from_text(raw)
        self.assertEqual(result["summary"], "ok")

    def test_json_with_surrounding_text(self):
        """JSON embedded in conversational text."""
        raw = 'Sure! Here are your results:\n{"summary": "Top picks", "recommendations": []}\nEnjoy your meal!'
        result = extract_json_from_text(raw)
        self.assertEqual(result["summary"], "Top picks")

    def test_json_with_code_fence_no_language_tag(self):
        """JSON inside ``` fences without 'json' language specifier."""
        raw = '```\n{"summary": "test", "recommendations": []}\n```'
        result = extract_json_from_text(raw)
        self.assertEqual(result["summary"], "test")

    def test_empty_string_raises_value_error(self):
        """Empty input should raise ValueError."""
        with self.assertRaises(ValueError):
            extract_json_from_text("")

    def test_whitespace_only_raises_value_error(self):
        """Whitespace-only input should raise ValueError."""
        with self.assertRaises(ValueError):
            extract_json_from_text("   \n\t  ")

    def test_no_json_in_text_raises_value_error(self):
        """Text with no JSON object should raise ValueError."""
        with self.assertRaises(ValueError):
            extract_json_from_text("I cannot help with that request.")

    def test_malformed_json_raises_value_error(self):
        """Malformed JSON should raise ValueError."""
        with self.assertRaises(ValueError):
            extract_json_from_text('{"summary": "broken",}')


# ────────────────────────────────────────────────────────────────
#  Response Parser Edge Cases
# ────────────────────────────────────────────────────────────────

class TestResponseParserEdgeCases(unittest.TestCase):
    """Extended parser tests for edge-case.md §7 scenarios."""

    def setUp(self):
        self.prefs = UserPreferences(location="Bangalore", budget="medium", cuisine="Italian", min_rating=4.0)
        self.candidates = _sample_restaurants()[:3]

    def test_all_hallucinated_triggers_backfill(self):
        """When LLM returns ONLY hallucinated names, backfill from candidates (§7.4)."""
        raw = json.dumps({
            "summary": "Great choices",
            "recommendations": [
                {"restaurant_name": "FakePlace1", "rank": 1, "explanation": "Made up"},
                {"restaurant_name": "FakePlace2", "rank": 2, "explanation": "Also fake"},
            ]
        })
        response = ResponseParser.parse_and_validate(
            raw_llm_output=raw, candidates=self.candidates,
            preferences=self.prefs, target_count=3,
        )
        # Should backfill from candidates since 0 valid recs < min(3, len(candidates))
        self.assertGreater(len(response.recommendations), 0)
        for rec in response.recommendations:
            self.assertIn(rec.restaurant_name, [c.name for c in self.candidates])

    def test_duplicate_restaurant_deduplication(self):
        """LLM returning same restaurant twice should be deduplicated."""
        raw = json.dumps({
            "summary": "Picks",
            "recommendations": [
                {"restaurant_name": "Truffles", "rank": 1, "explanation": "Great"},
                {"restaurant_name": "Truffles", "rank": 2, "explanation": "Also great"},
                {"restaurant_name": "Toit", "rank": 3, "explanation": "Good"},
            ]
        })
        response = ResponseParser.parse_and_validate(
            raw_llm_output=raw, candidates=self.candidates,
            preferences=self.prefs, target_count=3,
        )
        names = [r.restaurant_name for r in response.recommendations]
        self.assertEqual(names.count("Truffles"), 1)

    def test_missing_summary_generates_default(self):
        """When LLM omits summary, parser should generate a default."""
        raw = json.dumps({
            "recommendations": [
                {"restaurant_name": "Truffles", "rank": 1, "explanation": "Good"}
            ]
        })
        response = ResponseParser.parse_and_validate(
            raw_llm_output=raw, candidates=self.candidates,
            preferences=self.prefs, target_count=1,
        )
        self.assertIsNotNone(response.summary)
        self.assertIn("Bangalore", response.summary)

    def test_empty_recommendations_list_triggers_backfill(self):
        """When LLM returns empty recommendations array, candidates should be backfilled."""
        raw = json.dumps({"summary": "Nothing matched", "recommendations": []})
        response = ResponseParser.parse_and_validate(
            raw_llm_output=raw, candidates=self.candidates,
            preferences=self.prefs, target_count=2,
        )
        self.assertGreater(len(response.recommendations), 0)

    def test_substring_name_matching(self):
        """Parser should match partial restaurant names like 'Truffles' → 'Truffles'."""
        raw = json.dumps({
            "summary": "Best picks",
            "recommendations": [
                {"restaurant_name": "Truffles - Koramangala", "rank": 1, "explanation": "Top"},
            ]
        })
        response = ResponseParser.parse_and_validate(
            raw_llm_output=raw, candidates=self.candidates,
            preferences=self.prefs, target_count=1,
        )
        self.assertEqual(len(response.recommendations), 1)
        self.assertEqual(response.recommendations[0].restaurant_name, "Truffles")


# ────────────────────────────────────────────────────────────────
#  Fallback Explanation Quality
# ────────────────────────────────────────────────────────────────

class TestFallbackExplanationQuality(unittest.TestCase):
    """Verify deterministic explanations are informative (edge-case.md §8.3)."""

    def test_explanation_mentions_cuisine_when_matched(self):
        r = Restaurant(name="X", location="Y", cuisines=["Italian"], rating=4.5,
                       cost_for_two="₹800", budget_tier="medium", locality="Z")
        prefs = UserPreferences(location="Y", budget="medium", cuisine="Italian")
        explanation = generate_fallback_explanation(r, prefs)
        self.assertIn("Italian", explanation)

    def test_explanation_mentions_rating_for_high_rated(self):
        r = Restaurant(name="X", location="Y", cuisines=["Indian"], rating=4.8,
                       cost_for_two="₹500", budget_tier="low", locality="Z")
        prefs = UserPreferences(location="Y", budget="low")
        explanation = generate_fallback_explanation(r, prefs)
        self.assertIn("4.8", explanation)
        self.assertIn("outstanding", explanation)

    def test_explanation_mentions_budget_when_matched(self):
        r = Restaurant(name="X", location="Y", cuisines=["Indian"], rating=4.0,
                       cost_for_two="₹500", budget_tier="medium", locality="Z")
        prefs = UserPreferences(location="Y", budget="medium")
        explanation = generate_fallback_explanation(r, prefs)
        self.assertIn("medium budget", explanation)

    def test_explanation_for_no_cuisine_match(self):
        """When user didn't specify cuisine, explanation should mention restaurant's own."""
        r = Restaurant(name="X", location="Y", cuisines=["Korean", "Japanese"], rating=4.2,
                       cost_for_two="₹900", budget_tier="medium", locality="Z")
        prefs = UserPreferences(location="Y", budget="medium")
        explanation = generate_fallback_explanation(r, prefs)
        self.assertIn("Korean", explanation)


# ────────────────────────────────────────────────────────────────
#  Preference Validation Edge Cases
# ────────────────────────────────────────────────────────────────

class TestPreferenceValidationEdgeCases(unittest.TestCase):
    """Preference edge cases from edge-case.md §3."""

    def test_whitespace_location_is_trimmed(self):
        prefs = UserPreferences(location="  Bangalore  ", budget="medium")
        self.assertEqual(prefs.location, "Bangalore")

    def test_empty_string_location_raises(self):
        with self.assertRaises(ValueError):
            UserPreferences(location="", budget="medium")

    def test_whitespace_only_location_raises(self):
        with self.assertRaises(ValueError):
            UserPreferences(location="   ", budget="medium")

    def test_budget_case_insensitive(self):
        prefs = UserPreferences(location="X", budget="MEDIUM")
        self.assertEqual(prefs.budget, "medium")

    def test_invalid_budget_raises(self):
        with self.assertRaises(ValueError):
            UserPreferences(location="X", budget="ultra")

    def test_min_rating_boundary_zero(self):
        prefs = UserPreferences(location="X", budget="low", min_rating=0.0)
        self.assertEqual(prefs.min_rating, 0.0)

    def test_min_rating_boundary_five(self):
        prefs = UserPreferences(location="X", budget="low", min_rating=5.0)
        self.assertEqual(prefs.min_rating, 5.0)

    def test_min_rating_above_five_raises(self):
        with self.assertRaises(ValueError):
            UserPreferences(location="X", budget="low", min_rating=5.1)

    def test_min_rating_negative_raises(self):
        with self.assertRaises(ValueError):
            UserPreferences(location="X", budget="low", min_rating=-0.1)

    def test_additional_preferences_capped_at_300(self):
        long_text = "a" * 500
        prefs = UserPreferences(location="X", budget="low", additional_preferences=long_text)
        self.assertEqual(len(prefs.additional_preferences), 300)

    def test_empty_cuisine_normalized_to_none(self):
        prefs = UserPreferences(location="X", budget="low", cuisine="   ")
        self.assertIsNone(prefs.cuisine)


# ────────────────────────────────────────────────────────────────
#  Recommendation Model Serialization
# ────────────────────────────────────────────────────────────────

class TestRecommendationSerialization(unittest.TestCase):
    """Round-trip serialization for recommendation models."""

    def test_recommendation_round_trip(self):
        rec = Recommendation(
            restaurant_name="Toit", rank=1, cuisine="Italian, Pizza",
            rating=4.7, estimated_cost="₹1500 for two",
            explanation="Great craft beer and pizza.",
        )
        d = rec.to_dict()
        restored = Recommendation.from_dict(d)
        self.assertEqual(restored.restaurant_name, "Toit")
        self.assertEqual(restored.rank, 1)
        self.assertEqual(restored.rating, 4.7)

    def test_response_round_trip(self):
        resp = RecommendationResponse(
            summary="Test summary",
            recommendations=[
                Recommendation("A", 1, "Italian", 4.5, "₹800", "Good"),
                Recommendation("B", 2, "Indian", 4.3, "₹500", "Nice"),
            ],
            filters_relaxed=["budget"],
            is_fallback=True,
            total_candidates=10,
        )
        d = resp.to_dict()
        restored = RecommendationResponse.from_dict(d)
        self.assertEqual(restored.summary, "Test summary")
        self.assertEqual(len(restored.recommendations), 2)
        self.assertTrue(restored.is_fallback)
        self.assertEqual(restored.filters_relaxed, ["budget"])

    def test_response_from_dict_with_missing_fields(self):
        data = {"recommendations": []}
        restored = RecommendationResponse.from_dict(data)
        self.assertIsNone(restored.summary)
        self.assertEqual(len(restored.recommendations), 0)
        self.assertFalse(restored.is_fallback)


# ────────────────────────────────────────────────────────────────
#  LLM Client Configuration
# ────────────────────────────────────────────────────────────────

class TestLLMClientConfiguration(unittest.TestCase):
    """Verify GroqLLMClient configuration edge cases."""

    @unittest.mock.patch("src.services.llm_client.settings")
    def test_empty_api_key_not_configured(self, mock_settings):
        mock_settings.groq_api_key = ""
        mock_settings.groq_model = "test-model"
        client = GroqLLMClient(api_key="")
        self.assertFalse(client.is_configured)

    def test_placeholder_api_key_not_configured(self):
        client = GroqLLMClient(api_key="gsk_your_groq_api_key_here")
        self.assertFalse(client.is_configured)

    def test_short_api_key_not_configured(self):
        client = GroqLLMClient(api_key="abc")
        self.assertFalse(client.is_configured)

    def test_valid_api_key_is_configured(self):
        client = GroqLLMClient(api_key="gsk_abc123def456ghi789")
        self.assertTrue(client.is_configured)

    @unittest.mock.patch("src.services.llm_client.settings")
    def test_unconfigured_client_raises_on_generate(self, mock_settings):
        mock_settings.groq_api_key = ""
        mock_settings.groq_model = "test-model"
        client = GroqLLMClient(api_key="")
        with self.assertRaises(LLMInferenceError):
            client.generate("system", "user")


# ────────────────────────────────────────────────────────────────
#  Integration: Pipeline Error Scenarios
# ────────────────────────────────────────────────────────────────

class TestPipelineErrorScenarios(unittest.TestCase):
    """Integration tests for error recovery paths from Phase 5 error matrix."""

    def setUp(self):
        self.restaurants = _sample_restaurants()
        self.loader = MockLoader(self.restaurants)

    def test_empty_dataset_returns_error_response(self):
        """Dataset load fails → error response."""
        service = RecommendationService(
            loader=MockEmptyLoader(),
            llm_client=MagicMock(),
        )
        prefs = UserPreferences(location="Bangalore", budget="medium")
        response = service.recommend(prefs)
        self.assertTrue(response.is_fallback)
        self.assertEqual(len(response.recommendations), 0)
        self.assertIn("Unable to load", response.summary)

    def test_llm_returns_invalid_json_falls_back(self):
        """Invalid JSON from LLM → fallback to deterministic."""
        class BadJSONLLM:
            def generate(self, sys, usr):
                return "This is not JSON at all, just text."

        service = RecommendationService(
            loader=self.loader,
            llm_client=BadJSONLLM(),
        )
        prefs = UserPreferences(location="Bangalore", budget="medium")
        response = service.recommend(prefs, target_count=2)
        self.assertTrue(response.is_fallback)
        self.assertGreater(len(response.recommendations), 0)

    def test_llm_timeout_falls_back(self):
        """Groq timeout → deterministic fallback."""
        class TimeoutLLM:
            def generate(self, sys, usr):
                raise LLMInferenceError("Connection timed out after 8s")

        service = RecommendationService(
            loader=self.loader,
            llm_client=TimeoutLLM(),
        )
        prefs = UserPreferences(location="Bangalore", budget="medium", cuisine="Italian")
        response = service.recommend(prefs, target_count=2)
        self.assertTrue(response.is_fallback)
        self.assertGreater(len(response.recommendations), 0)

    def test_use_llm_false_skips_llm(self):
        """When use_llm=False, LLM is never called."""
        llm_mock = MagicMock()
        service = RecommendationService(
            loader=self.loader,
            llm_client=llm_mock,
        )
        prefs = UserPreferences(location="Bangalore", budget="medium")
        response = service.recommend(prefs, use_llm=False, target_count=2)
        llm_mock.generate.assert_not_called()
        self.assertTrue(response.is_fallback)

    def test_pipeline_with_min_rating_zero(self):
        """min_rating=0.0 should not crash and returns all budget-matching restaurants."""
        service = RecommendationService(
            loader=self.loader,
            llm_client=MagicMock(side_effect=LLMInferenceError("skip")),
        )
        prefs = UserPreferences(location="Bangalore", budget="medium", min_rating=0.0)
        response = service.recommend(prefs, target_count=5)
        self.assertGreater(len(response.recommendations), 0)

    def test_pipeline_with_long_additional_preferences(self):
        """Long additional_preferences (300 chars max) should not crash."""
        service = RecommendationService(
            loader=self.loader,
            llm_client=MagicMock(side_effect=LLMInferenceError("skip")),
        )
        prefs = UserPreferences(
            location="Bangalore", budget="low",
            additional_preferences="x" * 300,
        )
        response = service.recommend(prefs, target_count=2)
        self.assertIsNotNone(response)


# ────────────────────────────────────────────────────────────────
#  Prompt Builder Edge Cases
# ────────────────────────────────────────────────────────────────

class TestPromptBuilderEdgeCases(unittest.TestCase):
    """Additional prompt builder edge cases."""

    def test_no_cuisine_shows_any(self):
        prefs = UserPreferences(location="Bangalore", budget="low")
        prompt = PromptBuilder.build_user_prompt(prefs, _sample_restaurants()[:1])
        self.assertIn("Any / All", prompt)

    def test_empty_candidates_shows_zero_count(self):
        prefs = UserPreferences(location="Bangalore", budget="low")
        prompt = PromptBuilder.build_user_prompt(prefs, [], target_count=5)
        self.assertIn("top 0", prompt)

    def test_additional_preferences_none_shows_default(self):
        prefs = UserPreferences(location="Bangalore", budget="low")
        prompt = PromptBuilder.build_user_prompt(prefs, _sample_restaurants()[:1])
        self.assertIn("None provided", prompt)


if __name__ == "__main__":
    unittest.main()
