"""
Recommendation Orchestrator Service.
Coordinates data loading, deterministic filtering, Groq LLM ranking, and fallback handling.
"""

import logging
import time
from typing import Optional

from src.data.loader import DatasetLoader
from src.models.preferences import UserPreferences
from src.models.recommendation import RecommendationResponse
from src.services.filter import RestaurantFilter
from src.services.llm_client import GroqLLMClient, LLMProvider
from src.services.prompt_builder import PromptBuilder
from src.services.response_parser import ResponseParser

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    End-to-end recommendation orchestrator combining deterministic data processing
    with Groq LLM intelligence.
    """

    def __init__(
        self,
        loader: Optional[DatasetLoader] = None,
        filter_service: Optional[RestaurantFilter] = None,
        llm_client: Optional[LLMProvider] = None,
    ) -> None:
        self.loader = loader or DatasetLoader()
        self.filter_service = filter_service or RestaurantFilter()
        self.llm_client = llm_client if llm_client is not None else GroqLLMClient()

    def recommend(
        self,
        preferences: UserPreferences,
        target_count: int = 5,
        use_llm: bool = True,
    ) -> RecommendationResponse:
        """
        Generate ranked restaurant recommendations with explanations.
        
        Args:
            preferences: User search preferences.
            target_count: Number of top recommendations to return (default: 5).
            use_llm: Whether to attempt Groq LLM inference (default: True).
            
        Returns:
            RecommendationResponse with summary and ranked recommendations.
        """
        pipeline_start = time.perf_counter()

        # Log incoming request
        logger.info(
            f"[Pipeline] Request: location={preferences.location}, "
            f"budget={preferences.budget}, cuisine={preferences.cuisine or 'Any'}, "
            f"min_rating={preferences.min_rating}"
        )

        # 1. Load dataset (cached in memory)
        t0 = time.perf_counter()
        restaurants = self.loader.load()
        load_ms = (time.perf_counter() - t0) * 1000
        logger.info(f"[Pipeline] Dataset: {len(restaurants)} restaurants loaded ({load_ms:.1f}ms)")

        if not restaurants:
            logger.error("[Pipeline] Dataset load returned empty — returning error response")
            return RecommendationResponse(
                summary="Unable to load restaurant dataset. Please check configuration.",
                recommendations=[],
                filters_relaxed=None,
                is_fallback=True,
                total_candidates=0,
            )

        # 2. Apply deterministic filters
        t0 = time.perf_counter()
        filter_result = self.filter_service.filter(restaurants, preferences)
        filter_ms = (time.perf_counter() - t0) * 1000
        candidates = filter_result.candidates

        logger.info(
            f"[Pipeline] Filter: {filter_result.total_matched} matched → "
            f"{len(candidates)} candidates selected ({filter_ms:.1f}ms)"
            f"{' [RELAXED: ' + ', '.join(filter_result.filters_relaxed) + ']' if filter_result.is_relaxed else ''}"
        )

        if not candidates:
            total_ms = (time.perf_counter() - pipeline_start) * 1000
            logger.info(
                f"[Pipeline] Zero candidates for '{preferences.location}' — "
                f"total pipeline time: {total_ms:.1f}ms"
            )
            return RecommendationResponse(
                summary=f"No restaurants found for location '{preferences.location}'. Please check the city or locality name.",
                recommendations=[],
                filters_relaxed=filter_result.filters_relaxed,
                is_fallback=False,
                total_candidates=0,
            )

        # 3. Attempt LLM generation if enabled and configured
        if use_llm and self.llm_client:
            try:
                system_prompt = PromptBuilder.build_system_prompt()
                user_prompt = PromptBuilder.build_user_prompt(
                    preferences, candidates, target_count=target_count
                )

                t0 = time.perf_counter()
                raw_output = self.llm_client.generate(system_prompt, user_prompt)
                llm_ms = (time.perf_counter() - t0) * 1000

                response = ResponseParser.parse_and_validate(
                    raw_llm_output=raw_output,
                    candidates=candidates,
                    preferences=preferences,
                    filters_relaxed=filter_result.filters_relaxed if filter_result.is_relaxed else None,
                    target_count=target_count,
                )

                total_ms = (time.perf_counter() - pipeline_start) * 1000
                logger.info(
                    f"[Pipeline] LLM: {len(response.recommendations)} recommendations "
                    f"returned ({llm_ms:.1f}ms Groq, {total_ms:.1f}ms total)"
                )
                return response

            except Exception as exc:
                logger.warning(
                    f"[Pipeline] LLM failed ({type(exc).__name__}: {exc}). "
                    f"Activating deterministic fallback..."
                )

        # 4. Deterministic Fallback Engine
        t0 = time.perf_counter()
        fallback_response = ResponseParser.generate_fallback_response(
            candidates=candidates,
            preferences=preferences,
            filters_relaxed=filter_result.filters_relaxed if filter_result.is_relaxed else None,
            target_count=target_count,
        )
        fallback_ms = (time.perf_counter() - t0) * 1000
        total_ms = (time.perf_counter() - pipeline_start) * 1000
        logger.info(
            f"[Pipeline] Fallback: {len(fallback_response.recommendations)} recommendations "
            f"({fallback_ms:.1f}ms fallback, {total_ms:.1f}ms total)"
        )
        return fallback_response

