"""
Dataset Loader Module.
Loads the Zomato dataset from Hugging Face or fallback cache and exposes normalized Restaurant entities.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.config import settings
from src.data.preprocessor import RestaurantPreprocessor
from src.data.seed_data import SAMPLE_ZOMATO_RECORDS
from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)

LOCAL_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "cache"


class DatasetLoader:
    """
    Loads, cleans, and caches restaurant data from Hugging Face or offline fallback.
    """

    _cached_restaurants: Optional[List[Restaurant]] = None
    _dataset_source: Optional[str] = None

    def __init__(self, dataset_name: Optional[str] = None) -> None:
        self.dataset_name = dataset_name or settings.dataset_name

    def load(self, force_reload: bool = False, prefer_local: bool = True) -> List[Restaurant]:
        """
        Load and normalize restaurant data.
        Caches in memory after first successful load.
        """
        if self._cached_restaurants is not None and not force_reload:
            return self._cached_restaurants

        restaurants = None

        # Check local cache first (normalized JSON)
        if prefer_local:
            restaurants = self._try_load_local_cache()

        # Check raw parquet cache
        if not restaurants and prefer_local:
            restaurants = self._try_load_parquet_cache()

        # Try Hugging Face if explicitly requested / online
        if not restaurants and not prefer_local:
            restaurants = self._try_load_huggingface()

        # If not loaded, use bundled seed dataset and persist to local cache
        if not restaurants:
            logger.info("Loading bundled seed dataset as baseline/fallback...")
            restaurants = RestaurantPreprocessor.process_records(SAMPLE_ZOMATO_RECORDS)
            self._dataset_source = "seed_fallback"
            self._save_local_cache(restaurants)

        # Cache in memory
        DatasetLoader._cached_restaurants = restaurants
        logger.info(f"Loaded {len(restaurants)} restaurants from source: {self._dataset_source}")
        return restaurants

    def _try_load_huggingface(self) -> Optional[List[Restaurant]]:
        """Attempt to download and process the Hugging Face dataset."""
        try:
            from datasets import load_dataset  # type: ignore

            logger.info(f"Attempting to load dataset '{self.dataset_name}' from Hugging Face...")
            ds = load_dataset(self.dataset_name, split="train")

            # Convert Hugging Face Dataset to list of dicts
            raw_records: List[Dict[str, Any]] = [dict(row) for row in ds]
            processed = RestaurantPreprocessor.process_records(raw_records)

            if processed:
                self._dataset_source = f"huggingface:{self.dataset_name}"
                self._save_local_cache(processed)
                return processed

        except ImportError:
            logger.debug("datasets library not installed, skipping live Hugging Face load.")
        except Exception as exc:
            logger.warning(
                f"Failed to load dataset '{self.dataset_name}' from Hugging Face ({exc}). "
                "Falling back to local cache or seed data."
            )

        return None

    def _save_local_cache(self, restaurants: List[Restaurant]) -> None:
        """Save normalized records to local JSON cache for offline resilience."""
        try:
            LOCAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_file = LOCAL_CACHE_DIR / "zomato_normalized.json"
            data = [r.to_dict() for r in restaurants]
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            logger.debug(f"Saved {len(restaurants)} records to local cache at {cache_file}")
        except Exception as exc:
            logger.warning(f"Could not write local cache: {exc}")

    def _try_load_local_cache(self) -> Optional[List[Restaurant]]:
        """Attempt to load from local JSON cache if present."""
        cache_file = LOCAL_CACHE_DIR / "zomato_normalized.json"
        if not cache_file.exists():
            return None

        try:
            logger.info(f"Loading cached restaurant data from {cache_file}...")
            with open(cache_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            restaurants = [Restaurant.from_dict(row) for row in raw_data if isinstance(row, dict)]
            if restaurants:
                self._dataset_source = f"local_cache:{cache_file.name}"
                return restaurants
        except Exception as exc:
            logger.warning(f"Failed to read local cache {cache_file}: {exc}")

        return None

    def _try_load_parquet_cache(self) -> Optional[List[Restaurant]]:
        """Attempt to load from raw parquet cache if present."""
        parquet_file = LOCAL_CACHE_DIR.parent / "zomato_cached.parquet"
        if not parquet_file.exists():
            return None

        try:
            logger.info(f"Loading raw cached restaurant data from {parquet_file}...")
            df = pd.read_parquet(parquet_file)
            raw_records = df.to_dict(orient="records")
            processed = RestaurantPreprocessor.process_records(raw_records)
            if processed:
                self._dataset_source = f"parquet_cache:{parquet_file.name}"
                self._save_local_cache(processed)
                return processed
        except Exception as exc:
            logger.warning(f"Failed to read parquet cache {parquet_file}: {exc}")

        return None

    def get_cities(self) -> List[str]:
        """Return sorted unique list of cities available in the dataset."""
        restaurants = self.load()
        cities = {r.location for r in restaurants if r.location and r.location != "Unknown"}
        return sorted(cities)

    def get_cuisines(self) -> List[str]:
        """Return sorted unique list of cuisines across all restaurants."""
        restaurants = self.load()
        all_cuisines = set()
        for r in restaurants:
            for c in r.cuisines:
                if c and c != "Multi-Cuisine":
                    all_cuisines.add(c)
        return sorted(all_cuisines)

    def get_budget_tiers(self) -> List[str]:
        """Return available budget tiers."""
        return ["low", "medium", "high"]

    def get_by_city(self, city: str) -> List[Restaurant]:
        """Filter cached restaurants by city name (case-insensitive)."""
        restaurants = self.load()
        city_lower = city.strip().lower()
        return [r for r in restaurants if r.location.lower() == city_lower]

    @property
    def source(self) -> Optional[str]:
        """Return identifier of where the data was loaded from."""
        return self._dataset_source
