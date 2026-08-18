"""
FastAPI Route Handlers.
Implements /health, /metadata/*, and /recommendations endpoints with
proper error mapping (400, 404, 502, 503).
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from src.api.schemas import (
    ErrorResponse,
    HealthResponse,
    MetadataListResponse,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponseSchema,
)
from src.config import settings
from src.data.loader import DatasetLoader
from src.models.preferences import UserPreferences
from src.services.recommendation import RecommendationService

logger = logging.getLogger(__name__)

# ─── Shared singletons (initialised at app startup via lifespan) ────
_loader: DatasetLoader = DatasetLoader()
_service: RecommendationService = RecommendationService(loader=_loader)


def get_loader() -> DatasetLoader:
    """Return the module-level DatasetLoader singleton."""
    return _loader


def get_service() -> RecommendationService:
    """Return the module-level RecommendationService singleton."""
    return _service


# ─── Router ─────────────────────────────────────────────────────

router = APIRouter()


# ── Health ──────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns service status, dataset load state, and Groq configuration status.",
    tags=["System"],
)
async def health_check() -> HealthResponse:
    loader = get_loader()
    restaurants = loader.load()
    return HealthResponse(
        status="ok",
        dataset_loaded=len(restaurants) > 0,
        restaurant_count=len(restaurants),
        groq_configured=settings.is_groq_configured,
    )


# ── Metadata ────────────────────────────────────────────────────

@router.get(
    "/metadata/cities",
    response_model=MetadataListResponse,
    summary="List Available Cities",
    description="Returns a sorted list of unique cities/localities in the dataset.",
    tags=["Metadata"],
)
async def list_cities() -> MetadataListResponse:
    loader = get_loader()
    cities = loader.get_cities()
    return MetadataListResponse(items=cities, count=len(cities))


@router.get(
    "/metadata/cuisines",
    response_model=MetadataListResponse,
    summary="List Available Cuisines",
    description="Returns a sorted list of unique cuisines across all restaurants.",
    tags=["Metadata"],
)
async def list_cuisines() -> MetadataListResponse:
    loader = get_loader()
    cuisines = loader.get_cuisines()
    return MetadataListResponse(items=cuisines, count=len(cuisines))


@router.get(
    "/metadata/budgets",
    response_model=MetadataListResponse,
    summary="List Budget Tiers",
    description="Returns the available budget tier options.",
    tags=["Metadata"],
)
async def list_budgets() -> MetadataListResponse:
    loader = get_loader()
    tiers = loader.get_budget_tiers()
    return MetadataListResponse(items=tiers, count=len(tiers))


# ── Recommendations ────────────────────────────────────────────

@router.post(
    "/recommendations",
    response_model=RecommendationResponseSchema,
    summary="Generate Restaurant Recommendations",
    description=(
        "Accepts user preferences and returns ranked restaurant recommendations. "
        "Uses Groq LLM for intelligent ranking when available, otherwise falls back "
        "to deterministic rating-based sorting."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input / validation error"},
        502: {"model": ErrorResponse, "description": "Groq LLM inference failed (upstream error)"},
        503: {"model": ErrorResponse, "description": "Dataset not available"},
    },
    tags=["Recommendations"],
)
async def get_recommendations(request: RecommendationRequest) -> RecommendationResponseSchema:
    """Generate restaurant recommendations from user preferences."""

    # 1. Build domain preferences from validated request
    try:
        preferences = UserPreferences(
            location=request.location,
            budget=request.budget,
            cuisine=request.cuisine,
            min_rating=request.min_rating,
            additional_preferences=request.additional_preferences,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # 2. Generate recommendations
    service = get_service()
    try:
        result = service.recommend(preferences, target_count=5)
    except Exception as exc:
        logger.error(f"Recommendation pipeline error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Recommendation service encountered an upstream error. Please try again.",
        )

    # 3. Convert domain response to API schema
    recommendation_items = [
        RecommendationItem(
            restaurant_name=r.restaurant_name,
            rank=r.rank,
            cuisine=r.cuisine,
            rating=r.rating,
            estimated_cost=r.estimated_cost,
            explanation=r.explanation,
        )
        for r in result.recommendations
    ]

    return RecommendationResponseSchema(
        summary=result.summary,
        recommendations=recommendation_items,
        filters_relaxed=result.filters_relaxed,
        is_fallback=result.is_fallback,
        total_candidates=result.total_candidates,
    )
