# 🚀 Exoplanet Transit Hunter Roadmap

> **Vision**
>
> Build a scientifically credible, reproducible, and maintainable exoplanet detection pipeline capable of downloading, preprocessing, extracting features from, training on, and classifying Kepler/TESS light curves with high reliability.

---

# Current Milestone — v1.3

The engineering foundation and first model are complete.

The current objective is to fix the identified data leakage vectors, establish scientifically honest evaluation metrics, and make every prediction reproducible.

Current priorities:

* Fix same-star train/test and CV leakage (V3/V4).
* Fix CANDIDATE label handling (L1).
* Re-train and re-evaluate with honest metrics.
* Implement provenance tracking for reproducibility.

---

# Guiding Principles

* Correctness before optimization.
* Scientific validity before performance.
* Reliability before scale.
* Keep It Simple (KISS).
* Avoid Premature Optimization (YAGNI).
* Every prediction should be reproducible.
* Every scientific change should be supported by evidence.

---

# ✅ Completed (v1.2)

## Leakage Audit

### V3/V4 — Same-Star Train/Test and CV Leakage

* Identified: `split_dataset` and `cross_validate_model` do not constrain same-star samples.
* Multiple TCEs from the same star leak across test/CV boundaries.
* Severity: High — all evaluation metrics are over-optimistic.
* Fix planned: Add `groups` (star_id) parameter to `Dataset`, use `GroupShuffleSplit`.

---

### L1 — CANDIDATE Label Noise

* Identified: CANDIDATE disposition mapped to negative (0.0) alongside FALSE POSITIVE.
* Many CANDIDATEs are real planets — this introduces label noise.
* Fixed: Added `--candidate-policy` flag (`exclude`|`negative`|`separate`). `exclude` removes CANDIDATE rows; `negative` maps them to class 0.0.

---

## Scientific Correctness

### B1 — Lomb–Scargle Frequency Bug

* Corrected angular frequency conversion (`2π`).
* Corrected peak period computation.
* Added regression tests.

---

### B2 — NaN Propagation Bug

* Fixed array validation.
* Invalid samples are removed before feature extraction.
* Prevents NaN contamination throughout the pipeline.

---

### B3 — Histogram Probability Normalization

* Replaced PDF normalization with probability mass normalization.
* Fixed incorrect tail mass computation.
* Added regression tests.

---

## Reliability

Completed:

* Identifier normalization (KIC/TIC support)
* Download retry logic
* Configurable download timeout
* Improved exception handling
* Structured timing instrumentation
* FITS validation improvements

---

## Engineering

Completed:

* Migration to Pydantic BaseSettings
* Centralized configuration
* In-memory preprocessing support
* Improved logging utilities
* Modular preprocessing pipeline
* Better download configuration

---

## Testing

Completed:

* 34 automated tests passing
* Regression tests for scientific correctness bugs
* Feature extraction validation
* Statistical feature tests

---

## Documentation

Completed:

* CHANGELOG
* ROADMAP
* Graphify synchronization
* Scientific audit reports

---

## Repository

Completed:

* Canonical repository migrated to

```
E:\A.G\dev_projects\01-exoplanet-transit-hunter
```

* Repository cleanup
* Branch consolidation
* Git history synchronization

---

# 🔴 Current High Priority

## 1. Fix Data Leakage

Status: Diagnosis complete — fixes pending

### V3/V4 — Same-Star Leakage

Add group-aware splitting to prevent same-star leakage:

* Add `star_id` (groups) field to `Dataset`.
* Replace `train_test_split` with `GroupShuffleSplit` in `split_dataset`.
* Pass `groups` parameter to `StratifiedKFold.split()` in `cross_validate_model`.

### L1 — CANDIDATE Label Noise

* Added `--candidate-policy` flag (`exclude`/`negative`/`separate`) to training script.
* Train only on CONFIRMED vs FALSE POSITIVE.

### Deliverables

* `models/random_forest_v2.joblib` — leakage-free retrained model
* `docs/benchmark_report.md` — honest evaluation metrics

---

## 2. Scientific Reproducibility

Status: Pending

Every processed target should record:

* Target ID
* Observation ID
* Pipeline version
* Feature version
* Model version
* Detrending method
* Window size
* Sigma clipping threshold
* Normalization method
* Processing timestamp
* Prediction score
* Confidence

Goal:

Every prediction should be reproducible months or years later.

---

## 3. Scientific Improvements

Status: Pending

### Adaptive Detrending

Replace the fixed Savitzky–Golay window with an adaptive strategy based on:

* cadence
* observation duration
* expected transit duration
* stellar variability

Goal:

Preserve real transit signals.

---

### Feature Engineering Review

Audit every extracted feature.

Identify:

* redundant features
* weak predictors
* unstable features
* scientifically questionable features

Replace only where evidence supports improvement.

---

### Scientific Validation

Benchmark against:

* Confirmed Kepler planets
* KOIs
* False positives
* Eclipsing binaries

Evaluate:

* Precision
* Recall
* F1
* ROC-AUC
* Confusion Matrix

---

# 🟡 Medium Priority

## Configuration Improvements

* Configurable NaN handling
* Additional preprocessing options
* Better validation

---

## Dependency Hygiene

* Pin package versions
* Remove unused dependencies
* Improve reproducibility

---

## Test Coverage

Expand automated tests for:

* preprocessing
* download
* inference
* model training
* API

---

## Code Quality

* Remove unused parameters
* Replace magic numbers with named constants
* Continue reducing technical debt

---

# 🟢 Low Priority

## API

* Authentication
* Rate limiting
* Better OpenAPI documentation
* Improved error responses

---

## Performance

After scientific validation:

* ThreadPoolExecutor downloads
* Smarter caching
* Faster dataset generation

Do **not** introduce:

* asyncio
* aiohttp
* Ray
* Dask
* distributed computing

unless profiling demonstrates a real need.

---

# 🔬 Future Research

Potential future additions:

* Transit Least Squares (TLS)
* Box Least Squares (BLS)
* Multi-quarter stitching
* TESS support
* Gaia integration
* Stellar parameter enrichment
* Explainable AI (SHAP)
* Transit morphology classification
* Automated scientific reports

---

# 🚫 Explicitly Out of Scope (For Now)

The following are intentionally postponed:

* Ray
* Dask
* Kubernetes
* Microservices
* GPU clusters
* Event-driven architectures
* Distributed systems

These will only be considered after scientific correctness and profiling justify the added complexity.

---

# Version Roadmap

## v1.2 — Scientific Foundation

✅ Reliability complete

✅ Engineering foundation complete

✅ Scientific correctness bugs fixed

✅ Regression tests

✅ Model training (baseline Random Forest trained)

✅ Data leakage audit (report written)

⬜ Scientific reproducibility

⬜ Adaptive detrending

⬜ Benchmarking

---

## v1.3 — First Validated ML Pipeline (Current)

✅ Model training pipeline complete

✅ Data leakage audit complete

⬜ Fix same-star train/test and CV leakage

✅ Fix CANDIDATE label handling

⬜ Leakage-free retrained model

⬜ Honest evaluation metrics report

⬜ Provenance tracking

⬜ Validation against Kepler catalog

---

## v2.0 — Research-Grade Toolkit

Goals:

* TLS/BLS integration
* TESS support
* Gaia integration
* Explainable AI
* Advanced transit detection
* Research-quality benchmarking

---

# Definition of Success

The project is considered successful when it:

* Produces scientifically credible predictions.
* Is fully reproducible.
* Is well documented.
* Is modular and easy to extend.
* Supports both education and research.
* Can reliably classify exoplanet transit candidates using real astronomical data.

Success is measured not by the number of stars processed, but by the correctness, reproducibility, and scientific credibility of the results.
