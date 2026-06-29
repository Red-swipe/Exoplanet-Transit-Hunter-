"""Inference helpers for transit candidate scoring.

This module will load trained models, transform preprocessed light curves into
model inputs, and return calibrated confidence scores for likely transits.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import torch

from src.model import TransitClassifier


@dataclass(frozen=True)
class PredictionResult:
    """Prediction output for a single light curve.

    Attributes:
        transit_probability: Estimated probability that a transit is present.
        predicted_label: Binary class label where 1 indicates a transit.
    """

    transit_probability: float
    predicted_label: int


def predict_transit(
    model: TransitClassifier,
    flux: npt.NDArray[np.float64],
    threshold: float = 0.5,
) -> PredictionResult:
    """Predict whether a normalized light curve contains a transit.

    Args:
        model: Trained transit classification model.
        flux: Normalized flux values.
        threshold: Probability threshold for assigning a positive label.

    Returns:
        Transit prediction result.
    """

    model.eval()
    with torch.no_grad():
        inputs = torch.as_tensor(flux, dtype=torch.float32).view(1, 1, -1)
        logits = model(inputs)
        probability = torch.softmax(logits, dim=1)[0, 1].item()

    return PredictionResult(
        transit_probability=float(probability),
        predicted_label=int(probability >= threshold),
    )
