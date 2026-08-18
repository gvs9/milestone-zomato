"""
Unit tests for Filter Engine and Candidate Selection (Phase 2).
Tests UserPreferences validation, filter rules, relaxation waterfall, and candidate ranking.
"""

import unittest
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.filter import RestaurantFilter, FilterResult


class TestFilterEngine(unittest.TestCase):
    """Test suite for RestaurantFilter and UserPreferences."""

    def setUp(self):
        """Create sample mock restaurants for deterministic testing."""
        self.sample_restaurants = [
            Restaurant(
                name="Truffles",
                location="Bangalore",
                city="Bangalore",
                locality="Koramangala",
                cuisines=["American", "Italian", "Burger"],
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
            Restaurant(
                name="Empire Restaurant",
                location="Bangalore",
                city="Bangalore",
                locality="Koramangala",
                cuisines=["North Indian", "Mughlai", "Biryani"],
                rating=4.1,
                cost_for_two="₹750 for two",
                budget_tier="medium",
                votes=7000,
            ),
            Restaurant(
                name="The Black Pearl",
                location="Bangalore",
                city="Bangalore",
                locality="Koramangala",
                cuisines=["North Indian", "European", "Mediterranean"],
                rating=4.8,
                cost_for_two="₹1800 for two",
                budget_tier="high",
                votes=12000,
            ),
            Restaurant(
                name="Bukhara",
                location="Delhi",
                city="Delhi",
                locality="Diplomatic Enclave",
                cuisines=["North Indian", "Mughlai", "Kebab"],
                rating=4.9,
                cost_for_two="₹6500 for two",
                budget_tier="high",
                votes=8700,
            ),
            Restaurant(
                name="Big Chill Cafe",
                location="Delhi",
                city="Delhi",
                locality="Khan Market",
                cuisines=["Italian", "Continental", "Pasta"],
                rating=4.7,
                cost_for_two="₹1500 for two",
                budget_tier="medium",
                votes=11900,
            ),
        ]
        self.filter_service = RestaurantFilter(max_candidates=5)

    def test_user_preferences_validation(self):
        """Verify UserPreferences normalization and boundary checks."""
        # Valid preferences
        prefs = UserPreferences(
            location=" Bangalore ",
            budget="MEDIUM",  # type: ignore
            cuisine="Italian",
            min_rating=4.0,
            additional_preferences="Outdoor seating",
        )
        self.assertEqual(prefs.location, "Bangalore")
        self.assertEqual(prefs.budget, "medium")
        self.assertEqual(prefs.min_rating, 4.0)

        # Missing location throws ValueError
        with self.assertRaises(ValueError):
            UserPreferences(location="", budget="low")

        # Invalid budget throws ValueError
        with self.assertRaises(ValueError):
            UserPreferences(location="Delhi", budget="luxury")  # type: ignore

        # Out-of-bounds rating throws ValueError
        with self.assertRaises(ValueError):
            UserPreferences(location="Delhi", budget="low", min_rating=6.5)

    def test_location_filtering(self):
        """Test location matching on city and locality."""
        # City match
        blr_recs = [
            r for r in self.sample_restaurants
            if self.filter_service.matches_location(r, "Bangalore")
        ]
        self.assertEqual(len(blr_recs), 5)

        # Locality match
        kora_recs = [
            r for r in self.sample_restaurants
            if self.filter_service.matches_location(r, "Koramangala")
        ]
        self.assertEqual(len(kora_recs), 3)

        # Non-matching location
        mumbai_recs = [
            r for r in self.sample_restaurants
            if self.filter_service.matches_location(r, "Mumbai")
        ]
        self.assertEqual(len(mumbai_recs), 0)

    def test_rating_filtering(self):
        """Test minimum rating filter threshold."""
        high_rated = [
            r for r in self.sample_restaurants
            if self.filter_service.matches_rating(r, 4.6)
        ]
        self.assertEqual(len(high_rated), 5)
        for r in high_rated:
            self.assertGreaterEqual(r.rating, 4.6)

    def test_cuisine_filtering(self):
        """Test case-insensitive partial cuisine matching."""
        italian_recs = [
            r for r in self.sample_restaurants
            if self.filter_service.matches_cuisine(r, "italian")
        ]
        self.assertEqual(len(italian_recs), 3)
        for r in italian_recs:
            self.assertTrue(any("Italian" in c for c in r.cuisines))

    def test_budget_filtering(self):
        """Test budget tier filtering."""
        low_budget = [
            r for r in self.sample_restaurants
            if self.filter_service.matches_budget(r, "low")
        ]
        self.assertEqual(len(low_budget), 1)
        self.assertEqual(low_budget[0].name, "Vidyarthi Bhavan")

    def test_hard_filters_combined(self):
        """Test combined hard filters for Bangalore + Italian + medium budget + 4.5 rating."""
        prefs = UserPreferences(
            location="Bangalore",
            budget="medium",
            cuisine="Italian",
            min_rating=4.5,
        )
        matched = self.filter_service.apply_hard_filters(self.sample_restaurants, prefs)
        self.assertEqual(len(matched), 2)
        names = {r.name for r in matched}
        self.assertEqual(names, {"Truffles", "Toit"})

    def test_candidate_selection_ranking_and_limit(self):
        """Test candidate ranking by rating and vote count, and max candidate limit."""
        # Add multiple branches of same brand
        multi_branch = self.sample_restaurants + [
            Restaurant(
                name="Truffles - Indiranagar",
                location="Bangalore",
                cuisines=["American", "Burger"],
                rating=4.5,
                cost_for_two="₹800 for two",
                budget_tier="medium",
                votes=5000,
            ),
            Restaurant(
                name="Truffles - St. Marks",
                location="Bangalore",
                cuisines=["American", "Burger"],
                rating=4.4,
                cost_for_two="₹800 for two",
                budget_tier="medium",
                votes=4000,
            ),
        ]
        # Max per brand is 2, limit is 3
        candidates = self.filter_service.select_candidates(multi_branch, max_n=3, max_per_brand=2)
        self.assertEqual(len(candidates), 3)
        # Check order: Bukhara (4.9), Black Pearl (4.8), Toit (4.7)
        self.assertEqual(candidates[0].name, "Bukhara")
        self.assertEqual(candidates[1].name, "The Black Pearl")
        self.assertEqual(candidates[2].name, "Toit")

    def test_filter_relaxation_waterfall(self):
        """Test that impossible filter combinations trigger the relaxation waterfall."""
        # Bangalore + High Budget + South Indian + 4.8 Rating (No exact match)
        impossible_prefs = UserPreferences(
            location="Bangalore",
            budget="high",
            cuisine="South Indian",
            min_rating=4.8,
        )
        result = self.filter_service.filter(self.sample_restaurants, impossible_prefs)
        self.assertTrue(result.is_relaxed)
        self.assertGreater(len(result.candidates), 0)
        # Should have relaxed min_rating or budget
        self.assertTrue(any(r in result.filters_relaxed for r in ["min_rating", "budget"]))

    def test_non_existent_location_returns_empty(self):
        """Test that unknown locations return empty candidates even after relaxation."""
        unknown_prefs = UserPreferences(
            location="Tokyo",
            budget="medium",
            cuisine="Japanese",
            min_rating=4.0,
        )
        result = self.filter_service.filter(self.sample_restaurants, unknown_prefs)
        self.assertEqual(len(result.candidates), 0)
        self.assertEqual(result.total_matched, 0)


if __name__ == "__main__":
    unittest.main()
