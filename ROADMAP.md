# Roadmap

## Completed

### v1.1.0 — Scientific Correctness Fixes (current)

Three critical bugs in the feature engineering module were identified, fixed, and
verified with regression tests:

| Fix | Module | Description |
|-----|--------|-------------|
| **B1** — Lomb-Scargle periodogram | `src/features.py` | `angular_freqs` now correctly uses `linspace(...) * 2π`; `peak_period` computed as `2π / peak_freq`. Old code produced periods off by 2π (~1.0 day instead of ~5.0 days). |
| **B2** — NaN propagation | `src/features.py` | `_validate_arrays` now returns `time_arr[valid], flux_arr[valid]` (filtered). Old code returned unfiltered arrays, allowing NaN to poison `np.diff`, `np.corrcoef`, etc. |
| **B3** — Histogram probability normalization | `src/features.py` | `density=False` with explicit `total = np.sum(counts)` normalization. Old code used `density=True` (PDF, sum ≠ 1) and no total normalization, producing `tail_mass > 1`. |

## Known Issues (not yet addressed)

Remaining engineering gaps from the full audit:

| Priority | Issue | Area |
|----------|-------|------|
| **High** | No trained model persisted — prediction endpoints return 503 | `models/` |
| **High** | No training workflow script (`train.py`) | Pipeline |
| **Medium** | `flux_error` NaN removal hardcoded, not configurable | `preprocessing.py` |
| **Medium** | Unpinned dependencies (`numpy`, `scikit-learn`, etc.) | `requirements.txt` |
| **Medium** | `torch` / `torchvision` dead weight (~800 MB, never imported) | `requirements.txt` |
| **Low** | Unused `window_size` parameter in noise features | `features.py` |
| **Low** | Magic numbers `1.4826` (MAD→std), `3.0` (sigma clip) — no named constants | `features.py` |
| **Low** | 4+ test suites claimed in `checklist.md` but do not exist | Tests |

## Future Work

1. **Model training pipeline** — create `scripts/train.py` to fit
   `RandomForestClassifier` and persist via `joblib`; validate with
   cross-validation metrics.
2. **Configurable NaN handling** — expose a `drop_na` parameter in
   preprocessing; allow different strategies (drop, fill, interpolate).
3. **Dependency hygiene** — pin all versions in `requirements.txt`; remove
   unused `torch`/`torchvision`.
4. **Test coverage** — write tests for `preprocessing.py` (flux NaN handling,
   pipeline edge cases) and `inference.py` (model loading, prediction
   fallbacks).
5. **Refactor** — extract magic numeric constants into module-level named
   constants; remove dead parameters.

---

# Detailed Development Plan

> **Vision**
>
> Build a scientifically credible, reproducible, and maintainable exoplanet detection pipeline capable of downloading, preprocessing, extracting features from, and classifying Kepler/TESS light curves with high reliability.

## Guiding Principles

* **Correctness before optimization**
* **Scientific validity before performance**
* **Reliability before scale**
* **Keep It Simple (KISS)**
* **Avoid Premature Optimization (YAGNI)**
* **Every prediction should be reproducible**

---

## Phase 1 — Reliability Foundation

**Status:** In Progress

Goal: Build a stable and trustworthy pipeline before adding new features.

### 1. Identifier Normalization

Ensure every astronomical target is normalized before any query.

Examples:
- `10000162` → `KIC 10000162`
- `123456789` → `TIC 123456789`

Why?
- Faster Lightkurve lookups
- Removes ambiguity
- Consistent dataset generation

### 2. Replace Broad Exception Handling

Remove `except Exception:` with specific exceptions.

Benefits:
- Easier debugging
- Better error messages
- Prevent hidden bugs

### 3. Robust Download Pipeline

Implement:
- retry logic
- exponential backoff
- configurable timeout
- graceful handling of HTTP 429, 500, 503

Goal: Never fail permanently because NASA's servers are slow.

### 4. FITS Validation

Before caching:
- verify file exists
- verify FITS structure
- detect corruption
- redownload invalid files

Goal: Never process corrupted astronomical data.

### 5. Structured Timing Logs

Measure every pipeline stage.

Example:
```
Search........0.82 s
Download....31.41 s
Preprocess...0.08 s
Features.....0.15 s
Prediction...0.01 s

TOTAL........32.47 s
```

Goal: Never guess where performance problems occur.

---

## Phase 2 — Scientific Reproducibility

Goal: Every prediction should be reproducible months or years later.

For every processed target, log:
- Target ID, Observation ID
- Pipeline version, Feature version, Model version
- Detrending method, Window size, Sigma clipping threshold
- Normalization method, Processing timestamp
- Prediction score, Model confidence

Example:
```json
{
  "target": "KIC 10000162",
  "pipeline_version": "1.2.0",
  "feature_version": "v2",
  "model": "rf_v3.pkl",
  "detrending": "SavGol",
  "window": 101,
  "prediction": 0.97
}
```

Goal: Every result should be explainable and reproducible.

---

## Phase 3 — Scientific Improvements

Goal: Increase scientific accuracy instead of computational speed.

### Adaptive Detrending

Current: Fixed Savitzky-Golay window (101)

Future: Window depends on cadence, observation duration, expected transit duration, stellar variability.

Goal: Avoid removing real transits.

### Feature Engineering Review

Audit every feature for redundancy, instability, weakness, and scientific soundness. Replace with stronger astrophysical features.

### Leakage Prevention

Audit train/test split, preprocessing, feature extraction, target grouping. Ensure observations from the same target never leak across datasets.

### Scientific Validation

Evaluate against confirmed exoplanets, false positives, and eclipsing binaries.

Measure: Precision, Recall, F1, ROC-AUC.

---

## Phase 4 — Engineering Improvements

Goal: Improve developer experience without increasing unnecessary complexity.

### Configuration

Migrate configuration to Pydantic BaseSettings. Benefits: type safety, validation, clearer configuration.

### In-Memory Inference

Avoid upload→temp file→read again. Use upload→memory→prediction to reduce unnecessary disk I/O.

### Better Logging

Include timestamps, processing durations, target IDs, warning levels, error context.

---

## Phase 5 — Developer Productivity

(Only after Phases 1–4 are complete.)

### Parallel Downloads

```python
ThreadPoolExecutor(max_workers=4)
```

Reasons: Faster dataset generation, minimal complexity, easy debugging, no asyncio event loop.

Do NOT implement asyncio, aiohttp, Ray, or Dask at this stage.

---

## Phase 6 — Machine Learning Improvements

Review feature importance, feature selection, hyperparameter tuning, cross-validation, class imbalance, calibration.

Potential future models: XGBoost, LightGBM, CatBoost — only if they demonstrate measurable improvements.

---

## Phase 7 — API Improvements

Implement authentication, rate limiting, request validation, better error responses, OpenAPI improvements.

Goal: Prepare for public deployment.

---

## Phase 8 — Large Dataset Optimization

(Only after the entire scientific pipeline has been validated.)

Possible additions: async HTTP, advanced caching, download queues, checkpointing, resumable dataset generation.

Only implement after profiling identifies genuine bottlenecks.

---

## Phase 9 — Research Features

Potential future additions:
- Transit Least Squares (TLS)
- BLS (Box Least Squares)
- Lomb-Scargle improvements
- Multi-quarter stitching
- TESS support
- Gaia integration
- Stellar parameter enrichment
- Explainable AI (SHAP)
- Automated report generation

---

## Deliberately Avoid (For Now)

The following are intentionally postponed to avoid unnecessary complexity:

- Ray, Dask, Kubernetes, Microservices
- Distributed computing, GPU clusters
- Async architecture, Message queues, Event-driven systems

These should only be introduced when profiling proves they are necessary.

---

## Long-Term Vision

The long-term goal is to create an open-source exoplanet analysis toolkit that is:
- Scientifically credible
- Fully reproducible
- Modular
- Well documented
- Easy to extend
- Suitable for education and research
- Capable of processing both Kepler and TESS light curves

Success is measured not by how many stars the pipeline processes, but by how reliably and correctly it identifies planetary transits.
