"""
Application Configuration Module.
Loads and validates configuration from environment variables and .env file.
"""

from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
from typing import Optional

# Path to project root .env
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def _load_env_file(env_path: Path) -> None:
    """Load .env file into os.environ if present."""
    if not env_path.exists():
        return
    try:
        import dotenv
        dotenv.load_dotenv(dotenv_path=env_path)
    except ImportError:
        # Fallback standard library .env parser
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key not in os.environ:
                    os.environ[key] = val


_load_env_file(ENV_FILE)

# Streamlit Cloud deployment support
try:
    import streamlit as st
    if hasattr(st, "secrets"):
        try:
            for key in ["GROQ_API_KEY", "GROQ_MODEL", "DATASET_NAME"]:
                if key in st.secrets and key not in os.environ:
                    os.environ[key] = st.secrets[key]
        except Exception:
            # st.secrets throws an error if secrets.toml is missing locally
            pass
except ImportError:
    pass


@dataclass
class Settings:
    """Application settings and environment configuration."""

    groq_api_key: str = field(
        default_factory=lambda: os.getenv("GROQ_API_KEY", "").strip()
    )
    groq_model: str = field(
        default_factory=lambda: os.getenv("GROQ_MODEL", "llama3-70b-8192").strip()
    )
    max_candidates: int = field(
        default_factory=lambda: int(os.getenv("MAX_CANDIDATES", "20"))
    )
    budget_low_max: int = field(
        default_factory=lambda: int(os.getenv("BUDGET_LOW_MAX", "500"))
    )
    budget_medium_max: int = field(
        default_factory=lambda: int(os.getenv("BUDGET_MEDIUM_MAX", "1500"))
    )
    dataset_name: str = field(
        default_factory=lambda: os.getenv(
            "DATASET_NAME", "ManikaSaini/zomato-restaurant-recommendation"
        ).strip()
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").strip()
    )
    app_host: str = field(
        default_factory=lambda: os.getenv("APP_HOST", "0.0.0.0").strip()
    )
    app_port: int = field(
        default_factory=lambda: int(os.getenv("APP_PORT", "8000"))
    )

    @property
    def is_groq_configured(self) -> bool:
        """Check if a valid, non-placeholder Groq API key is configured."""
        return bool(
            self.groq_api_key
            and not self.groq_api_key.startswith("gsk_your_groq_api_key")
            and len(self.groq_api_key) > 5
        )

    def validate_groq_key(self, fail_fast: bool = False) -> bool:
        """
        Validate Groq API key presence and format.
        
        Args:
            fail_fast: If True, raises ValueError when unconfigured.
                       If False, logs a warning and returns False.
        """
        if not self.is_groq_configured:
            msg = (
                "GROQ_API_KEY is not configured or is a placeholder. "
                "Please set GROQ_API_KEY in .env or environment variables. "
                "Get a free key from https://console.groq.com/keys"
            )
            if fail_fast:
                raise ValueError(msg)
            logging.getLogger(__name__).warning(msg)
            return False
        return True


# Global settings instance
settings = Settings()
