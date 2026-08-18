"""
Unit tests for Data Preprocessor (Phase 1).
Tests data normalization, cleaning, type coercion, and edge cases.
"""

import unittest
from src.data.preprocessor import (
    RestaurantPreprocessor,
    clean_rating,
    clean_cost,
    clean_cuisines,
    clean_location,
    clean_votes,
)
from src.models.restaurant import Restaurant


class TestPreprocessor(unittest.TestCase):
    """Test suite for data preprocessing and normalization functions."""

    def test_clean_rating_valid(self):
        """Test parsing valid rating formats."""
        self.assertEqual(clean_rating("4.1/5"), (4.1, False))
        self.assertEqual(clean_rating("4.5 / 5"), (4.5, False))
        self.assertEqual(clean_rating("3.9"), (3.9, False))
        self.assertEqual(clean_rating(4.2), (4.2, False))
        self.assertEqual(clean_rating("5.0"), (5.0, False))

    def test_clean_rating_edge_cases(self):
        """Test parsing irregular or dirty rating values (docs/edge-case.md §2.3)."""
        self.assertEqual(clean_rating("NEW"), (0.0, True))
        self.assertEqual(clean_rating("-"), (0.0, True))
        self.assertEqual(clean_rating("Opening Soon"), (0.0, True))
        self.assertEqual(clean_rating(None), (0.0, True))
        self.assertEqual(clean_rating(""), (0.0, True))
        # Clamping
        self.assertEqual(clean_rating("6.5/5"), (5.0, False))

    def test_clean_cost_and_budget_tiers(self):
        """Test cost string parsing and budget tier derivation (docs/edge-case.md §2.4)."""
        # Low budget (<= 500)
        cost_str, tier = clean_cost("₹400 for two")
        self.assertEqual(cost_str, "₹400 for two")
        self.assertEqual(tier, "low")

        cost_str, tier = clean_cost("500")
        self.assertEqual(cost_str, "₹500 for two")
        self.assertEqual(tier, "low")

        # Medium budget (501 - 1500)
        cost_str, tier = clean_cost("₹1,200")
        self.assertEqual(cost_str, "₹1200 for two")
        self.assertEqual(tier, "medium")

        # Range handling: "500-800" -> average 650 -> medium
        cost_str, tier = clean_cost("500-800")
        self.assertEqual(cost_str, "₹650 for two")
        self.assertEqual(tier, "medium")

        # High budget (> 1500)
        cost_str, tier = clean_cost("₹2,500 for two")
        self.assertEqual(cost_str, "₹2500 for two")
        self.assertEqual(tier, "high")

        # Unparseable / None
        cost_str, tier = clean_cost(None)
        self.assertEqual(cost_str, "Price on request")
        self.assertEqual(tier, "medium")

    def test_clean_cuisines(self):
        """Test cuisine string cleaning, splitting, and deduplication (docs/edge-case.md §2.5)."""
        res = clean_cuisines("North Indian, Chinese / Fast Food")
        self.assertEqual(res, ["North Indian", "Chinese", "Fast Food"])

        # Deduplication
        res = clean_cuisines("Cafe, Cafe, Bakery")
        self.assertEqual(res, ["Cafe", "Bakery"])

        # Empty / None fallback
        self.assertEqual(clean_cuisines(None), ["Multi-Cuisine"])
        self.assertEqual(clean_cuisines(""), ["Multi-Cuisine"])

    def test_clean_location(self):
        """Test location normalization."""
        self.assertEqual(clean_location("  bangalore  "), "Bangalore")
        self.assertEqual(clean_location("DELHI"), "Delhi")
        self.assertEqual(clean_location(None), "Unknown")

    def test_clean_votes(self):
        """Test vote count parsing."""
        self.assertEqual(clean_votes("14,820"), 14820)
        self.assertEqual(clean_votes("500"), 500)
        self.assertEqual(clean_votes(None), None)

    def test_process_record_column_aliases(self):
        """Test schema drift handling with various column aliases (docs/edge-case.md §2.2)."""
        raw_row = {
            "restaurant_name": "Corner House",
            "locality": "Bangalore",
            "food_type": "Desserts, Ice Cream",
            "rate": "4.6/5",
            "approx_cost(for two people)": "₹350",
            "votes": "9100",
        }
        res = RestaurantPreprocessor.process_record(raw_row)
        self.assertIsNotNone(res)
        self.assertEqual(res.name, "Corner House")
        self.assertEqual(res.location, "Bangalore")
        self.assertEqual(res.cuisines, ["Desserts", "Ice Cream"])
        self.assertEqual(res.rating, 4.6)
        self.assertEqual(res.budget_tier, "low")
        self.assertEqual(res.votes, 9100)

    def test_process_record_missing_mandatory_fields(self):
        """Test that records missing name or location are dropped."""
        # Missing name
        row1 = {"location": "Bangalore", "rate": "4.0"}
        self.assertIsNone(RestaurantPreprocessor.process_record(row1))

        # Missing location
        row2 = {"name": "Truffles", "rate": "4.5"}
        self.assertIsNone(RestaurantPreprocessor.process_record(row2))

    def test_process_records_batch(self):
        """Test batch record processing."""
        raw_rows = [
            {"name": "Valid 1", "location": "Bangalore", "rate": "4.2", "cost": "600"},
            {"name": "", "location": "Bangalore"},  # invalid, should be skipped
            {"name": "Valid 2", "location": "Delhi", "rate": "4.8", "cost": "2000"},
        ]
        results = RestaurantPreprocessor.process_records(raw_rows)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, "Valid 1")
        self.assertEqual(results[1].name, "Valid 2")


if __name__ == "__main__":
    unittest.main()
