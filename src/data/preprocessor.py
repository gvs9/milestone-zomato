"""
Data Preprocessing and Normalization Module.
Cleans raw restaurant records from datasets into canonical Restaurant domain entities.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from src.config import settings
from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)

# Column name aliases to handle upstream schema drift (see docs/edge-case.md §2.2)
COLUMN_ALIASES: Dict[str, List[str]] = {
    "name": ["name", "restaurant_name", "res_name", "title"],
    "location": ["location", "listed_in(city)", "city", "locality", "address_city"],
    "cuisines": ["cuisines", "cuisine", "food_type", "dish_type"],
    "rating": ["rate", "rating", "aggregate_rating", "user_rating"],
    "cost": [
        "approx_cost(for two people)",
        "cost_for_two",
        "average_cost_for_two",
        "approx_cost",
        "cost",
    ],
    "address": ["address", "full_address", "street_address"],
    "rest_type": ["rest_type", "type", "restaurant_type", "listed_in(type)"],
    "votes": ["votes", "review_count", "rating_count", "vote_count"],
}


def clean_rating(raw_val: Any) -> Tuple[float, bool]:
    """
    Parse raw rating into a float in range [0.0, 5.0] and an is_unrated flag.
    Handles formats like '4.1/5', ' 4.2 ', 'NEW', '-', None, np.nan.
    
    Returns:
        Tuple of (rating_float, is_unrated_bool)
    """
    if raw_val is None:
        return 0.0, True

    val_str = str(raw_val).strip()
    if not val_str or val_str.upper() in ("NEW", "-", "N/A", "OPENING SOON", "NONE", "NAN"):
        return 0.0, True

    # Match leading float e.g. "4.1/5" -> 4.1 or "4.2" -> 4.2
    match = re.search(r"^(\d+(\.\d+)?)", val_str)
    if match:
        try:
            val = float(match.group(1))
            clamped = min(max(val, 0.0), 5.0)
            return round(clamped, 1), False
        except (ValueError, TypeError):
            pass

    return 0.0, True


def clean_cost(
    raw_val: Any,
    budget_low_max: Optional[int] = None,
    budget_medium_max: Optional[int] = None,
) -> Tuple[str, str]:
    """
    Clean raw cost string into formatted '₹<amount> for two' and determine budget tier.
    Handles '₹1,200', '1,500', '500-800', 'N/A', None.
    
    Returns:
        Tuple of (cost_for_two_str, budget_tier_str)
    """
    low_threshold = budget_low_max if budget_low_max is not None else settings.budget_low_max
    med_threshold = budget_medium_max if budget_medium_max is not None else settings.budget_medium_max

    if raw_val is None:
        return "Price on request", "medium"

    val_str = str(raw_val).strip().replace(",", "").replace("₹", "").replace("INR", "").strip()

    # Handle ranges like "500-800" or "500 - 800"
    range_match = re.search(r"(\d+)\s*-\s*(\d+)", val_str)
    if range_match:
        try:
            low = int(range_match.group(1))
            high = int(range_match.group(2))
            numeric_cost = (low + high) // 2
        except (ValueError, TypeError):
            numeric_cost = None
    else:
        # Extract first continuous digits
        digit_match = re.search(r"\d+", val_str)
        if digit_match:
            try:
                numeric_cost = int(digit_match.group(0))
            except (ValueError, TypeError):
                numeric_cost = None
        else:
            numeric_cost = None

    if numeric_cost is None or numeric_cost <= 0:
        return "Price on request", "medium"

    # Derive budget tier
    if numeric_cost <= low_threshold:
        tier = "low"
    elif numeric_cost <= med_threshold:
        tier = "medium"
    else:
        tier = "high"

    return f"₹{numeric_cost} for two", tier


def clean_cuisines(raw_val: Any) -> List[str]:
    """
    Clean and split comma/slash/pipe separated cuisine string into deduplicated list.
    Handles 'North Indian, Chinese / Fast Food', 'Cafe, Cafe', None.
    
    Returns:
        List of cleaned, title-cased cuisine names.
    """
    if raw_val is None:
        return ["Multi-Cuisine"]

    val_str = str(raw_val).strip()
    if not val_str or val_str.lower() in ("nan", "none", "n/a"):
        return ["Multi-Cuisine"]

    # Split on comma, slash, or pipe
    tokens = re.split(r"[,|/]", val_str)
    cleaned = []
    seen = set()

    for token in tokens:
        item = token.strip().title()
        if item and item.lower() not in seen:
            seen.add(item.lower())
            cleaned.append(item)

    return cleaned if cleaned else ["Multi-Cuisine"]


KNOWN_CITIES = {
    "bangalore": "Bangalore",
    "bengaluru": "Bangalore",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "ncr": "Delhi",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "pune": "Pune",
    "hyderabad": "Hyderabad",
    "chennai": "Chennai",
    "madras": "Chennai",
}


def clean_location_and_city(
    raw_location: Any,
    raw_address: Any = None,
    raw_listed_city: Any = None,
) -> Tuple[str, str, Optional[str]]:
    """
    Normalize location, city, and locality.
    
    Returns:
        Tuple of (canonical_location, city, locality)
    """
    loc_str = str(raw_location).strip() if raw_location is not None else ""
    addr_str = str(raw_address).strip() if raw_address is not None else ""
    listed_str = str(raw_listed_city).strip() if raw_listed_city is not None else ""

    combined_text = f"{loc_str} {addr_str} {listed_str}".lower()

    # Detect city from combined location and address text
    detected_city = None
    for key, city_name in KNOWN_CITIES.items():
        if key in combined_text:
            detected_city = city_name
            break

    # If not detected from known cities, default to location title or "Bangalore"
    if not detected_city:
        detected_city = loc_str.title() if loc_str else "Unknown"

    locality = None
    if loc_str and loc_str.lower() != detected_city.lower():
        locality = loc_str.title()

    # Canonical display location: City (or "Locality, City")
    canonical_location = detected_city if detected_city != "Unknown" else (loc_str.title() or "Unknown")

    return canonical_location, detected_city, locality


def clean_location(raw_val: Any) -> str:
    """Normalize location string (backward-compatible helper)."""
    loc, _, _ = clean_location_and_city(raw_val)
    return loc


def clean_votes(raw_val: Any) -> Optional[int]:
    """Extract numeric vote count safely."""
    if raw_val is None:
        return None
    val_str = str(raw_val).strip().replace(",", "")
    match = re.search(r"\d+", val_str)
    if match:
        try:
            return int(match.group(0))
        except (ValueError, TypeError):
            return None
    return None


class RestaurantPreprocessor:
    """Preprocessor for converting raw tabular/dictionary records into Restaurant models."""

    @staticmethod
    def _extract_field(row: Dict[str, Any], canonical_name: str) -> Any:
        """Find value in raw row using known aliases for canonical field name."""
        aliases = COLUMN_ALIASES.get(canonical_name, [canonical_name])
        for alias in aliases:
            if alias in row and row[alias] is not None:
                return row[alias]
            # Also try case-insensitive check
            for k in row:
                if k.lower() == alias.lower() and row[k] is not None:
                    return row[k]
        return None

    @classmethod
    def process_record(cls, raw_row: Dict[str, Any]) -> Optional[Restaurant]:
        """
        Normalize a single raw record into a Restaurant entity.
        Returns None if record lacks mandatory fields (name or location).
        """
        name_raw = cls._extract_field(raw_row, "name")
        location_raw = cls._extract_field(raw_row, "location")
        address_raw = cls._extract_field(raw_row, "address")
        listed_city_raw = raw_row.get("listed_in(city)")

        if not name_raw or str(name_raw).strip() in ("", "nan", "None"):
            return None

        name = str(name_raw).strip()
        location, city, locality = clean_location_and_city(
            location_raw, raw_address=address_raw, raw_listed_city=listed_city_raw
        )

        if location in ("Unknown", ""):
            return None

        cuisines = clean_cuisines(cls._extract_field(raw_row, "cuisines"))
        rating, is_unrated = clean_rating(cls._extract_field(raw_row, "rating"))
        cost_for_two, budget_tier = clean_cost(cls._extract_field(raw_row, "cost"))

        address = str(address_raw).strip() if address_raw and str(address_raw).strip() not in ("nan", "None") else None
        rest_type_raw = cls._extract_field(raw_row, "rest_type")
        rest_type = str(rest_type_raw).strip() if rest_type_raw and str(rest_type_raw).strip() not in ("nan", "None") else None

        votes = clean_votes(cls._extract_field(raw_row, "votes"))

        return Restaurant(
            name=name,
            location=location,
            city=city,
            locality=locality,
            cuisines=cuisines,
            rating=rating,
            cost_for_two=cost_for_two,
            budget_tier=budget_tier,
            address=address,
            rest_type=rest_type,
            votes=votes,
            is_unrated=is_unrated,
        )

    @classmethod
    def process_records(cls, raw_records: List[Dict[str, Any]]) -> List[Restaurant]:
        """
        Batch normalize a list of raw dictionary records into Restaurant entities.
        Drops dirty/incomplete records.
        """
        results: List[Restaurant] = []
        for idx, row in enumerate(raw_records):
            try:
                restaurant = cls.process_record(row)
                if restaurant:
                    results.append(restaurant)
            except Exception as exc:
                logger.debug(f"Skipping malformed row {idx}: {exc}")
                continue
        return results
