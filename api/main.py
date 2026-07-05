"""FastAPI application for the Exoplanet Transit Hunter."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from src.inference import load_trained_model
from src.logging_utils import get_logger

from .routes import router

logger = get_logger(__name__)

APP_TITLE = "Exoplanet Transit Hunter API"
APP_VERSION = "0.1.0"
DEFAULT_MODEL_NAME = "random_forest.joblib"

# ---------------------------------------------------------------------------
# Application lifespan — replaces deprecated on_event("startup")
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", APP_TITLE, APP_VERSION)

    app.state.settings = settings
    app.state.version = APP_VERSION
    app.state.server_started_at = time.time()
    app.state.total_predictions = 0
    app.state.model_name = DEFAULT_MODEL_NAME
    app.state.model = None

    model_path = settings.paths.root / "models" / DEFAULT_MODEL_NAME
    if model_path.is_file():
        try:
            app.state.model = load_trained_model(DEFAULT_MODEL_NAME)
            app.state.model_name = DEFAULT_MODEL_NAME
            logger.info("Model loaded from %s", model_path)
        except Exception:
            logger.warning("Failed to load model from %s", model_path, exc_info=True)
    else:
        logger.warning(
            "No model found at %s — predictions will return 503 until a model is trained.",
            model_path,
        )

    yield

    logger.info("Shutting down %s", APP_TITLE)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    lifespan=lifespan,
    description=(
        "REST API for classifying exoplanet transit candidates from FITS "
        "light-curve files using classical machine learning classifiers."
    ),
)

# ---------------------------------------------------------------------------
# CORS — open to all origins by default (tighten in production)
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------

app.include_router(router)
