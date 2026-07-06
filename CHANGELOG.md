# Changelog

All notable changes to the Exoplanet Transit Hunter project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] — 2026-07-06

### Added

- **L1 — CANDIDATE label handling**: `--candidate-policy` CLI argument replaces
  `--exclude-candidates`. Supports three modes:
  - `exclude` (default): removes CANDIDATE rows, trains on CONFIRMED vs FALSE POSITIVE
  - `negative`: maps CANDIDATE to class 0.0 alongside FALSE POSITIVE
  - `separate`: raises `NotImplementedError` (reserved for future three-class)
- **`TestCandidatePolicy`** regression tests in `tests/test_model.py`: 5 test
  methods covering all three policy modes, default behavior, and no-candidate edge case

### Changed

- `scripts/train.py`: `_load_from_excel` accepts `candidate_policy` string param
  instead of boolean `exclude_candidates`; filtering uses `koi_disposition` value
  directly instead of KOI ID list matching; removed `_filter_out_candidates`
- `docs/scientific_validation.md`: L1 marked ✅ Fixed, P1 updated to reflect
  actual implementation
- `ROADMAP.md`: CANDIDATE label handling marked ✅ completed

## [1.2.0] — 2026-07-06

### Fixed

- **V4 — Cross-validation same-star leakage**: `cross_validate_model` now uses
  `StratifiedGroupKFold` when `groups` is provided, replacing `StratifiedKFold`.
  The old `StratifiedKFold.split(X, y, groups=groups)` accepted the groups
  parameter silently but did **not** enforce group integrity, allowing TCEs from
  the same star to appear in different folds and inflating CV metrics.
  (Fixes docs/scientific_validation.md §4-V4)

### Changed

- `docs/scientific_validation.md`: V3 and V4 both marked ✅ Fixed
- `tests/test_model.py`: added `test_grouped_cv_keeps_stars_together` to
  `TestCrossValidateModel`

## [1.1.0] — 2026-07-05

### Added

- **Regression tests** for all three scientific correctness fixes in
  `tests/test_features.py`:
  - `B1` — `TestExtractTimeseriesFeatures.test_lomb_scargle_detects_known_period`:
    sine wave with period 5.0 days, asserts `ts_ls_peak_period ≈ 5.0`
  - `B2` — `TestExtractFeatures.test_handles_nan_in_time_and_flux`: 500 points
    with NaN every 10th/15th sample, asserts all features finite
  - `B2` — `TestExtractFeatures.test_all_nan_still_raises`: all-NaN input
    asserts `ValueError`
  - `B3` — `TestExtractDistributionFeatures.test_tail_mass_is_fraction_in_unit_interval`:
    random data, asserts `0.0 ≤ dist_tail_mass ≤ 1.0`
  - `B3` — `TestExtractDistributionFeatures.test_uniform_tail_mass_is_reasonable`:
    uniform [-1,1], 20 bins, asserts `≈0.20`
- **`ROADMAP.md`** — completed fixes, known issues, and future work sections

### Fixed

- **B1 — Lomb-Scargle angular frequency**: `angular_freqs` now uses
  `linspace(...) * 2π` (radians/day); `peak_period = 2π / peak_freq`. Old code
  produced periods off by a factor of 2π.
- **B2 — NaN propagation in feature extraction**: `_validate_arrays` now returns
  filtered arrays (`time_arr[valid], flux_arr[valid]`). Old code returned
  unfiltered arrays, letting NaN poison downstream computations.
- **B3 — Histogram probability mass normalization**: `density=True` replaced
  with `density=False`; `tail_mass` normalized by explicit total count sum. Old
  code produced `tail_mass > 1`.

### Changed

- `src/features.py`: three scientific correctness fixes described above
- `tests/test_features.py`: 5 new regression test methods added across 3
  existing test classes

## [1.0.0] — 2026-07-01

### Added

- **API routes** (`api/routes.py`): three endpoints — `GET /health` (service status + model loaded flag), `GET /metrics` (model name, type, total predictions, uptime), `POST /predict` (confidence, predicted class, processing time)
- **Pydantic schemas** (`api/schemas.py`): `HealthResponse`, `MetricsResponse`, `PredictRequest`, `PredictResponse`, `ErrorResponse`
- **Frontend API client** (`frontend/src/api.js`): `getHealth()`, `getMetrics()`, `predict()` wired to the live backend
- **Vite configuration** (`frontend/vite.config.js`): build toolchain for the React frontend
- **sklearn-based inference pipeline** (`src/inference.py`, `src/model.py`): real model loading via `joblib`, prediction with `RandomForestClassifier`, training pipeline with lightkurve + optional xgboost
- **`joblib`** added to `requirements.txt` for model persistence

### Changed

- `api/main.py`: FastAPI app with lifespan context manager, CORS middleware, and router mounting
- `frontend/src/main.jsx`: React UI now consumes live API endpoints instead of mock data
- `frontend/src/styles.css`: upload UI and prediction result styling
- `tests/test_imports.py`: updated to reflect new module structure
