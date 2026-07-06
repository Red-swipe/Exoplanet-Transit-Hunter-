"""Tests for ``src/model.py`` — dataset preparation, training, evaluation,
cross-validation, and model persistence."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

from src.model import (
    Dataset,
    cross_validate_model,
    evaluate_model,
    load_model,
    prepare_dataset,
    save_model,
    split_dataset,
    train_gradient_boosting,
    train_random_forest,
)


class TestPrepareDataset:
    def test_from_list_of_dicts(self):
        features = [{"a": 1.0, "b": 2.0}, {"a": 3.0, "b": 4.0}]
        labels = [0.0, 1.0]
        ds = prepare_dataset(features, labels)
        assert isinstance(ds, Dataset)
        assert ds.X.shape == (2, 2)
        assert ds.y.shape == (2,)
        np.testing.assert_array_almost_equal(ds.y, [0.0, 1.0])

    def test_from_numpy_array(self):
        X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        y = np.array([0.0, 1.0, 0.0])
        ds = prepare_dataset(X, y)
        assert ds.X.shape == (3, 2)
        assert ds.y.shape == (3,)

    def test_mismatched_counts_raises(self):
        X = np.array([[1.0, 2.0], [3.0, 4.0]])
        y = np.array([0.0])
        with pytest.raises(ValueError, match="does not match label count"):
            prepare_dataset(X, y)

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            prepare_dataset([], [])

    def test_labels_are_flattened(self):
        X = np.array([[1.0, 2.0], [3.0, 4.0]])
        y = np.array([[0.0], [1.0]])
        ds = prepare_dataset(X, y)
        assert ds.y.ndim == 1
        assert ds.y.shape == (2,)


class TestSplitDataset:
    def test_default_split(self):
        X = np.array([[1.0], [2.0], [3.0], [4.0], [5.0]])
        y = np.array([0.0, 0.0, 1.0, 1.0, 0.0])
        ds = Dataset(X=X, y=y)
        X_tr, X_te, y_tr, y_te = split_dataset(ds, test_size=0.4, random_state=42)
        assert X_tr.shape[0] == 3
        assert X_te.shape[0] == 2
        assert y_tr.shape[0] == 3
        assert y_te.shape[0] == 2

    def test_stratified_split_proportions(self):
        rng = np.random.default_rng(42)
        X = rng.random((100, 4))
        y = np.array([0.0] * 50 + [1.0] * 50)
        ds = Dataset(X=X, y=y)
        _, X_te, _, y_te = split_dataset(ds, test_size=0.2, random_state=0)
        ratio = float(y_te.sum()) / y_te.shape[0]
        assert ratio == pytest.approx(0.5, abs=0.15)

    def test_grouped_split_keeps_stars_together(self):
        X = np.array([[1.0], [2.0], [3.0], [4.0], [5.0], [6.0]])
        y = np.array([0.0, 0.0, 1.0, 1.0, 0.0, 1.0])
        groups = np.array([0, 0, 1, 1, 2, 2])
        ds = Dataset(X=X, y=y)
        X_tr, X_te, y_tr, y_te = split_dataset(
            ds, test_size=0.33, random_state=42, groups=groups,
        )
        train_idx = -np.ones(X.shape[0], dtype=int)
        test_idx = -np.ones(X.shape[0], dtype=int)
        for i, row in enumerate(X):
            match = np.where((X_tr == row).all(axis=1))[0]
            if len(match):
                train_idx[i] = match[0]
            match = np.where((X_te == row).all(axis=1))[0]
            if len(match):
                test_idx[i] = match[0]
        train_groups = set(groups[train_idx >= 0])
        test_groups = set(groups[test_idx >= 0])
        assert train_groups.isdisjoint(test_groups), "A star appears in both train and test"


class TestTrainRandomForest:
    def test_fit_returns_classifier(self):
        X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]])
        y = np.array([0.0, 0.0, 1.0, 1.0])
        model = train_random_forest(X, y, n_estimators=10, random_state=42)
        assert isinstance(model, RandomForestClassifier)
        assert model.n_estimators == 10
        preds = model.predict(X)
        assert preds.shape == (4,)

    def test_passes_kwargs(self):
        X = np.array([[1.0, 2.0], [3.0, 4.0]])
        y = np.array([0.0, 1.0])
        model = train_random_forest(X, y, max_depth=3, random_state=42)
        assert model.max_depth == 3


class TestTrainGradientBoosting:
    def test_fit_returns_classifier(self):
        X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        y = np.array([0.0, 1.0, 0.0])
        model = train_gradient_boosting(X, y, n_estimators=10, random_state=42)
        assert model.n_estimators == 10
        preds = model.predict(X)
        assert preds.shape == (3,)


class TestEvaluateModel:
    def test_returns_metrics(self):
        X = np.array([[1.0, 2.0], [2.0, 1.0], [5.0, 6.0], [6.0, 5.0]])
        y = np.array([0.0, 0.0, 1.0, 1.0])
        model = train_random_forest(X, y, n_estimators=10, random_state=42)
        metrics = evaluate_model(model, X, y)
        assert 0.0 <= metrics.accuracy <= 1.0
        assert 0.0 <= metrics.precision <= 1.0
        assert 0.0 <= metrics.recall <= 1.0
        assert 0.0 <= metrics.f1 <= 1.0
        assert metrics.roc_auc == pytest.approx(1.0, abs=0.05)
        assert len(metrics.confusion) == 2

    def test_single_class_sets_roc_auc_zero(self):
        X = np.array([[1.0], [2.0], [3.0], [4.0]])
        y = np.array([1.0, 1.0, 1.0, 1.0])
        model = train_random_forest(X, y, n_estimators=10, random_state=42)
        metrics = evaluate_model(model, X, y)
        assert metrics.roc_auc == 0.0

    def test_report_is_string(self):
        X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]])
        y = np.array([0.0, 0.0, 1.0, 1.0])
        model = train_random_forest(X, y, n_estimators=10, random_state=42)
        metrics = evaluate_model(model, X, y)
        assert isinstance(metrics.report, str)
        assert "precision" in metrics.report


class TestCrossValidateModel:
    def test_returns_aggregated_scores(self):
        rng = np.random.default_rng(42)
        X = rng.random((50, 4))
        y = np.array([0.0] * 25 + [1.0] * 25)
        result = cross_validate_model(
            RandomForestClassifier, X, y,
            cv=3, n_estimators=10, random_state=42,
        )
        assert 0.0 <= result.accuracy_mean <= 1.0
        assert result.n_folds == 3
        assert len(result.per_fold) == 3

    def test_std_is_nonnegative(self):
        rng = np.random.default_rng(99)
        X = rng.random((30, 3))
        y = np.array([0.0] * 15 + [1.0] * 15)
        result = cross_validate_model(
            RandomForestClassifier, X, y,
            cv=3, n_estimators=10, random_state=99,
        )
        assert result.accuracy_std >= 0.0
        assert result.f1_std >= 0.0
        assert result.roc_auc_std >= 0.0

    def test_grouped_cv_keeps_stars_together(self):
        rng = np.random.default_rng(42)
        X = rng.random((12, 3))
        y = np.array([0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        groups = np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5])
        result = cross_validate_model(
            RandomForestClassifier, X, y,
            cv=3, n_estimators=10, random_state=42, groups=groups,
        )
        assert result.n_folds == 3
        assert result.accuracy_mean > 0.0


class TestModelPersistence:
    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.model._ensure_models_dir",
            lambda: tmp_path,
        )
        X = np.array([[1.0, 2.0], [3.0, 4.0]])
        y = np.array([0.0, 1.0])
        model = train_random_forest(X, y, n_estimators=10, random_state=42)
        path = save_model(model, "test_model.joblib")
        saved_path = Path(path)
        assert saved_path == tmp_path / "test_model.joblib"
        assert saved_path.is_file()

        loaded = load_model(str(saved_path))
        np.testing.assert_array_equal(
            loaded.predict(X), model.predict(X),
        )

    def test_save_empty_filename_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            save_model(RandomForestClassifier(), "")

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError, match="Model file not found"):
            load_model("/nonexistent/path.joblib")


class TestCandidatePolicy:
    def _make_xlsx(self, tmp_path, dispositions):
        import pandas as pd
        xlsx = tmp_path / "test.xlsx"
        features = pd.DataFrame({"a": [float(i) for i in range(len(dispositions))]})
        labels = pd.DataFrame({"koi_disposition": dispositions})
        with pd.ExcelWriter(xlsx) as writer:
            features.to_excel(writer, sheet_name="tce_features", index=False)
            labels.to_excel(writer, sheet_name="tce_training_labels", index=False)
        return xlsx

    def test_exclude_policy_drops_candidates(self, tmp_path):
        from scripts.train import _load_from_excel
        xlsx = self._make_xlsx(
            tmp_path, ["CONFIRMED", "CANDIDATE", "FALSE POSITIVE", "CANDIDATE"],
        )
        X, y, star_ids = _load_from_excel(str(xlsx), candidate_policy="exclude")
        assert X.shape[0] == 2
        assert y.shape[0] == 2
        assert list(y) == [1.0, 0.0]
        assert star_ids is None

    def test_exclude_is_default(self, tmp_path):
        from scripts.train import _load_from_excel
        xlsx = self._make_xlsx(tmp_path, ["CONFIRMED", "CANDIDATE", "FALSE POSITIVE"])
        X, y, star_ids = _load_from_excel(str(xlsx))
        assert X.shape[0] == 2
        assert list(y) == [1.0, 0.0]
        assert star_ids is None

    def test_negative_policy_preserves_all(self, tmp_path):
        from scripts.train import _load_from_excel
        xlsx = self._make_xlsx(
            tmp_path, ["CONFIRMED", "CANDIDATE", "FALSE POSITIVE", "CANDIDATE"],
        )
        X, y, star_ids = _load_from_excel(str(xlsx), candidate_policy="negative")
        assert X.shape[0] == 4
        assert y.shape[0] == 4
        assert list(y) == [1.0, 0.0, 0.0, 0.0]
        assert star_ids is None

    def test_separate_policy_raises(self, tmp_path):
        from scripts.train import _load_from_excel
        xlsx = self._make_xlsx(tmp_path, ["CONFIRMED", "CANDIDATE"])
        with pytest.raises(NotImplementedError):
            _load_from_excel(str(xlsx), candidate_policy="separate")

    def test_no_candidates_exclude_is_noop(self, tmp_path):
        from scripts.train import _load_from_excel
        xlsx = self._make_xlsx(tmp_path, ["CONFIRMED", "FALSE POSITIVE"])
        X, y, star_ids = _load_from_excel(str(xlsx), candidate_policy="exclude")
        assert X.shape[0] == 2
        assert list(y) == [1.0, 0.0]
        assert star_ids is None
