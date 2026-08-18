"""
Unit and integration tests for the FastAPI API Layer (Phase 4).
Uses FastAPI TestClient for synchronous endpoint testing.
"""

import unittest
from fastapi.testclient import TestClient

from src.main import app


class TestAPILayer(unittest.TestCase):
    """Test suite for FastAPI REST endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # ── Health ──────────────────────────────────────────────────

    def test_health_endpoint(self):
        """GET /health returns 200 with dataset status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("dataset_loaded", data)
        self.assertIn("restaurant_count", data)
        self.assertIn("groq_configured", data)
        self.assertIsInstance(data["restaurant_count"], int)
        self.assertGreater(data["restaurant_count"], 0)

    # ── Metadata ────────────────────────────────────────────────

    def test_metadata_cities(self):
        """GET /metadata/cities returns sorted city list."""
        response = self.client.get("/metadata/cities")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("count", data)
        self.assertGreater(data["count"], 0)
        self.assertIsInstance(data["items"], list)
        # Verify sorted order
        self.assertEqual(data["items"], sorted(data["items"]))

    def test_metadata_cuisines(self):
        """GET /metadata/cuisines returns sorted cuisine list."""
        response = self.client.get("/metadata/cuisines")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["count"], 0)
        self.assertEqual(data["items"], sorted(data["items"]))

    def test_metadata_budgets(self):
        """GET /metadata/budgets returns budget tier options."""
        response = self.client.get("/metadata/budgets")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["items"], ["low", "medium", "high"])
        self.assertEqual(data["count"], 3)

    # ── Recommendations (valid) ─────────────────────────────────

    def test_recommendations_valid_request(self):
        """POST /recommendations with valid payload returns recommendations."""
        payload = {
            "location": "Bangalore",
            "budget": "medium",
            "cuisine": "Italian",
            "min_rating": 4.0,
        }
        response = self.client.post("/recommendations", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("summary", data)
        self.assertIn("recommendations", data)
        self.assertIn("is_fallback", data)
        self.assertIn("total_candidates", data)
        self.assertGreater(len(data["recommendations"]), 0)

        # Validate recommendation structure
        rec = data["recommendations"][0]
        self.assertIn("restaurant_name", rec)
        self.assertIn("rank", rec)
        self.assertIn("cuisine", rec)
        self.assertIn("rating", rec)
        self.assertIn("estimated_cost", rec)
        self.assertIn("explanation", rec)
        self.assertEqual(rec["rank"], 1)

    def test_recommendations_without_cuisine(self):
        """POST /recommendations without optional cuisine still works."""
        payload = {
            "location": "Bangalore",
            "budget": "low",
        }
        response = self.client.post("/recommendations", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data["recommendations"]), 0)

    def test_recommendations_filters_relaxed_populated(self):
        """POST /recommendations with impossible combo triggers relaxation."""
        payload = {
            "location": "Bangalore",
            "budget": "high",
            "cuisine": "Ethiopian",
            "min_rating": 4.9,
        }
        response = self.client.post("/recommendations", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Relaxation should have occurred
        self.assertIsNotNone(data["filters_relaxed"])
        self.assertGreater(len(data["filters_relaxed"]), 0)

    # ── Recommendations (invalid — 400) ─────────────────────────

    def test_recommendations_missing_location(self):
        """POST /recommendations without location returns 422."""
        payload = {"budget": "medium"}
        response = self.client.post("/recommendations", json=payload)
        self.assertIn(response.status_code, [400, 422])

    def test_recommendations_invalid_budget(self):
        """POST /recommendations with invalid budget returns 422."""
        payload = {"location": "Bangalore", "budget": "ultra"}
        response = self.client.post("/recommendations", json=payload)
        self.assertIn(response.status_code, [400, 422])

    def test_recommendations_rating_out_of_range(self):
        """POST /recommendations with min_rating > 5.0 returns 422."""
        payload = {
            "location": "Bangalore",
            "budget": "medium",
            "min_rating": 6.0,
        }
        response = self.client.post("/recommendations", json=payload)
        self.assertIn(response.status_code, [400, 422])

    def test_recommendations_empty_location(self):
        """POST /recommendations with empty string location returns 422."""
        payload = {"location": "", "budget": "medium"}
        response = self.client.post("/recommendations", json=payload)
        self.assertIn(response.status_code, [400, 422])

    # ── Unknown Location (valid but yields 0 results) ──────────

    def test_recommendations_unknown_location(self):
        """POST /recommendations for non-existent city returns 200 with empty list."""
        payload = {
            "location": "Zyxwvutsrqp",
            "budget": "medium",
        }
        response = self.client.post("/recommendations", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["recommendations"]), 0)
        self.assertIn("No restaurants found", data["summary"])

    # ── OpenAPI docs ────────────────────────────────────────────

    def test_openapi_docs_available(self):
        """GET /docs returns the OpenAPI Swagger UI page."""
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))


if __name__ == "__main__":
    unittest.main()
