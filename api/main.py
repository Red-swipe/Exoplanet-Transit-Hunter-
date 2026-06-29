"""FastAPI application for Exoplanet Transit Hunter."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from config import settings
from src.logging_utils import configure_logging, get_logger


configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="API for detecting exoplanet transits in stellar light curves.",
    version="0.1.0",
)


class HealthResponse(BaseModel):
    """Health check response payload."""

    status: str = Field(..., examples=["ok"])
    service: str = Field(..., examples=[settings.app_name])


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return API health status.

    Returns:
        Health response payload.
    """

    logger.debug("Health check requested.")
    return HealthResponse(status="ok", service=settings.app_name)
