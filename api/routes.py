"""API route definitions for the Exoplanet Transit Hunter."""

from __future__ import annotations

import os
import tempfile
import time
import traceback
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse

from src.inference import predict_file as inference_predict
from src.logging_utils import get_logger

from .schemas import (
    BatchItemResult,
    BatchPredictResponse,
    MetricsResponse,
    PredictResponse,
)

logger = get_logger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {".fits", ".fit", ".fits.gz"}


def _is_allowed(filename: str) -> bool:
    """Check whether *filename* has a FITS-like extension."""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)


# ---------------------------------------------------------------------------
# GET / — project information
# ---------------------------------------------------------------------------


@router.get("/")
async def root(request: Request) -> dict:
    return {
        "app_name": request.app.state.settings.app_name,
        "version": request.app.state.version,
        "description": (
            "Exoplanet Transit Hunter REST API — upload FITS light-curve "
            "files for transit candidate classification using a trained "
            "machine-learning model."
        ),
        "endpoints": {
            "GET  /": "This help message",
            "GET  /health": "Health check",
            "POST /predict": "Classify a single FITS light-curve file",
            "POST /predict-batch": "Classify multiple FITS files in one request",
            "GET  /metrics": "Application metrics and uptime",
        },
    }


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


@router.get("/health")
async def health(request: Request) -> dict:
    return {
        "status": "ok",
        "service": request.app.state.settings.app_name,
        "model_loaded": request.app.state.model is not None,
    }


# ---------------------------------------------------------------------------
# POST /predict  — single light-curve classification
# ---------------------------------------------------------------------------


@router.post(
    "/predict",
    response_model=PredictResponse,
    responses={
        400: {"description": "Invalid input (bad file, missing data, ...)"},
        415: {"description": "Unsupported file type (only FITS accepted)"},
        422: {"description": "Unprocessable entity"},
        503: {"description": "Model not loaded"},
    },
)
async def predict(request: Request, file: UploadFile = File(...)) -> PredictResponse:
    if file.filename is None or not _is_allowed(file.filename):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    if request.app.state.model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded. Train or place a model file first.",
        )

    suffix = Path(file.filename).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        content = await file.read()
        tmp.write(content)
        tmp.close()

        t0 = time.perf_counter()
        result = inference_predict(
            tmp.name,
            model=request.app.state.model,
        )
        elapsed = time.perf_counter() - t0

    except Exception as exc:
        logger.error("Prediction failed for %s: %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prediction failed: {exc}",
        )
    finally:
        if Path(tmp.name).is_file():
            os.unlink(tmp.name)

    request.app.state.total_predictions += 1
    model_name = getattr(request.app.state, "model_name", "unknown")

    probs = result.probabilities if isinstance(result.probabilities, dict) else {}

    return PredictResponse(
        predicted_class=int(result.predicted_class),
        confidence=float(result.confidence),
        processing_time_seconds=round(elapsed, 4),
        model_name=model_name,
        filename=file.filename,
        n_samples=int(result.n_samples),
        n_features=int(result.n_features),
        probabilities=probs,
    )


# ---------------------------------------------------------------------------
# POST /predict-batch  — batch classification
# ---------------------------------------------------------------------------


@router.post(
    "/predict-batch",
    response_model=BatchPredictResponse,
    responses={
        503: {"description": "Model not loaded"},
    },
)
async def predict_batch(
    request: Request,
    files: list[UploadFile] = File(...),
) -> BatchPredictResponse:
    if request.app.state.model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded. Train or place a model file first.",
        )

    results: list[BatchItemResult] = []

    for f in files:
        if f.filename is None:
            results.append(
                BatchItemResult(
                    filename="unknown",
                    success=False,
                    error="Uploaded file has no filename",
                )
            )
            continue

        if not _is_allowed(f.filename):
            results.append(
                BatchItemResult(
                    filename=f.filename,
                    success=False,
                    error=f"Unsupported file type: {Path(f.filename).suffix}",
                )
            )
            continue

        suffix = Path(f.filename).suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            content = await f.read()
            tmp.write(content)
            tmp.close()

            pred_result = inference_predict(
                tmp.name,
                model=request.app.state.model,
            )

            request.app.state.total_predictions += 1
            model_name = getattr(request.app.state, "model_name", "unknown")
            probs = (
                pred_result.probabilities
                if isinstance(pred_result.probabilities, dict)
                else {}
            )

            results.append(
                BatchItemResult(
                    filename=f.filename,
                    success=True,
                    data=PredictResponse(
                        predicted_class=int(pred_result.predicted_class),
                        confidence=float(pred_result.confidence),
                        processing_time_seconds=0.0,
                        model_name=model_name,
                        filename=f.filename,
                        n_samples=int(pred_result.n_samples),
                        n_features=int(pred_result.n_features),
                        probabilities=probs,
                    ),
                )
            )
        except Exception as exc:
            logger.warning("Batch item failed for %s: %s", f.filename, exc)
            results.append(
                BatchItemResult(
                    filename=f.filename,
                    success=False,
                    error=str(exc),
                )
            )
        finally:
            if Path(tmp.name).is_file():
                os.unlink(tmp.name)

    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]

    return BatchPredictResponse(
        total_files=len(results),
        successful_files=len(successes),
        failed_files=len(failures),
        results=results,
    )


# ---------------------------------------------------------------------------
# GET /metrics
# ---------------------------------------------------------------------------


@router.get("/metrics", response_model=MetricsResponse)
async def metrics(request: Request) -> MetricsResponse:
    uptime = time.time() - request.app.state.server_started_at
    model_obj = request.app.state.model
    model_type = type(model_obj).__name__ if model_obj is not None else None

    return MetricsResponse(
        model_name=getattr(request.app.state, "model_name", None),
        model_type=model_type,
        total_predictions=request.app.state.total_predictions,
        uptime_seconds=round(uptime, 2),
        server_started_at=request.app.state.server_started_at,
        app_name=request.app.state.settings.app_name,
        version=request.app.state.version,
    )
