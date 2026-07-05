from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import numpy.typing as npt
from sklearn.base import ClassifierMixin

if TYPE_CHECKING:
    from lightkurve import LightCurve

from src.features import extract_features_from_batch
from src.logging_utils import get_logger
from src.model import load_model
from config import settings
from src.preprocessing import (
    detrend,
    load_lightcurve,
    normalize,
    preprocess_pipeline,
    remove_nan,
    sigma_clip,
)

logger = get_logger(__name__)

FloatArray = npt.NDArray[np.float64]


def _import_lightkurve() -> Any:
    """Lazy-import lightkurve; raises ``ImportError`` if not installed."""
    try:
        import lightkurve as lk  # noqa: F811

        return lk
    except ImportError:
        raise ImportError(
            "lightkurve is required for inference. "
            "Install it with: pip install lightkurve"
        )


@dataclass
class PredictionResult:
    predicted_class: int
    confidence: float
    probabilities: dict[str, float]
    model_name: str
    input_file: str
    processing_time_seconds: float
    n_samples: int
    n_features: int
    metadata: dict[str, Any] | None = None


@dataclass
class BatchPredictionResult:
    successes: list[PredictionResult]
    failures: list[dict[str, Any]]
    total_files: int
    successful_files: int
    failed_files: int


def load_trained_model(name: str = "random_forest") -> ClassifierMixin:
    model_path = settings.paths.root / "models" / name
    logger.info("Loading model: %s", model_path)
    try:
        model = load_model(str(model_path))
        logger.info("Model loaded: %s (%s)", model_path, type(model).__name__)
        return model
    except FileNotFoundError:
        logger.exception("Model not found: %s", model_path)
        raise
    except Exception:
        logger.exception("Failed to load model: %s", model_path)
        raise


def _extract_arrays(
    lc: LightCurve,
) -> tuple[FloatArray, FloatArray, FloatArray | None]:
    time = lc.time.value.reshape(-1).astype(np.float64)
    flux = lc.flux.value.reshape(-1).astype(np.float64)
    flux_err = None
    if lc.flux_err is not None:
        flux_err = lc.flux_err.value.reshape(-1).astype(np.float64)
    return time, flux, flux_err


def predict_file(
    file_path: str | Path,
    model: ClassifierMixin | None = None,
    model_name: str = "random_forest",
    **preprocess_kwargs: Any,
) -> PredictionResult:
    start_time = time.perf_counter()
    path = Path(file_path)
    logger.info("Predicting: %s", path)

    if model is None:
        model = load_trained_model(model_name)

    processed_lc = preprocess_pipeline(path, **preprocess_kwargs)
    logger.info("Preprocessing completed: %s", path.name)

    time_arr, flux_arr, _ = _extract_arrays(processed_lc)
    n_samples = len(time_arr)

    features = extract_features_from_batch(time_arr, flux_arr)
    n_features = features.shape[1]
    logger.info("Features extracted: %s (%d features)", path.name, n_features)

    pred_class = int(model.predict(features)[0])
    proba = model.predict_proba(features)[0]
    confidence = float(proba[pred_class])
    probabilities = {str(c): float(p) for c, p in zip(model.classes_, proba)}

    elapsed = time.perf_counter() - start_time
    logger.info(
        "Result: %s class=%d confidence=%.4f (%.3fs)",
        path.name, pred_class, confidence, elapsed,
    )

    return PredictionResult(
        predicted_class=pred_class,
        confidence=confidence,
        probabilities=probabilities,
        model_name=model_name,
        input_file=path.name,
        processing_time_seconds=round(elapsed, 3),
        n_samples=n_samples,
        n_features=n_features,
        metadata={
            "model_class": type(model).__name__,
            "preprocess_kwargs": preprocess_kwargs,
        },
    )


def predict_lightcurve(
    time: FloatArray,
    flux: FloatArray,
    flux_error: FloatArray | None = None,
    model: ClassifierMixin | None = None,
    model_name: str = "random_forest",
    **preprocess_kwargs: Any,
) -> PredictionResult:
    start_time = time.perf_counter()
    logger.info("Predicting light curve (%d cadences)", len(time))

    if model is None:
        model = load_trained_model(model_name)

    lk = _import_lightkurve()
    lc = lk.LightCurve(time=time, flux=flux, flux_err=flux_error)

    processed_lc = remove_nan(lc)
    processed_lc = normalize(processed_lc)
    processed_lc = detrend(
        processed_lc,
        window_length=preprocess_kwargs.get("savgol_window_length", 101),
        polyorder=preprocess_kwargs.get("savgol_polyorder", 2),
    )
    processed_lc = sigma_clip(
        processed_lc,
        sigma=preprocess_kwargs.get("sigma", 5.0),
    )
    logger.info("Preprocessing completed")

    time_arr, flux_arr, _ = _extract_arrays(processed_lc)
    n_samples = len(time_arr)

    features = extract_features_from_batch(time_arr, flux_arr)
    n_features = features.shape[1]
    logger.info("Features extracted (%d features)", n_features)

    pred_class = int(model.predict(features)[0])
    proba = model.predict_proba(features)[0]
    confidence = float(proba[pred_class])
    probabilities = {str(c): float(p) for c, p in zip(model.classes_, proba)}

    elapsed = time.perf_counter() - start_time
    logger.info(
        "Result: class=%d confidence=%.4f (%.3fs)",
        pred_class, confidence, elapsed,
    )

    return PredictionResult(
        predicted_class=pred_class,
        confidence=confidence,
        probabilities=probabilities,
        model_name=model_name,
        input_file="<array>",
        processing_time_seconds=round(elapsed, 3),
        n_samples=n_samples,
        n_features=n_features,
        metadata={
            "model_class": type(model).__name__,
            "preprocess_kwargs": preprocess_kwargs,
        },
    )


def predict_batch(
    file_paths: list[str | Path],
    model: ClassifierMixin | None = None,
    model_name: str = "random_forest",
    **preprocess_kwargs: Any,
) -> BatchPredictionResult:
    logger.info("Batch: %d files, model=%s", len(file_paths), model_name)

    if model is None:
        model = load_trained_model(model_name)

    successes: list[PredictionResult] = []
    failures: list[dict[str, Any]] = []

    for file_path in file_paths:
        try:
            result = predict_file(
                file_path,
                model=model,
                model_name=model_name,
                **preprocess_kwargs,
            )
            successes.append(result)
        except Exception as e:
            logger.exception("Failed: %s", file_path)
            failures.append({"file": str(file_path), "error": f"{type(e).__name__}: {e}"})

    n_total = len(file_paths)
    n_ok = len(successes)
    n_fail = len(failures)
    logger.info("Batch done: %d/%d ok, %d/%d failed", n_ok, n_total, n_fail, n_total)

    return BatchPredictionResult(
        successes=successes,
        failures=failures,
        total_files=n_total,
        successful_files=n_ok,
        failed_files=n_fail,
    )
