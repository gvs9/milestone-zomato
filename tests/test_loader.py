"""
Unit tests for Dataset Loader (Phase 1).
Tests data loading, caching, city/cuisine extraction, and offline fallback.
"""

import unittest
from src.data.loader import DatasetLoader
from src.models.restaurant import Restaurant


class TestDatasetLoader(unittest.TestCase):
    """Test suite for DatasetLoader."""

    def setUp(self):
        """Reset dataset loader before each test."""
        DatasetLoader._cached_restaurants = None
        self.loader = DatasetLoader()

    def test_load_restaurants_returns_valid_data(self):
        """Verify that loader returns a non-empty list of Restaurant entities."""
        restaurants = self.loader.load()
        self.assertIsInstance(restaurants, list)
        self.assertGreater(len(restaurants), 0)

        sample = restaurants[0]
        self.assertIsInstance(sample, Restaurant)
        self.assertTrue(bool(sample.name))
        self.assertTrue(bool(sample.location))
        self.assertIsInstance(sample.cuisines, list)
        self.assertGreater(len(sample.cuisines), 0)
        self.assertIn(sample.budget_tier, ["low", "medium", "high"])
        self.assertGreaterEqual(sample.rating, 0.0)
        self.assertLessEqual(sample.rating, 5.0)

    def test_get_cities(self):
        """Verify get_cities returns sorted unique cities including major Indian metros."""
        cities = self.loader.get_cities()
        self.assertIsInstance(cities, list)
        self.assertGreater(len(cities), 0)
        self.assertEqual(cities, sorted(cities))

        # Must include Bangalore and key localities
        self.assertIn("Bangalore", cities)
        self.assertTrue(
            any(loc in cities for loc in ["Koramangala", "Indiranagar", "Whitefield", "Jayanagar"])
        )

    def test_get_cuisines(self):
        """Verify get_cuisines returns sorted unique cuisines."""
        cuisines = self.loader.get_cuisines()
        self.assertIsInstance(cuisines, list)
        self.assertGreater(len(cuisines), 0)
        self.assertEqual(cuisines, sorted(cuisines))

        # Check typical cuisines
        self.assertTrue(any("Italian" in c for c in cuisines))
        self.assertTrue(any("North Indian" in c for c in cuisines))
        self.assertTrue(any("South Indian" in c for c in cuisines))

    def test_get_budget_tiers(self):
        """Verify get_budget_tiers returns low, medium, high."""
        tiers = self.loader.get_budget_tiers()
        self.assertEqual(tiers, ["low", "medium", "high"])

    def test_in_memory_caching(self):
        """Verify that repeated load() calls return the cached in-memory instance."""
        res1 = self.loader.load()
        res2 = self.loader.load()
        self.assertIs(res1, res2)

    def test_get_by_city(self):
        """Verify filtering by city."""
        blr_restaurants = self.loader.get_by_city("Bangalore")
        self.assertGreater(len(blr_restaurants), 0)
        for r in blr_restaurants:
            self.assertEqual(r.location.lower(), "bangalore")


if __name__ == "__main__":
    unittest.main()
