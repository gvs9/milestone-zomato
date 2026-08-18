"""
FastAPI Application Entry Point.
Wires the application, loads the dataset at startup, and registers route handlers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import router, get_loader
from src.config import settings

# ─── Logging ────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Lifespan (startup / shutdown) ──────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: pre-load dataset into memory for fast first request."""
    logger.info("Starting Zomato Recommender API...")
    loader = get_loader()
    restaurants = loader.load()
    logger.info(
        f"Dataset loaded: {len(restaurants)} restaurants "
        f"(source: {loader.source})"
    )
    settings.validate_groq_key(fail_fast=False)
    yield
    logger.info("Shutting down Zomato Recommender API.")


# ─── App Factory ────────────────────────────────────────────────

app = FastAPI(
    title="Zomato Restaurant Recommender API",
    description=(
        "AI-powered restaurant recommendation engine using Groq LLM. "
        "Filters restaurants from the Zomato dataset based on user preferences "
        "(location, budget, cuisine, rating) and returns ranked recommendations "
        "with personalised explanations."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router)


# ─── Global Exception Handler ──────────────────────────────────

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Map domain ValueError to 400 Bad Request."""
    return JSONResponse(
        status_code=400,
        content={
            "error": "validation_error",
            "message": str(exc),
            "details": None,
        },
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    """Catch-all for unexpected server errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again later.",
            "details": None,
        },
    )
