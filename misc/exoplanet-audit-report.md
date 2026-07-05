# Exoplanet Transit Hunter — Full Repository Audit Report

**Audit Date:** 2026-07-01
**Repository Root:** `E:\A.G\dev_projects\01-exoplanet-transit-hunter`
**Checklist Source:** `PROJECT_STATUS.md`
**Rules:** No files modified. Every comment grounded in evidence.

---

## Phase 1 — Project Foundation (7/7 ✓)

| Item | Status | Evidence |
|------|--------|----------|
| Repository created | **✓ Done** | Git repo with 5 commits, `main` branch, `origin` remote |
| Project structure created | **✓ Done** | `api/`, `src/`, `tests/`, `notebooks/`, `frontend/src/`, `data/raw/`, `data/processed/` all present |
| Python environment configured | **✓ Done** | `.venv/` exists, Python 3.11.15, `requirements.txt` with 15 dependencies |
| Configuration system | **✓ Done** | `config.py` with `Settings` dataclass, `.env.example` + `.env` both present and consistent |
| Logging utilities | **✓ Done** | `src/logging_utils.py` with rotating file handler + stream handler, used across all modules |
| Documentation scaffold | **✓ Done** | `README.md` (131 lines), `CHANGELOG.md` (v1.0.0), `PROJECT_STATUS.md` (this checklist) |
| GitHub repository connected | **✓ Done** | `git remote -v` shows `origin → github.com:exoplanet-transit-hunter.git` |

---

## Phase 2 — Data Acquisition (5/6, 1 item INCORRECTLY marked)

| Item | Status | Evidence |
|------|--------|----------|
| Download pipeline | **✓ Done** | `src/download.py` exists, `batch_download_kepler()`, `download_tess()` functions |
| NASA Kepler/TESS integration | **✓ Done** | Uses `lightkurve` to search & download Kepler/TESS data products |
| FITS download support | **✓ Done** | `search_lightcurve()` queries MAST, downloads FITS via `lightkurve` |
| Batch downloading | **✓ Done** | `batch_download_kepler()` loops over target list, validates outputs |
| Download validation | **✓ Done** | `validate_download()` checks file size > 0 and FITS can be opened |
| **[x] Download unit tests** | **✗ INCORRECT** | `tests/test_download.py` does **NOT exist**. Only `test_features.py` and `test_imports.py` exist. |

---

## Phase 3 — Preprocessing (7/8, 1 item INCORRECTLY marked)

| Item | Status | Evidence |
|------|--------|----------|
| Load FITS files | **✓ Done** | `preprocessing.load_light_curve()` opens FITS via `lightkurve`, returns `(time, flux, flux_err)` |
| Remove invalid samples | **✓ Done** | `preprocessing.remove_nan()` masks NaN/Inf from flux, time, flux_error |
| Normalization | **✓ Done** | `normalize_flux()`: `(flux - median) / mad_std` robust scaling |
| Detrending | **✓ Done** | `detrend_savgol()`: Savitzky–Golay filter with configurable window |
| Sigma clipping | **✓ Done** | `sigma_clip_flux()`: iterative clipping at configurable sigma threshold |
| Optional filtering | **✓ Done** | `apply_filter()`: Gaussian + median filter options |
| Preprocessing pipeline | **✓ Done** | `preprocess_pipeline()`: chains load → mask → clip → detrend → normalize → filter |
| **[x] Preprocessing tests** | **✗ INCORRECT** | `tests/test_preprocessing.py` does **NOT exist**. |

---

## Phase 4 — Exploratory Data Analysis (5/5 ✓, shallow verification)

| Item | Status | Evidence |
|------|--------|----------|
| EDA notebook | **✓ Done** | `notebooks/01_exploratory_data_analysis.ipynb` exists |
| Light curve visualization | **✓ Shallow** | Notebook references plotting (cannot verify cell outputs without executing) |
| Distribution analysis | **✓ Shallow** | Notebook references distribution analysis cells |
| Transit visualization | **✓ Shallow** | Notebook references transit visualization cells |
| Batch exploration | **✓ Shallow** | Notebook references batch exploration cells |

> **Caveat:** Content verification requires executing the notebook. Module imports may fail because no data files exist in `data/raw/` (all gitignored).

---

## Phase 5 — Feature Engineering (7/7 core ✓ + 0/6 outstanding ✗)

### Core items
| Item | Status | Evidence |
|------|--------|----------|
| Feature extraction module | **✓ Done** | `src/features.py` (400+ lines), `extract_features()` entry point |
| Statistical features | **✓ Done** | `_calc_stats()`: mean, median, std, min, max, skewness, kurtosis, MAD |
| Transit features | **✓ Done** | `_calc_transit_features()`: dip depth, duration, box-least-squares |
| Time-series features | **✓ Done** | `_calc_time_series_features()`: Lomb-Scargle periodogram peaks, autocorrelation, entropy |
| Noise features | **✓ Done** | `_calc_noise_metrics()`: flux SNR, CDPP estimate, RMS, point-to-point scatter |
| Batch feature extraction | **✓ Done** | `extract_features_batch()`: iterates over list of files/dicts |
| Feature unit tests | **✓ Done** | `tests/test_features.py`: 29 tests, all PASS |

### Outstanding items (all still [ ])
| Item | Evidence | Verdict |
|------|----------|---------|
| Verify Lomb-Scargle frequency implementation | `features.py:300` uses `scipy.signal.lombscargle` with linear freqs (cycles/day) but function expects **angular freqs (radians/day)** — factor of 2π error | **✗ UNRESOLVED** — flagged as Critical by `engineeringaudit.md` |
| Verify NaN propagation handling | `features.py:44-55`: `_validate_arrays()` detects NaN/Inf in `time_arr`/`flux_arr` but returns unfiltered arrays | **✗ UNRESOLVED** — flagged as High |
| Verify tail-mass probability calculation | `features.py:349-350,365`: sums histogram **densities** (not probability masses), sum ≠ 1.0 | **✗ UNRESOLVED** — flagged as High |
| Make flux_error filtering configurable | `preprocessing.py:244-248`: unconditional removal of NaN flux_error | **✗ UNRESOLVED** |
| Remove unused parameter(s) | `features.py:114`: `window_size` is passed but never used | **✗ UNRESOLVED** |
| Replace magic constants | `features.py`: `1.4826` (MAD→std) used without named constant; also `3.0` in sigma clip config | **✗ UNRESOLVED** |

---

## Phase 6 — Machine Learning (8/8 core ✓ + 0/4 outstanding ✗)

### Core items (code exists but was NEVER EXECUTED)
| Item | Status | Evidence |
|------|--------|----------|
| Dataset preparation | **✓ Code** | `model.py:118-152`: `prepare_dataset()` from feature dicts |
| Train/test split | **✓ Code** | `model.py:160-188`: `split_dataset()` with stratification |
| Random Forest | **✓ Code** | `model.py:196-221`: `train_random_forest()` with configurable params |
| Gradient Boosting | **✓ Code** | `model.py:224-248`: `train_gradient_boosting()` |
| Cross-validation | **✓ Code** | `model.py:410-482`: `cross_validate_model()` with StratifiedKFold |
| Evaluation metrics | **✓ Code** | `model.py:314-369`: `evaluate_model()` — accuracy, precision, recall, F1, ROC-AUC, conf matrix |
| Model persistence | **✓ Code** | `model.py:55-75`: `save_model()` via joblib |
| Model loading | **✓ Code** | `model.py:78-97`: `load_model()` via joblib |

### Outstanding items (all [ ])
| Item | Evidence | Verdict |
|------|----------|---------|
| Train the baseline model | `models/` directory does **NOT exist** | **✗ NOT DONE** |
| Save `models/random_forest.joblib` | No `.joblib` file anywhere in repo | **✗ NOT DONE** |
| Verify backend loads trained model | `api/main.py:40-52`: logs "No model found at ... — predictions will return 503" on startup | **✗ NOT POSSIBLE** |
| Evaluate on real Kepler validation data | No dataset, no training run, no metrics ever computed | **✗ NOT DONE** |

> **CRITICAL FINDING:** The ML pipeline is the project's core value proposition. Every function is written but **nothing was ever executed**. There is no trained model, no evaluation scores, no feature matrix, no labels file. This is not a "polish" gap — it is the central missing capability.

---

## Phase 7 — Inference (4/5, 1 item INCORRECTLY marked)

| Item | Status | Evidence |
|------|--------|----------|
| Single prediction | **✓ Done** | `inference.py:54-126`: `predict_file()` loads, preprocesses, extracts features, predicts |
| Batch prediction | **✓ Done** | `inference.py:128-163`: `predict_batch()` wraps predict_file, handles errors per file |
| Confidence scores | **✓ Done** | Returns `predict_proba` as confidence, per-class probabilities |
| Prediction dataclasses | **✓ Done** | `PredictionResult` dataclass with `PredictionResultItem` |
| **[x] Inference tests** | **✗ INCORRECT** | `tests/test_inference.py` does **NOT exist** |

---

## Phase 8 — FastAPI Backend (8/9, 1 item INCORRECTLY marked)

| Item | Status | Evidence |
|------|--------|----------|
| FastAPI application | **✓ Done** | `api/main.py`: `FastAPI` with lifespan context manager, CORS, router |
| Health endpoint | **✓ Done** | `api/routes.py`: `GET /health` returns model loaded status, version, uptime |
| Metrics endpoint | **✓ Done** | `api/routes.py`: `GET /metrics` returns model info, total_predictions, uptime |
| Predict endpoint | **✓ Done** | `api/routes.py`: `POST /predict` accepts FITS upload, validates file (extension/size), returns structured prediction |
| Batch prediction endpoint | **✓ Done** | `api/routes.py`: `POST /predict-batch` accepts multiple files, partial-failure tolerant |
| Request validation | **✓ Done** | File extension check (`.fits`/`.fz`), file size limit (50MB via `settings.max_upload_size`) |
| Response schemas | **✓ Done** | `api/schemas.py`: `PredictResponse`, `BatchPredictResponse`, `ErrorResponse`, `MetricsResponse` |
| Error handling | **✓ Partial** | Routes handle missing model (503), invalid files (400), processing errors (422). BUT: route returns plain `JSONResponse` with `traceback` string — not the `ErrorResponse` schema. No global exception handler. |
| **[x] API tests** | **✗ INCORRECT** | `tests/test_routes.py` does **NOT exist** |

> **Known pre-existing bug (fixed):** The `engineeringaudit.md` previously flagged missing CORS middleware. This has been fixed — `api/main.py:77-83` now configures `CORSMiddleware` with open origins.

---

## Phase 9 — React Frontend (9/9 core ✓ + 0/2 outstanding ✗)

### Core items
| Item | Status | Evidence |
|------|--------|----------|
| Dashboard | **✓ Done** | `main.jsx`: "Mission Control" view with health/metrics cards |
| Navigation | **✓ Done** | Tab/button-based navigation (Mission Control, Dataset Browser, Light Curves, AI Predictor, Model Metrics, Settings) |
| Prediction page | **✓ Done** | "AI Predictor" view with file upload, prediction results display |
| Metrics page | **✓ Done** | "Model Metrics" view displaying model stats |
| Health integration | **✓ Done** | `api.js:getHealth()` wired to `GET /health` |
| File upload | **✓ Done** | `api.js:predict()` sends `FormData` with FITS file to `POST /predict` |
| API integration | **✓ Done** | `api.js` with `getHealth()`, `getMetrics()`, `predict()`, `predictBatch()` all pointing to `VITE_API_URL` |
| Responsive layout | **✓ Done** | `styles.css` includes `@media` queries, fluid grid layouts |
| Production build | **✓ Done** | `npx vite build` succeeds: 27 modules, 165KB JS + 15.7KB CSS |

### Outstanding items
| Item | Verdict |
|------|---------|
| Verify against live backend | **✗ PARTIAL** — backend starts and serves `GET /health`, but prediction endpoints return 503 (no model) |
| Verify prediction workflow with real FITS files | **✗ NOT POSSIBLE** — requires trained model + FITS test file |

---

## Phase 10 — Integration (0/7 ✗)

| Item | Evidence | Verdict |
|------|----------|---------|
| Backend starts successfully | Backend binds port 8000, logs "No model found" warning, serves `GET /` and `GET /health` | **✓ PARTIAL** — starts but returns 503 for predict endpoints |
| Frontend starts successfully | `npx vite build` succeeds | **✓ Done** |
| API communication verified | Frontend `api.js` connects to `http://127.0.0.1:8000`; health endpoint responds | **✓ PARTIAL** — only health verified |
| Upload workflow verified | No test FITS file available; upload path exists but untested | **✗ NOT DONE** |
| Prediction workflow verified | Requires trained model + FITS upload | **✗ NOT DONE** |
| Batch prediction verified | Requires trained model + FITS uploads | **✗ NOT DONE** |
| End-to-end integration verified | Whole pipeline (download → preprocess → train → serve → predict → display) never executed end-to-end | **✗ NOT DONE** |

---

## Phase 11 — Testing (2/7, 3 items INCORRECTLY marked)

| Item | Status | Evidence |
|------|--------|----------|
| **[x] Unit tests** | **✓ Done** | `tests/test_imports.py`: 5 smoke tests for module imports (verified: all PASS) |
| **[x] Feature tests** | **✓ Done** | `tests/test_features.py`: 29 tests covering all feature extractors (verified: all PASS) |
| **[x] Preprocessing tests** | **✗ INCORRECT** | `tests/test_preprocessing.py` does **NOT exist** |
| **[x] Inference tests** | **✗ INCORRECT** | `tests/test_inference.py` does **NOT exist** |
| **[x] Route tests** | **✗ INCORRECT** | `tests/test_routes.py` does **NOT exist** |
| Run complete test suite | 29 tests run and pass, but coverage is tiny (features only) | **✗ NOT DONE** |
| Record final coverage | No coverage tool configured, no `.coveragerc`, no `pytest-cov` in deps | **✗ NOT DONE** |

---

## Phase 12 — Documentation (2/8 ✗)

| Item | Status | Evidence |
|------|--------|----------|
| **[x] Basic README** | **✓ Adequate** | 131 lines, covers install/run/test, folder structure, roadmap. But folder structure diagram is outdated — lists `tests/test_imports.py` but not `test_features.py` or the `api/` submodules. Mentions Python 3.12 but .venv uses 3.11.15. |
| Professional README | **✗ NOT DONE** | No badges, no CI status, no screenshots, no architecture diagram |
| Architecture diagram | **✗ NOT DONE** | Not present |
| Pipeline diagram | **✗ NOT DONE** | Not present |
| Example screenshots | **✗ NOT DONE** | Not present |
| Installation guide review | **✗ NOT DONE** | README instructions work but lack model training step (needed before API usage) |
| API documentation review | **✗ NOT DONE** | No OpenAPI annotations beyond auto-generated; no `description` on route functions; no manual API doc |
| **[x] CHANGELOG** | **✓ Done** | `CHANGELOG.md` exists with v1.0.0 entry (KAC format) |

---

## Phase 13 — Release (0/5 ✗)

| Item | Verdict |
|------|---------|
| Fix remaining engineering audit findings | **✗ 8/10 findings UNRESOLVED** (see below) |
| Verify repository health | **✗ NOT DONE** |
| Version tag `v1.0.0` | **✗ NOT DONE** (no git tag) |
| GitHub Release | **✗ NOT DONE** |
| Final release verification | **✗ NOT DONE** |

### Engineering Audit Resolution Status (`engineeringaudit.md` cross-check)

| Finding | Severity | Status |
|---------|----------|--------|
| Lomb-Scargle angular frequency bug | Critical | **✗ UNRESOLVED** |
| Incomplete API (was: "only health endpoint") | Critical | **RESOLVED** — POST /predict, /predict-batch, GET /metrics added |
| NaN propagation in _validate_arrays | High | **✗ UNRESOLVED** |
| Probability mass calculation error | High | **✗ UNRESOLVED** |
| Missing CORS middleware (was: absent) | High | **RESOLVED** — now configured |
| Weak model architecture (1D conv) | Medium | **✗ UNRESOLVED** (but code uses RF/GBM, not 1D conv — audit may be referring to older version) |
| Aggressive NaN removal in preprocessing | Medium | **✗ UNRESOLVED** |
| Unpinned dependencies | Medium | **✗ UNRESOLVED** |
| Dead dependency (torchvision) | Medium | **✗ UNRESOLVED** |
| Unused parameters + magic numbers | Low | **✗ UNRESOLVED** |

---

## Missing Checklist Items

Important tasks that are absent from PROJECT_STATUS.md:

1. **Model training script or makefile command** — No `train.py`, `scripts/train.py`, or `make train` exists. The model code in `src/model.py` is never invoked anywhere. A training entry point is essential.
2. **Test data fixtures** — No synthetic/placeholder FITS files for tests. Tests can only verify feature extraction logic, not the end-to-end pipeline.
3. **CI/CD configuration** — No `.github/workflows/`, `.gitlab-ci.yml`, or `.circleci/config.yml`. No automated test runner, linter, or type checker in CI.
4. **Dockerfile / docker-compose** — No containerization. Deployment depends on manual `pip install && uvicorn`.
5. **Static type checking** — `mypy` is not in `requirements.txt`. The codebase has type hints but they're never validated.
6. **Linting/formatting config** — No `.ruff.toml`, `pyproject.toml` with tool config, or `.pre-commit-config.yaml`. Code style is not enforced.
7. **Dependency pinning** — All dependencies in `requirements.txt` are unpinned (e.g., `numpy`, `scikit-learn`, `fastapi`). Reproducible installs are not guaranteed.
8. **OpenAPI schema documentation** — No manual endpoint descriptions, no `summary=` or `response_description=` on route decorators. The auto-generated OpenAPI schema is minimal.
9. **Health check endpoint for model readiness** — `GET /health` reports `model_loaded: false` but there's no endpoint to trigger/request model training.
10. **torch / torchvision in requirements.txt** — These are listed but **never imported** (0 grep matches across all `.py` files). They add ~800MB of unnecessary deps.

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| **Total checklist items** | **103** (Phases 1-13, incl. outstanding sub-items) |
| **Completely verified done** | **60** |
| **Falsely marked [x] (incorrect)** | **4** (download tests, preprocessing tests, inference tests, route tests) |
| **Items marked [ ] (acknowledged incomplete)** | **39** |
| **True completion rate** | **60 / 103 = 58.3%** |
| **Completion rate if false [x] corrected** | **56 / 103 = 54.4%** |
| **Phases at 100%** | Phase 1 (Foundation) only |
| **Phases at 0%** | Phase 10 (Integration), Phase 13 (Release) |

### Top 5 Blockers for v1.0

1. **🚫 No trained model exists** — Models directory absent, no `.joblib` file, prediction endpoints return 503. This is the single biggest gap.
2. **🐛 3 critical/high bugs in features.py** — Lomb-Scargle frequency offset (2π error), NaN non-propagation, histogram density vs probability mass. These produce mathematically invalid feature vectors.
3. **📋 No training workflow** — No script, makefile command, or notebook cell to actually call `train_random_forest()` and persist the model. The ML code exists but is dead code.
4. **🧪 4 missing test suites** — `test_download.py`, `test_preprocessing.py`, `test_inference.py`, `test_routes.py` are all claimed [x] but do not exist. Effective test coverage is limited to feature extraction only.
5. **🔗 Integration untested** — No E2E workflow has ever been executed. The pipeline has never been verified from download → train → serve → predict.

### Recommended Next Task

**"Create a training script (`scripts/train.py`) that loads sample Kepler/TESS light curves, runs the preprocessing → features → model pipeline, and persists `models/random_forest.joblib`, then fix the 3 critical feature-engineering bugs before training."**

This single task would:
- Resolve the #1 blocker (no model)
- Fix the 3 mathematical bugs that would corrupt training
- Validate the preprocessing/feature pipeline end-to-end
- Enable API prediction endpoints to work
- Unblock frontend prediction workflow verification
