"""Pydantic models for the Exoplanet Transit Hunter REST API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PredictResponse(BaseModel):
    predicted_class: int = Field(
        ..., description="0 = non-transit, 1 = transit candidate"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Prediction confidence (probability of predicted class)"
    )
    processing_time_seconds: float = Field(
        ..., ge=0.0, description="Elapsed wall-clock time for feature extraction and inference"
    )
    model_name: str = Field(..., description="Name of the model used for inference")
    filename: str = Field(..., description="Original uploaded file name")
    n_samples: int = Field(
        ..., ge=1, description="Number of flux samples found in the light curve"
    )
    n_features: int = Field(
        ..., ge=1, description="Number of engineered features extracted"
    )
    probabilities: dict[str, float] = Field(
        ..., description="Per-class probabilities, e.g. {'non_transit': 0.92, 'transit': 0.08}"
    )


class BatchItemResult(BaseModel):
    filename: str
    success: bool
    data: PredictResponse | None = None
    error: str | None = None


class BatchPredictResponse(BaseModel):
    total_files: int = Field(..., ge=0)
    successful_files: int = Field(..., ge=0)
    failed_files: int = Field(..., ge=0)
    results: list[BatchItemResult]


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None


class MetricsResponse(BaseModel):
    model_name: str | None = Field(None, description="Currently loaded model, if any")
    model_type: str | None = Field(None, description="Classifier type, e.g. RandomForestClassifier")
    total_predictions: int = Field(0, ge=0)
    uptime_seconds: float = Field(..., ge=0.0)
    server_started_at: float = Field(..., description="Unix timestamp when the server started")
    app_name: str
    version: str
