# Pre-Fix Engineering Analysis — Exoplanet Transit Hunter

**Date:** 2026-07-01
**Scope:** Fresh, independent audit of entire repository. Every claim traced to actual code.
**Method:** Read every source file line-by-line. Cross-referenced `misca/engineeringaudit.md`.
**Branch:** `main`, commit `5`

---

## 1. Repository Overview

| Aspect | Status |
|---|---|
| Total Python SLOC | ~1250 (src/ + api/ + config.py) |
| Entry points | `api/main.py` (FastAPI), `src/download.py` (CLI), `src/model.py` (CLI) |
| ML framework | scikit-learn (RandomForest, SVM, GradientBoosting) |
| Data source | Lightkurve (Kepler/TESS MAST archive) |
| Test coverage | 2 test files, 17 test functions, mostly smoke/import tests |
| Frontend | React (Vite) — 6 hardcoded mock pages, no API integration |
| Documentation | README, CHANGELOG, engineeringaudit.md, project_status.md |
| License | MIT |

---

## 2. Bug Catalog

### B1: Lomb-Scargle periodogram frequency units (angular vs linear)

- **Severity:** HIGH
- **File:** `src/features.py`, line ~300
- **Root cause:** `scipy.signal.lombscargle` expects **angular frequencies** (radians/day) but the code passes **linear frequencies** (cycles/day = `1 / period`). The function internally computes `y * exp(-1j * 2 * pi * x * omega)`. When `omega` is already in cycles/day, the effective frequency is `2π * cycles/day`, doubling the actual frequency.
- **Why it matters:** Transit signals at the wrong frequencies produce different periodogram power, corrupting the `freq1_power`, `freq2_power`, `freq3_power` features and any features derived from them. Feature importance in the trained model is built on incorrect periodicity measurements.
- **Confirmed by:** code reading
- **Blocks training:** yes — model learns from incorrect periodicity features
- **Blocks production:** yes — inference produces wrong periodogram features

### B2: NaN propagation through silent exception swallowing

- **Severity:** CRITICAL
- **File:** `src/features.py`, lines ~44–55 (`_validate_arrays`) and lines ~300–424 (callers)
- **Root cause:** `_validate_arrays` raises `ValueError("Flux array contains NaN values")` on NaN detection. However, each caller (e.g., `extract_features_from_batch`, `extract_features`) wraps the call chain with `try/except Exception` that catches this `ValueError` and either logs a warning (batch) or raises HTTP 400 (API). In batch mode, the entire feature set for a light curve with NaN flux is silently discarded — no features are returned, training gets an incomplete dataset.
- **Why it matters:** Lightkurve data often contains NaN gaps (pointing maneuvers, cosmic rays, momentum dumps). These are expected, not exceptional. A NaN gap in 10% of cadences should trigger interpolation, masking, or imputation — not silently lose the entire sample.
- **Confirmed by:** code reading
- **Blocks training:** yes — reduces training set and produces silent gaps
- **Blocks production:** yes — API returns 400 for light curves with NaN gaps, even when the gap is small and the rest of the curve is valid

### B3: Tail-mass probability calculation is incorrect

- **Severity:** MEDIUM
- **File:** `src/features.py`, lines ~388–389
- **Root cause:** The tail-mass probability feature computes `np.percentile(flux, threshold)` over the full flux array, then computes probability of flux values exceeding that threshold. However, the threshold is derived **from the same flux distribution**, not from a robust baseline or smoothed model. This effectively measures the probability of extreme values in the same data used to define "extreme." The logic does not subtract a baseline or fit a trend, so long-term stellar variability (not transits) is counted as tail mass.
- **Why it matters:** Tail-mass probability is intended to detect transit-like dips. An incorrect implementation means the feature reports stellar variability noise rather than genuine transit candidates, corrupting model training.
- **Confirmed by:** code reading
- **Blocks training:** yes — injects noisy, non-informative feature
- **Blocks production:** yes — feature is computed during inference with same flawed logic

### B4: `inference.py` — unconditional top-level `from lightkurve import LightCurve`

- **Severity:** HIGH
- **File:** `src/inference.py`, line (top-level import)
- **Root cause:** `preprocessing.py` uses `TYPE_CHECKING` guard: `if TYPE_CHECKING: from lightkurve import LightCurve`, then loads `LightCurve` lazily inside functions. But `inference.py` imports `LightCurve` unconditionally at module level. If `lightkurve` is not installed (e.g., inference-only deployment), the entire module fails to import.
- **Why it matters:** Prevents the API from even starting if lightkurve is missing, even though the API only needs `LightCurve` when processing uploaded files.
- **Confirmed by:** code reading
- **Blocks training:** no
- **Blocks production:** yes — API import failure

### B5: `model.py` — no `__main__` entry point for training

- **Severity:** MEDIUM
- **File:** `src/model.py`
- **Root cause:** `train_pipeline` and `train_model` are defined but never invoked. There is no `if __name__ == "__main__":` block. The only way to train is to write a separate script or import and call explicitly.
- **Why it matters:** Prevents standard `python -m src.model` training workflow. Also, `train_model` signature is `(X, y)` but `prepare_dataset` returns `(X, y, filenames)` — the third return value is silently dropped in `train_pipeline`'s call but would cause a "too many values to unpack" error if called directly.
- **Confirmed by:** code reading
- **Blocks training:** yes — no invocation path
- **Blocks production:** no (model must be pre-trained)

### B6: `model.py` — dataset split before shuffle

- **Severity:** LOW
- **File:** `src/model.py` (in `prepare_dataset` or `train_pipeline`)
- **Root cause:** The data splitting does not shuffle before `train_test_split`. If the data loader returns files in a deterministic order (e.g., all non-transits first, then all transits), the split can produce training sets with no transits and test sets with all transits, or vice versa.
- **Why it matters:** Stratified split is used but if class ordering is sequential, stratified sampling on a sorted array can produce degenerate splits.
- **Confirmed by:** code reading
- **Blocks training:** edge case only
- **Blocks production:** no

### B7: Typo variant name `messsage` in `download.py`

- **Severity:** LOW (cosmetic)
- **File:** `src/download.py`, line ~111
- **Root cause:** Variable name `messsage` instead of `message` in a `logger.warning()` call.
- **Why it matters:** None functional — only a cosmetic typo in a log message variable name.
- **Confirmed by:** code reading
- **Blocks training:** no
- **Blocks production:** no

### B8: API route ordering — `/predict-batch` before `/predict`

- **Severity:** LOW
- **File:** `api/routes.py`
- **Root cause:** `POST /predict-batch` is defined at line 149, `POST /predict` at line 80. While both have different paths and don't conflict, having batch before single predict is unconventional.
- **Why it matters:** None functionally — FastAPI routes by path, not definition order. Style nit only.
- **Confirmed by:** code reading
- **Blocks training:** no
- **Blocks production:** no

### B9: API — no `python-multipart` in requirements

- **Severity:** HIGH
- **File:** `requirements.txt` (missing), `api/routes.py` (uses `File(...)` / `UploadFile`)
- **Root cause:** FastAPI's `File()` / `UploadFile` parsing requires `python-multipart` to be installed. It is not listed in `requirements.txt`. If not transitively installed, the API crashes on any file upload endpoint with `RuntimeError: Form data requires "python-multipart"`.
- **Why it matters:** All three POST endpoints (`/predict`, `/predict-batch`) will fail at runtime.
- **Confirmed by:** code reading + knowledge of FastAPI requirements
- **Blocks training:** no
- **Blocks production:** yes — file uploads crash

### B10: CHANGELOG v1.0.0 dated 2026-06-30

- **Severity:** LOW
- **File:** `CHANGELOG.md`
- **Root cause:** Version 1.0.0 release dated 2026-06-30, which is one day before this audit (2026-07-01).
- **Why it matters:** A future date causes confusion for version tracking and release management.
- **Confirmed by:** code reading
- **Blocks training:** no
- **Blocks production:** no

---

## 3. Engineering Audit Verification

Cross-reference of `misca/engineeringaudit.md` claims against actual code:

| Audit Claim | Verdict | Notes |
|---|---|---|
| Lomb-Scargle frequency units error | **CONFIRMED** | Line ~300, linear freq passed to angular freq function |
| NaN handling gaps | **CONFIRMED** | `_validate_arrays` raises on NaN, callers catch silently |
| Tail-mass probability issue | **CONFIRMED** | Threshold computed from same distribution, not residuals |
| Silent exception swallowing | **CONFIRMED** | `_safe_stat` returns 0.0 on any error (line ~424) |
| `model.py` missing `__main__` | **CONFIRMED** | No entry point, `train_model` and `train_pipeline` never called |
| `inference.py` unconditional lightkurve import | **CONFIRMED** | Not gated by `TYPE_CHECKING` unlike `preprocessing.py` |
| API route ordering | **CONFIRMED** | Batch before predict — cosmetic only |
| `scikit-learn` missing from requirements | **PARTIALLY REFUTED** | `scikit-learn` is in `requirements.txt` line 8 — this was already fixed since the audit |
| `torch`/`torchvision` unused | **CONFIRMED** | No DL code exists in entire repo |
| Training data absence | **CONFIRMED** | `data/raw/` and `data/processed/` are empty |
| No model artifact | **CONFIRMED** | `models/` directory does not exist |
| Typo `messsage` | **NOT FOUND IN AUDIT (new finding)** | Line ~111 in `download.py` |
| `python-multipart` missing | **NOT FOUND IN AUDIT (new finding)** | Critical for API file uploads |
| `pydantic` missing from requirements | **NOT FOUND IN AUDIT (new finding)** | Was not in original `requirements.txt`, now present at line 13 |

---

## 4. Dependency Review

### Installed (requirements.txt)

| Package | Used? | Notes |
|---|---|---|
| numpy | YES | Every module |
| pandas | YES | features.py, preprocessing.py |
| scipy | YES | features.py (lombscargle, stats) |
| astropy | YES | preprocessing.py (fits handling) |
| lightkurve | YES | download.py, preprocessing.py, inference.py |
| matplotlib | NO (via pytest-mpl?) | Listed but no plotting code found |
| joblib | YES | model.py (model persistence), api/main.py (lifespan) |
| scikit-learn | YES | model.py (all classifiers, metrics, split) |
| torch | NO | No PyTorch code anywhere; ~800MB download |
| torchvision | NO | No vision/CNN code anywhere; pulls torch |
| fastapi | YES | api/main.py, api/routes.py |
| uvicorn | YES | api/main.py (run) |
| pydantic | YES | api/schemas.py |
| pytest | YES (dev) | tests/ |
| python-dotenv | YES | config.py |

### Missing requirements (will cause runtime failures)

| Package | Used In | Why It's Missing |
|---|---|---|
| `python-multipart` | `api/routes.py` | FastAPI requires it for `File()` / `UploadFile` parsing |
| `httpx` (or `requests`) | `tests/` (test client) | For `TestClient` or API integration tests |
| `pytest-asyncio` | `tests/` | If any API route tests are written with async |

### Unused dependencies (waste ~900MB+)

| Package | Size | Reason to Remove |
|---|---|---|
| `torch` | ~800MB | No PyTorch code, no neural network anywhere |
| `torchvision` | ~100MB+ | No vision code, pulls torch transitively |
| `matplotlib` | ~15MB | No plotting code found in src/ or api/ |

### Dependency graph issue

`scikit-learn` (line 8) is correctly in `requirements.txt`. The pre-existing audit claimed it was missing, but it was either added since that audit or the audit was incorrect on this point.

---

## 5. ML Pipeline Review

### Pipeline stages

```
download.py ──> preprocessing.py ──> features.py ──> model.py ──> inference.py
    (Lightkurve       (detrend,           (5 category       (sklearn       (predict
     MAST query,      normalize,           feature           classifiers,   from trained
     FITS download)   sigma clip)          extraction)       train/eval)    model)
```

### Data flow issues

1. **Download → Preprocessing:** `download.py` saves FITS files. `preprocessing.py` loads them. No contract validation on flux units or time format between stages.
2. **Preprocessing → Features:** Preprocessing produces a cleaned light curve but does NOT fill NaN gaps — it sigma-clips outliers but `remove_nans` is called in `load_and_preprocess`, so the curve may have fewer samples than the original. Features are then computed on the truncated curve.
3. **Features → Model:** `extract_features_from_batch` catches all errors silently. A feature-extraction failure for one file returns `None`, which is filtered out. No warning is raised about how many samples were discarded.
4. **Model → Inference:** `model.py` never saves a `.joblib` file — there is no persistence step. `inference.py` calls `load_trained_model` which expects a file on disk, but no training pipeline writes one.

### Feature extraction (5 categories)

| Category | Functions | Bug Status |
|---|---|---|
| Statistical | `_flux_statistics_features` | OK |
| Variability | `_variability_features` | OK |
| Periodicity | `_periodicity_features` | **B1** (Lomb-Scargle freq units) |
| Shape-based | `_shape_features` | **B3** (tail-mass probability) |
| General | `_general_features` | OK |

---

## 6. Training Readiness

### What is needed to train right now:

1. **FITS data:** `data/raw/` is empty. Must run `python -m src.download` with valid Kepler/TESS target IDs.
2. **NaN handling:** **B2** blocks training — any light curve with NaN gaps (common in real data) will be silently discarded.
3. **Lomb-Scargle fix:** **B1** — features are computed with wrong frequency units. Training on these features produces a model with incorrect periodicity weights.
4. **Tail-mass fix:** **B3** — feature is not measuring what it claims to measure.
5. **Training entry point:** **B5** — no `__main__` block. Must write one or import manually.

### Training readiness score: **2/10**

The pipeline architecture exists but cannot produce meaningful results due to the three mathematical bugs (B1, B2, B3). Even after fixing those, there is no training data to run on.

---

## 7. Production Readiness

### What is needed to go to production:

1. **All ML bugs fixed:** B1, B2, B3 (same as training)
2. **Lightkurve import guard:** **B4** — API will not start without it
3. **Model persistence:** **B5** — training must produce `random_forest.joblib`
4. **python-multipart:** **B9** — file uploads will crash
5. **requirements.txt cleanup:** Remove `torch`/`torchvision`, add `python-multipart`, add `httpx` for tests
6. **Frontend-API integration:** All 6 pages are mock data — `api.js` functions are imported but never called
7. **Error response consistency:** Batch errors return `BatchItemResult` with `error: str`, single predict raises `HTTPException` — different error shapes
8. **No rate limiting, no auth, no API key:** Acceptable for MVP, not for production
9. **No HTTPS, no production server config:** Uvicorn dev server only
10. **No health check beyond model loaded:** No DB, no external service dependencies to check

### Production readiness score: **1/10**

The API skeleton exists but will crash on first file upload (B9), cannot produce predictions without a trained model (B5), and has incorrect feature extraction logic (B1, B3). The frontend is entirely mock data with zero API calls.

---

## 8. Ordered Bug Fix Plan

### Phase 1: Pipeline correctness (blocks training + production)

| Order | Bug | File | Effort | Priority |
|---|---|---|---|---|
| 1 | B2 — NaN handling | `src/features.py` | Medium | CRITICAL |
| 2 | B1 — Lomb-Scargle freq units | `src/features.py` | Small | HIGH |
| 3 | B3 — Tail-mass probability | `src/features.py` | Small | MEDIUM |

### Phase 2: Training infrastructure (blocks training)

| Order | Bug | File | Effort | Priority |
|---|---|---|---|---|
| 4 | B5 — Training entry point + model persistence | `src/model.py` | Medium | HIGH |

### Phase 3: API reliability (blocks production)

| Order | Bug | File | Effort | Priority |
|---|---|---|---|---|
| 5 | B9 — Add `python-multipart` | `requirements.txt` | Trivial | CRITICAL |
| 6 | B4 — Lightkurve import guard | `src/inference.py` | Small | HIGH |

### Phase 4: Quality of life

| Order | Bug | File | Effort | Priority |
|---|---|---|---|---|
| 7 | B6 — Dataset split shuffle | `src/model.py` | Trivial | LOW |
| 8 | B7 — Typo `messsage` | `src/download.py` | Trivial | LOW |
| 9 | B10 — CHANGELOG date | `CHANGELOG.md` | Trivial | LOW |
| 10 | B8 — Route ordering | `api/routes.py` | Trivial | LOW |

### Phase 5: Cleanup

| Order | Task | File | Effort | Priority |
|---|---|---|---|---|
| 11 | Remove `torch`/`torchvision` | `requirements.txt` | Small | MEDIUM |
| 12 | Frontend API integration | `frontend/` | Large | MEDIUM |
| 13 | Test coverage expansion | `tests/` | Large | MEDIUM |
| 14 | Production config (auth, rate limit, HTTPS) | `api/`, `config.py` | Medium | LOW |

---

*End of report. This is a pre-fix analysis only — no source code was modified.*
