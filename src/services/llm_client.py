"""
Groq LLM Client and Inference Layer.
Implements the LLMProvider interface with retries, timeouts, and rate-limit backoff.
"""

import logging
import os
import random
import time
from typing import Optional, Protocol

from src.config import settings

logger = logging.getLogger(__name__)


class LLMInferenceError(Exception):
    """Raised when LLM generation fails after all retries."""
    pass


class LLMProvider(Protocol):
    """Protocol interface for LLM providers."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate LLM response given system and user prompts."""
        ...


class GroqLLMClient:
    """
    Groq API client implementing LLMProvider.
    Uses Groq's high-speed LPU inference with JSON mode and exponential backoff.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 8.0,
        max_retries: int = 2,
    ) -> None:
        self.api_key = (api_key or settings.groq_api_key or "").strip()
        self.model = (model or settings.groq_model or "llama-3.3-70b-versatile").strip()
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None

    @property
    def is_configured(self) -> bool:
        """Check if client has a valid, non-placeholder API key."""
        return bool(
            self.api_key
            and not self.api_key.startswith("gsk_your_groq_api_key")
            and len(self.api_key) > 5
        )

    def _get_client(self):
        """Lazy-initialize Groq SDK client."""
        if self._client is None:
            if not self.is_configured:
                raise LLMInferenceError(
                    "Groq API key is not configured. Please set GROQ_API_KEY in .env."
                )
            try:
                from groq import Groq  # type: ignore

                self._client = Groq(api_key=self.api_key, timeout=self.timeout)
            except ImportError as exc:
                raise LLMInferenceError("groq package is not installed.") from exc
        return self._client

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate completions from Groq Chat API with retries and exponential backoff.
        
        Args:
            system_prompt: Guiding system instructions.
            user_prompt: Structured input data and preferences.
            
        Returns:
            JSON response text from Groq.
        """
        client = self._get_client()

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Calling Groq API (model={self.model}, attempt={attempt + 1})...")
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
                if not content:
                    raise LLMInferenceError("Groq returned empty response content.")
                return content

            except Exception as exc:
                exc_name = type(exc).__name__
                is_last = attempt == self.max_retries
                logger.warning(
                    f"Groq API call attempt {attempt + 1} failed with {exc_name}: {exc}"
                )

                if is_last:
                    raise LLMInferenceError(
                        f"Groq inference failed after {self.max_retries + 1} attempts: {exc}"
                    ) from exc

                # Exponential backoff with jitter (docs/edge-case.md §6.2)
                sleep_time = (2 ** attempt) + random.uniform(0.1, 0.5)
                time.sleep(sleep_time)

        raise LLMInferenceError("Groq inference terminated unexpectedly.")
