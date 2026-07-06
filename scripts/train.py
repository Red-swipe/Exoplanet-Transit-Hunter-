"""Training entry point: load processed data, train a classifier, and persist it.

Supports two input modes:

1.  **Excel** (default):  ``--data data/processed/kepler_candidates.xlsx``
    with two sheets — ``tce_features`` (feature matrix) and
    ``tce_training_labels`` (label column ``koi_disposition``).

2.  **NumPy files**:  ``--features features.npy --labels labels.npy``
    for pre-computed arrays.

Usage:

    python -m scripts.train
    python -m scripts.train --data path/to/data.xlsx
    python -m scripts.train --features X.npy --labels y.npy --model gradient_boosting
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from config import settings
from src.logging_utils import configure_logging, get_logger
from src.model import (
    cross_validate_model,
    evaluate_model,
    prepare_dataset,
    save_model,
    split_dataset,
    train_gradient_boosting,
    train_random_forest,
)

logger = get_logger(__name__)


def _resolve_path(candidate: str) -> Path:
    path = Path(candidate)
    if not path.is_absolute():
        path = settings.paths.root / path
    return path.resolve()


def _load_from_excel(
    path: str | Path,
    candidate_policy: str = "exclude",
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    import pandas as pd

    resolved = _resolve_path(str(path))
    logger.info("Loading data from %s", resolved)
    df_features = pd.read_excel(resolved, sheet_name="tce_features")
    df_labels = pd.read_excel(resolved, sheet_name="tce_training_labels")

    star_ids: np.ndarray | None = None
    try:
        df_star_ids = pd.read_excel(resolved, sheet_name="star_ids")
        col = df_star_ids.columns[0]
        raw_star = df_star_ids[col].astype(str).str.strip()
        star_ids = raw_star.to_numpy(dtype=str)
        logger.info("Loaded %d star IDs from sheet.", len(star_ids))
    except (ValueError, KeyError):
        logger.info("No star_ids sheet found; proceeding without grouped splits.")

    col = df_labels.columns[0]
    raw = df_labels[col].astype(str).str.strip().str.lower()

    if candidate_policy == "exclude":
        is_candidate = raw == "candidate"
        n_candidate = int(is_candidate.sum())
        if n_candidate > 0:
            df_features = df_features.loc[~is_candidate].reset_index(drop=True)
            df_labels = df_labels.loc[~is_candidate].reset_index(drop=True)
            if star_ids is not None:
                star_ids = star_ids[~is_candidate]
            logger.info("Excluded %d CANDIDATE sample(s).", n_candidate)
        raw = df_labels[df_labels.columns[0]].astype(str).str.strip().str.lower()
    elif candidate_policy == "separate":
        raise NotImplementedError(
            "Separate candidate policy is not implemented. "
            "Use --candidate-policy exclude or negative."
        )

    X = df_features.select_dtypes(include=[np.number]).to_numpy(dtype=np.float64)

    y = np.array(
        [1.0 if v == "confirmed" else 0.0 for v in raw],
        dtype=np.float64,
    )

    n_confirmed = int(y.sum())
    n_negative = int(y.shape[0] - n_confirmed)
    logger.info(
        "Loaded %d samples (%d confirmed, %d negative) with %d features.",
        X.shape[0], n_confirmed, n_negative, X.shape[1],
    )
    return X, y, star_ids




def _load_from_npy(features_path: str, labels_path: str) -> tuple[np.ndarray, np.ndarray, None]:
    X = np.load(_resolve_path(features_path))
    y = np.load(_resolve_path(labels_path)).ravel()
    logger.info("Loaded %d samples with %d features from .npy files.", X.shape[0], X.shape[1])
    return X, y, None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train an Exoplanet Transit Hunter classifier.",
    )
    src = parser.add_mutually_exclusive_group()
    src.add_argument(
        "--data",
        type=str,
        default="data/processed/kepler_candidates.xlsx",
        help="Path to the processed XLSX file with tce_features / tce_training_labels sheets.",
    )
    src.add_argument("--features", type=str, help="Path to a .npy feature matrix.")
    src.add_argument("--labels", type=str, help="Path to a .npy label vector.")
    parser.add_argument(
        "--model",
        default="random_forest",
        choices=["random_forest", "gradient_boosting"],
        help="Classifier to train.",
    )
    parser.add_argument(
        "--test-size", type=float, default=0.2, help="Fraction for test split.",
    )
    parser.add_argument(
        "--cv", type=int, default=5, help="Number of cross-validation folds.",
    )
    parser.add_argument(
        "--seed", type=int, default=settings.random_seed, help="Random seed.",
    )
    parser.add_argument(
        "--candidate-policy",
        type=str,
        choices=["exclude", "negative", "separate"],
        default="exclude",
        help="How to handle CANDIDATE-labeled samples: exclude (default, drop them), negative (treat as negative class), separate (not yet implemented).",
    )
    return parser


def _factorize_groups(star_ids: np.ndarray | None) -> np.ndarray | None:
    if star_ids is None:
        return None
    import pandas as pd
    codes, _ = pd.factorize(star_ids)
    logger.info("Factorized %d star IDs into %d unique groups.", len(star_ids), int(codes.max()) + 1)
    return codes


def main() -> None:
    configure_logging()
    parser = _build_parser()
    args = parser.parse_args()

    if args.features and args.labels:
        X, y, star_ids = _load_from_npy(args.features, args.labels)
    elif args.data:
        logger.info("Candidate policy: %s", args.candidate_policy)
        X, y, star_ids = _load_from_excel(args.data, args.candidate_policy)
    else:
        logger.error("Either --data or both --features and --labels are required.")
        sys.exit(1)

    groups = _factorize_groups(star_ids)

    dataset = prepare_dataset(X, y)

    X_train, X_test, y_train, y_test = split_dataset(
        dataset, test_size=args.test_size, random_state=args.seed, groups=groups,
    )

    if args.model == "random_forest":
        model = train_random_forest(X_train, y_train, random_state=args.seed)
    else:
        model = train_gradient_boosting(X_train, y_train, random_state=args.seed)

    metrics = evaluate_model(model, X_test, y_test)
    logger.info(
        "Test set — accuracy: %.4f | precision: %.4f | recall: %.4f | f1: %.4f | roc_auc: %.4f",
        metrics.accuracy, metrics.precision, metrics.recall,
        metrics.f1, metrics.roc_auc,
    )

    cv_result = cross_validate_model(
        type(model), X_train, y_train,
        cv=args.cv, random_state=args.seed, groups=groups,
    )
    logger.info(
        "Cross-validation (%d folds) — accuracy: %.4f ± %.4f | f1: %.4f ± %.4f | roc_auc: %.4f ± %.4f",
        cv_result.n_folds,
        cv_result.accuracy_mean, cv_result.accuracy_std,
        cv_result.f1_mean, cv_result.f1_std,
        cv_result.roc_auc_mean, cv_result.roc_auc_std,
    )

    model_file = f"{args.model}.joblib"
    save_model(model, model_file)
    logger.info("Model saved as '%s' in the models/ directory.", model_file)

    logger.info("Training complete.")


if __name__ == "__main__":
    main()
