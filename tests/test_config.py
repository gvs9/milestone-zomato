"""
Unit tests for configuration module (Phase 0).
Supports both pytest and standard library unittest.
"""

import unittest
from src.config import Settings


class TestConfig(unittest.TestCase):
    """Test suite for application configuration."""

    def test_default_settings(self):
        """Verify default configuration values."""
        settings = Settings()
        self.assertEqual(settings.groq_model, "llama-3.3-70b-versatile")
        self.assertEqual(settings.max_candidates, 20)
        self.assertEqual(settings.budget_low_max, 500)
        self.assertEqual(settings.budget_medium_max, 1500)
        self.assertEqual(settings.dataset_name, "ManikaSaini/zomato-restaurant-recommendation")
        self.assertEqual(settings.log_level, "INFO")
        self.assertEqual(settings.app_port, 8000)

    def test_groq_key_validation_placeholder(self):
        """Verify placeholder Groq key is treated as unconfigured."""
        settings = Settings(groq_api_key="gsk_your_groq_api_key_here")
        self.assertFalse(settings.is_groq_configured)
        self.assertFalse(settings.validate_groq_key(fail_fast=False))

        with self.assertRaises(ValueError):
            settings.validate_groq_key(fail_fast=True)

    def test_groq_key_validation_valid(self):
        """Verify valid Groq key format passes validation."""
        settings = Settings(groq_api_key="gsk_live_test_api_key_123456789")
        self.assertTrue(settings.is_groq_configured)
        self.assertTrue(settings.validate_groq_key(fail_fast=True))

    def test_custom_overrides(self):
        """Verify custom settings overrides."""
        settings = Settings(
            groq_model="llama-3.1-8b-instant",
            max_candidates=15,
            budget_low_max=400,
            budget_medium_max=1200,
        )
        self.assertEqual(settings.groq_model, "llama-3.1-8b-instant")
        self.assertEqual(settings.max_candidates, 15)
        self.assertEqual(settings.budget_low_max, 400)
        self.assertEqual(settings.budget_medium_max, 1200)


if __name__ == "__main__":
    unittest.main()
