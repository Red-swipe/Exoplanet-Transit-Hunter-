"""Machine learning model definitions for transit detection.

This module provides classical machine learning classifiers — Random Forest
and Gradient Boosting — for classifying candidate transit events in
astronomical light curves.  It also exposes train / test helpers, evaluation
metrics, cross-validation, and model persistence via ``joblib``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import joblib
from sklearn.base import ClassifierMixin
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split

from config import settings
from src.logging_utils import get_logger, timer


logger = get_logger(__name__)

FloatArray = npt.NDArray[np.float64]


# ---------------------------------------------------------------------------
# Model persistence
# ---------------------------------------------------------------------------


def _ensure_models_dir() -> Path:
    """Return the ``models/`` directory, creating it if necessary."""
    models_dir = settings.paths.root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def save_model(model: ClassifierMixin, filename: str) -> str:
    """Persist a trained classifier to the ``models/`` directory.

    Args:
        model: Trained scikit-learn classifier.
        filename: File name (e.g. ``"random_forest.joblib"``).

    Returns:
        Absolute path of the saved file.

    Raises:
        ValueError: If ``filename`` is empty.
    """
    if not filename:
        raise ValueError("filename must not be empty.")

    models_dir = _ensure_models_dir()
    path = str(models_dir / filename)
    joblib.dump(model, path)
    logger.info("Model saved to %s", path)
    return path


def load_model(path: str | Path) -> ClassifierMixin:
    """Load a persisted classifier from disk.

    Args:
        path: Path to a ``.joblib`` file.

    Returns:
        Deserialized classifier.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        logger.error("Model file not found: %s", resolved)
        raise FileNotFoundError(f"Model file not found: {resolved}")

    model: ClassifierMixin = joblib.load(resolved)
    logger.info("Model loaded from %s", resolved)
    return model


# ---------------------------------------------------------------------------
# Dataset preparation
# ---------------------------------------------------------------------------


@dataclass
class Dataset:
    """Container for features and ground-truth labels.

    Attributes:
        X: Feature matrix of shape ``(n_samples, n_features)``.
        y: Label vector of shape ``(n_samples,)``.
    """

    X: FloatArray
    y: FloatArray


def prepare_dataset(
    features: list[dict[str, float]] | FloatArray,
    labels: list[float | int] | FloatArray,
) -> Dataset:
    """Convert extracted feature dictionaries and labels into a dataset.

    Args:
        features: Feature dictionaries from
            :func:`~src.features.extract_features` or a pre-computed feature
            matrix.
        labels: Ground-truth binary labels (0 = non-transit, 1 = transit).

    Returns:
        Dataset with consistent feature ordering.

    Raises:
        ValueError: If the number of samples does not match.
    """
    if isinstance(features, list):
        if not features:
            raise ValueError("Feature list must not be empty.")
        keys = sorted(features[0].keys())
        X = np.array([[d[k] for k in keys] for d in features], dtype=np.float64)
    else:
        X = np.asarray(features, dtype=np.float64)

    y = np.asarray(labels, dtype=np.float64).ravel()

    if X.shape[0] != y.shape[0]:
        raise ValueError(
            f"Feature count {X.shape[0]} does not match label count {y.shape[0]}."
        )

    logger.info("Prepared dataset with %d samples and %d features.", X.shape[0], X.shape[1])
    return Dataset(X=X, y=y)


# ---------------------------------------------------------------------------
# Train / test splitting
# ---------------------------------------------------------------------------


def split_dataset(
    dataset: Dataset,
    test_size: float = 0.2,
    random_state: int | None = None,
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    """Split a dataset into stratified train and test sets.

    Args:
        dataset: Input dataset.
        test_size: Fraction of samples reserved for testing.
        random_state: Seed used by the splitter.

    Returns:
        Tuple ``(X_train, X_test, y_train, y_test)``.
    """
    seed = random_state if random_state is not None else settings.random_seed
    X_train, X_test, y_train, y_test = train_test_split(
        dataset.X,
        dataset.y,
        test_size=test_size,
        random_state=seed,
        shuffle=True,
        stratify=dataset.y,
    )
    logger.info(
        "Split dataset: %d train / %d test samples.",
        X_train.shape[0],
        X_test.shape[0],
    )
    return X_train, X_test, y_train, y_test


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


def train_random_forest(
    X: FloatArray,
    y: FloatArray,
    **kwargs: Any,
) -> RandomForestClassifier:
    """Train a Random Forest classifier.

    Args:
        X: Feature matrix.
        y: Target labels.
        **kwargs: Additional keyword arguments forwarded to
            :class:`~sklearn.ensemble.RandomForestClassifier`.

    Returns:
        Fitted classifier.
    """
    params: dict[str, Any] = {
        "n_estimators": kwargs.pop("n_estimators", 100),
        "random_state": kwargs.pop("random_state", settings.random_seed),
        "n_jobs": kwargs.pop("n_jobs", -1),
        **kwargs,
    }
    model = RandomForestClassifier(**params)
    with timer(logger, "train_random_forest"):
        model.fit(X, y)
    logger.info("Random Forest trained with %d estimators.", params["n_estimators"])
    return model


def train_gradient_boosting(
    X: FloatArray,
    y: FloatArray,
    **kwargs: Any,
) -> GradientBoostingClassifier:
    """Train a Gradient Boosting classifier.

    Args:
        X: Feature matrix.
        y: Target labels.
        **kwargs: Additional keyword arguments forwarded to
            :class:`~sklearn.ensemble.GradientBoostingClassifier`.

    Returns:
        Fitted classifier.
    """
    params: dict[str, Any] = {
        "n_estimators": kwargs.pop("n_estimators", 100),
        "random_state": kwargs.pop("random_state", settings.random_seed),
        **kwargs,
    }
    model = GradientBoostingClassifier(**params)
    with timer(logger, "train_gradient_boosting"):
        model.fit(X, y)
    logger.info("Gradient Boosting trained with %d estimators.", params["n_estimators"])
    return model


def _optional_xgboost(
    X: FloatArray,
    y: FloatArray,
    **kwargs: Any,
) -> ClassifierMixin:
    """Train an XGBoost classifier if the package is available.

    Args:
        X: Feature matrix.
        y: Target labels.
        **kwargs: Additional keyword arguments forwarded to the XGBoost
            constructor.

    Returns:
        Fitted XGBoost classifier, or ``None`` if XGBoost is not installed.
    """
    try:
        import xgboost as xgb  # type: ignore[import-untyped]
    except ImportError:
        logger.info("XGBoost is not installed; skipping optional training.")
        return None  # type: ignore[return-value]

    params: dict[str, Any] = {
        "n_estimators": kwargs.pop("n_estimators", 100),
        "random_state": kwargs.pop("random_state", settings.random_seed),
        "eval_metric": kwargs.pop("eval_metric", "logloss"),
        "use_label_encoder": kwargs.pop("use_label_encoder", False),
        **kwargs,
    }
    model = xgb.XGBClassifier(**params)
    model.fit(X, y)
    logger.info("XGBoost trained with %d estimators.", params["n_estimators"])
    return model  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


@dataclass
class Metrics:
    """Container for evaluation results.

    Attributes:
        accuracy: Fraction of correctly predicted samples.
        precision: Precision score (macro-averaged).
        recall: Recall score (macro-averaged).
        f1: F1 score (macro-averaged).
        roc_auc: Area under the ROC curve.
        confusion: Confusion matrix as a 2-D list.
        report: Human-readable classification report.
    """

    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion: list[list[int]]
    report: str


def evaluate_model(
    model: ClassifierMixin,
    X_test: FloatArray,
    y_test: FloatArray,
) -> Metrics:
    """Compute a comprehensive set of classification metrics.

    Args:
        model: Fitted classifier.
        X_test: Test feature matrix.
        y_test: Ground-truth test labels.

    Returns:
        Aggregated evaluation metrics.

    Raises:
        ValueError: If fewer than two distinct classes are present in
            ``y_test`` (ROC AUC requires both classes).
    """
    with timer(logger, "evaluate_model"):
        y_pred = model.predict(X_test)

        try:
            y_prob = model.predict_proba(X_test)[:, 1]
        except (AttributeError, IndexError):
            y_prob = y_pred

        unique = np.unique(y_test)
        roc_auc: float
        if unique.size < 2:
            logger.warning("Only one class present in y_test; ROC AUC set to 0.0.")
            roc_auc = 0.0
        else:
            roc_auc = float(roc_auc_score(y_test, y_prob))

        cm = confusion_matrix(y_test, y_pred).tolist()

        metrics = Metrics(
            accuracy=float(accuracy_score(y_test, y_pred)),
            precision=float(precision_score(y_test, y_pred, average="macro", zero_division=0)),
            recall=float(recall_score(y_test, y_pred, average="macro", zero_division=0)),
            f1=float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
            roc_auc=roc_auc,
            confusion=cm,
            report=classification_report(y_test, y_pred, zero_division=0),
        )

    logger.info(
        "Evaluation — accuracy: %.4f, precision: %.4f, recall: %.4f, "
        "f1: %.4f, roc_auc: %.4f",
        metrics.accuracy,
        metrics.precision,
        metrics.recall,
        metrics.f1,
        metrics.roc_auc,
    )
    return metrics


# ---------------------------------------------------------------------------
# Cross-validation
# ---------------------------------------------------------------------------


@dataclass
class CrossValidationResult:
    """Container for cross-validation scores.

    Attributes:
        accuracy_mean: Mean accuracy across folds.
        accuracy_std: Standard deviation of accuracy across folds.
        precision_mean: Mean precision (macro) across folds.
        precision_std: Standard deviation of precision (macro) across folds.
        recall_mean: Mean recall (macro) across folds.
        recall_std: Standard deviation of recall (macro) across folds.
        f1_mean: Mean F1 score (macro) across folds.
        f1_std: Standard deviation of F1 score (macro) across folds.
        roc_auc_mean: Mean ROC AUC across folds.
        roc_auc_std: Standard deviation of ROC AUC across folds.
        n_folds: Number of folds used.
        per_fold: List of per-fold ``Metrics`` for detailed inspection.
    """

    accuracy_mean: float
    accuracy_std: float
    precision_mean: float
    precision_std: float
    recall_mean: float
    recall_std: float
    f1_mean: float
    f1_std: float
    roc_auc_mean: float
    roc_auc_std: float
    n_folds: int
    per_fold: list[Metrics] = field(default_factory=list)


def cross_validate_model(
    model_class: type,
    X: FloatArray,
    y: FloatArray,
    cv: int = 5,
    random_state: int | None = None,
    **kwargs: Any,
) -> CrossValidationResult:
    """Run stratified k-fold cross-validation on a classifier.

    Args:
        model_class: Uninstantiated classifier class (e.g.
            :class:`~sklearn.ensemble.RandomForestClassifier`).
        X: Full feature matrix.
        y: Full label vector.
        cv: Number of folds.
        random_state: Seed passed to the model and the fold splitter.
        **kwargs: Additional keyword arguments forwarded to the model
            constructor.

    Returns:
        Aggregated cross-validation results with per-fold details.
    """
    seed = random_state if random_state is not None else settings.random_seed
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=seed)

    fold_metrics: list[Metrics] = []

    with timer(logger, "cross_validate_model"):
        for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y)):
            X_fold_train = X[train_idx]
            X_fold_test = X[test_idx]
            y_fold_train = y[train_idx]
            y_fold_test = y[test_idx]

            model = model_class(random_state=seed, **kwargs)
            model.fit(X_fold_train, y_fold_train)
            m = evaluate_model(model, X_fold_test, y_fold_test)
            fold_metrics.append(m)
            logger.info("Fold %d — accuracy: %.4f, f1: %.4f", fold_idx + 1, m.accuracy, m.f1)

    accs = np.array([m.accuracy for m in fold_metrics])
    precs = np.array([m.precision for m in fold_metrics])
    recs = np.array([m.recall for m in fold_metrics])
    f1s = np.array([m.f1 for m in fold_metrics])
    aucs = np.array([m.roc_auc for m in fold_metrics])

    result = CrossValidationResult(
        accuracy_mean=float(np.mean(accs)),
        accuracy_std=float(np.std(accs)),
        precision_mean=float(np.mean(precs)),
        precision_std=float(np.std(precs)),
        recall_mean=float(np.mean(recs)),
        recall_std=float(np.std(recs)),
        f1_mean=float(np.mean(f1s)),
        f1_std=float(np.std(f1s)),
        roc_auc_mean=float(np.mean(aucs)),
        roc_auc_std=float(np.std(aucs)),
        n_folds=cv,
        per_fold=fold_metrics,
    )

    logger.info(
        "Cross-validation (%d folds) — accuracy: %.4f ± %.4f, "
        "f1: %.4f ± %.4f, roc_auc: %.4f ± %.4f",
        cv,
        result.accuracy_mean,
        result.accuracy_std,
        result.f1_mean,
        result.f1_std,
        result.roc_auc_mean,
        result.roc_auc_std,
    )
    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _main() -> None:
    """Train a model and save it to the models directory."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Train an Exoplanet Transit Hunter classifier."
    )
    parser.add_argument(
        "--model",
        default="random_forest",
        choices=["random_forest", "gradient_boosting"],
    )
    parser.add_argument(
        "--features", type=str, default=None, help="Path to a .npy or .npz feature matrix."
    )
    parser.add_argument(
        "--labels", type=str, default=None, help="Path to a .npy label vector."
    )
    parser.add_argument(
        "--test-size", type=float, default=0.2, help="Fraction for test split."
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility."
    )
    args = parser.parse_args()

    if args.features and args.labels:
        X = np.load(args.features)
        y = np.load(args.labels)
        dataset = prepare_dataset(X, y)
    else:
        logger.warning("No feature/label files provided; training on synthetic data.")
        rng = np.random.default_rng(args.seed)
        X = rng.random((200, 10))
        y = (X[:, 0] + X[:, 1] * 0.5 > 0.75).astype(np.float64)
        dataset = prepare_dataset(X, y)

    X_train, X_test, y_train, y_test = split_dataset(dataset, test_size=args.test_size, random_state=args.seed)

    if args.model == "random_forest":
        model = train_random_forest(X_train, y_train, random_state=args.seed)
    else:
        model = train_gradient_boosting(X_train, y_train, random_state=args.seed)

    metrics = evaluate_model(model, X_test, y_test)
    cv_result = cross_validate_model(
        type(model), X_train, y_train, cv=5, random_state=args.seed
    )

    model_type = "random_forest" if args.model == "random_forest" else "gradient_boosting"
    save_model(model, f"{model_type}.joblib")

    logger.info(
        "Training complete — test accuracy: %.4f, CV accuracy: %.4f ± %.4f",
        metrics.accuracy,
        cv_result.accuracy_mean,
        cv_result.accuracy_std,
    )


if __name__ == "__main__":
    _main()
