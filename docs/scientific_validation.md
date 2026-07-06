# Scientific Validation Audit

> **Objective:** Systematically audit the Exoplanet Transit Hunter pipeline for data leakage, label correctness, and scientific reproducibility.
>
> **Auditor:** AI-assisted static analysis of source code at commit `HEAD`.
>
> **Date:** 2026-07-06

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Methodology](#2-methodology)
3. [Pipeline Architecture](#3-pipeline-architecture)
4. [Leakage Vector Analysis](#4-leakage-vector-analysis)
    - [V1: Preprocessing — Per-Curve Statistics](#v1-preprocessing--per-curve-statistics)
    - [V2: Feature Extraction — Per-Curve Features](#v2-feature-extraction--per-curve-features)
    - [V3: Train / Test Split — Missing Group Constraints](#v3-train--test-split--missing-group-constraints)
    - [V4: Cross-Validation — Missing Group Constraints](#v4-cross-validation--missing-group-constraints)
    - [V5: Feature Scaling — No Global Normalization](#v5-feature-scaling--no-global-normalization)
    - [V6: Inference — No Training Data Reuse](#v6-inference--no-training-data-reuse)
5. [Label Quality Assessment](#5-label-quality-assessment)
6. [Reproducibility Assessment](#6-reproducibility-assessment)
7. [Recommended Fixes](#7-recommended-fixes)
8. [Validation Roadmap](#8-validation-roadmap)
9. [Appendix: Code References](#9-appendix-code-references)

---

## 1. Executive Summary

The pipeline has **two confirmed data leakage vectors** and **one medium-severity label-quality issue**:

| # | Vector | Status | Severity | Component |
|---|--------|--------|----------|-----------|
| V1 | Preprocessing per-curve | ✅ Clean | — | `src/preprocessing.py` |
| V2 | Feature extraction per-curve | ✅ Clean | — | `src/features.py` |
| **V3** | **Train/test split (same-star leakage)** | ✅ **Fixed** | — | `src/model.py:split_dataset` |
| **V4** | **Cross-validation (same-star leakage)** | ✅ **Fixed** | — | `src/model.py:cross_validate_model` |
| V5 | Feature scaling | ✅ Clean | — | `src/model.py:prepare_dataset` |
| V6 | Inference pipeline | ✅ Clean | — | `src/inference.py` |
| L1 | CANDIDATE disposition mapped to negative | ✅ Fixed | — | `scripts/train.py:_load_from_excel` |

**Bottom line:** Both same-star leakage vectors have been fixed. Cross-validation now uses `StratifiedGroupKFold` to keep all TCEs from the same star within the same fold while maintaining stratification.

---

## 2. Methodology

The audit was conducted via full static analysis of every source file in the training and inference pipeline:

1. **Read every function call chain** from data loading through prediction.
2. **Identify each point where aggregate statistics are computed** and verify they respect per-sample independence.
3. **Verify split boundaries** — do samples from the same source cross train/test or CV fold boundaries?
4. **Check inference isolation** — does inference re-use any statistics from the training set?
5. **Assess label quality** — are the ground-truth labels scientifically sound?

---

## 3. Pipeline Architecture

```
Kepler FITS files
    │
    ▼
src/preprocessing.py         Per-curve: detrend, normalize, sigma-clip, fill-NaN
    │
    ▼
src/features.py               Per-curve: statistical, noise, transit, timeseries, distribution
    │
    ▼
scripts/train.py              _load_from_excel → prepare_dataset → split_dataset → train → evaluate → CV
    │
    ▼
src/inference.py              Load model → preprocess → extract features → predict
```

**Key architectural property:** Every step from raw data through features is **per-light-curve**. No global statistics are accumulated across samples. The leakage appears only at the **dataset splitting stage**.

---

## 4. Leakage Vector Analysis

### V1: Preprocessing — Per-Curve Statistics

**Status:** ✅ Clean

**File:** `src/preprocessing.py`

Every preprocessing function operates on a single light curve array:

| Function | Computation | Scope |
|----------|-------------|-------|
| `detrend` | Savitzky–Golay filter | Single curve |
| `normalize` | `(flux - median) / mad` | Single curve |
| `sigma_clip` | Iterative MAD-based clipping | Single curve |
| `fill_nan` | Forward-fill + median fill | Single curve |

**No StandardScaler, no global mean/variance, no cross-curve statistics.**

**Verdict:** No leakage possible through preprocessing.

---

### V2: Feature Extraction — Per-Curve Features

**Status:** ✅ Clean

**File:** `src/features.py`

`extract_features(time, flux)` takes a single `(time, flux)` pair and returns a dict of features:

| Feature group | Functions | Uses global data? |
|--------------|-----------|-------------------|
| Statistical | `extract_statistical_features` | No — single array |
| Noise | `extract_noise_features` | No — single array |
| Transit | `extract_transit_features` | No — single array |
| Timeseries | `extract_timeseries_features` | No — single array |
| Distribution | `extract_distribution_features` | No — single array |

`extract_features_from_batch` loops over `batch` and calls `extract_features` per sample. Features are then aggregated into a list of dicts. **No aggregation across samples occurs during feature extraction.**

**Verdict:** No leakage possible through feature extraction.

---

### V3: Train / Test Split — Missing Group Constraints

**Status:** ✅ **Fixed**

**File:** `src/model.py`, lines 160–189

**Fix applied:** `split_dataset` now accepts an optional `groups` parameter. When provided, it uses `GroupShuffleSplit` instead of `train_test_split`, ensuring all samples from the same star stay together in either the train or test set.

```python
def split_dataset(dataset, test_size=0.2, random_state=None, groups=None):
    seed = random_state if random_state is not None else settings.random_seed
    if groups is not None:
        gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
        train_idx, test_idx = next(gss.split(dataset.X, dataset.y, groups=groups))
        return dataset.X[train_idx], dataset.X[test_idx], dataset.y[train_idx], dataset.y[test_idx]
    ...
```

**Test coverage:** `TestCrossValidateModel.test_grouped_split_keeps_stars_together` verifies that a star's samples never cross the train/test boundary.

---

### V4: Cross-Validation — Missing Group Constraints

**Status:** ✅ **Fixed**

**File:** `src/model.py`, lines 414–487

**Fix applied:** `cross_validate_model` now uses `StratifiedGroupKFold` when `groups` is provided, instead of `StratifiedKFold`. This simultaneously enforces group integrity (same-star samples stay in the same fold) and maintains class stratification.

```python
if groups is not None:
    skf = StratifiedGroupKFold(n_splits=cv, shuffle=True, random_state=seed)
else:
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=seed)
for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y, groups=groups)):
    ...
```

**Fallback:** When `groups` is `None`, the original `StratifiedKFold` behavior is preserved — no unnecessary behavior change for non-grouped usage.

**Test coverage:** `TestCrossValidateModel.test_grouped_cv_keeps_stars_together` verifies that grouped cross-validation runs without error and produces sensible results.

---

### V5: Feature Scaling — No Global Normalization

**Status:** ✅ Clean

**File:** `src/model.py`, `prepare_dataset` (lines 118–152)

`prepare_dataset` converts dict features to a matrix and builds a `Dataset(X, y)`. **No StandardScaler, RobustScaler, or any other global normalization is applied.** Features are passed raw to the model.

This is actually correct because Random Forest and Gradient Boosting are **tree-based models** — they are invariant to monotonic feature transformations. No scaling is needed, and no scaling leakage can occur.

**Verdict:** Clean. (If a future model requires scaling — e.g. logistic regression, SVM, neural network — the scaler must be **fit on training data only** and used to transform both test and inference data.)

---

### V6: Inference — No Training Data Reuse

**Status:** ✅ Clean

**File:** `src/inference.py`

The inference pipeline:
1. Loads a raw FITS file
2. Preprocesses per-curve (same as V1)
3. Extracts features per-curve (same as V2)
4. Calls `model.predict()` on the extracted features

No training data statistics, no saved scaler, no reference to training labels. The model file is self-contained.

**Verdict:** No leakage through inference.

---

## 5. Label Quality Assessment

### L1: CANDIDATE → Negative Mapping

**Status:** ⚠️ **Label Noise — MEDIUM**

**File:** `scripts/train.py`, lines 61–63

```python
y = np.array(
    [1.0 if v == "confirmed" else 0.0 for v in raw],
    dtype=np.float64,
)
```

**Problem:** The NASA Kepler catalog labels have three dispositions:

| Label | Meaning | Mapped to |
|-------|---------|-----------|
| `CONFIRMED` | Validated exoplanet | `1.0` (positive) |
| `CANDIDATE` | Likely but not yet confirmed | `0.0` (negative) |
| `FALSE POSITIVE` | Instrumental/astrophysical false alarm | `0.0` (negative) |

Mapping `CANDIDATE` to the negative class introduces label noise because:
- Many CANDIDATEs are **real planets** awaiting confirmation.
- The model is trained to treat probable planets as non-detections.
- This artificially depresses recall and teaches the model that borderline transit signals are negative.

**Alternative approaches** (in order of preference):

| Approach | Pros | Cons |
|----------|------|------|
| **Exclude CANDIDATEs** from training | Clean labels; model sees only confident examples. | Reduces training set size. |
| **Three-class classification** (CONFIRMED / CANDIDATE / FP) | Matches the real scientific question. | More complex; CANDIDATE class is ambiguous by nature. |
| **Weighted loss** for CANDIDATEs | Soft-label approach; preserves data. | Adds complexity; weight selection is arbitrary. |

**Recommendation:** Exclude CANDIDATE samples from the training set. Train only on CONFIRMED vs FALSE POSITIVE. This is the standard practice in astrophysical transit classification literature.

---

## 6. Reproducibility Assessment

### What is tracked

The pipeline records:
- `random_state` (seeds for all splits and models)
- `settings.random_seed` as the global default

### What is NOT tracked (NEEDED)

A reproducible prediction requires:

| Metadata | Status | Action |
|----------|--------|--------|
| Target / KIC ID | ❌ Missing | Add to prediction output |
| Pipeline version | ❌ Missing | Use `git describe` or a version string |
| Feature version | ❌ Missing | Hash of feature function list |
| Model version | ❌ Missing | Hash of model file + hyperparameters |
| Detrending parameters | ❌ Missing | Add window, method to provenance |
| Normalization method | ❌ Missing | Add median/MAD to provenance |
| Processing timestamp | ❌ Missing | Record in prediction output |

**Recommendation:** Add a `Provenance` dataclass that records all pipeline parameters and attach it to every prediction.

---

## 7. Recommended Fixes

### P0 — Fix Same-Star Leakage (V3 + V4)

**Scope:** `src/model.py` — `Dataset`, `split_dataset`, `cross_validate_model`

**Changes needed:**

1. **Add `star_id` field to the `Dataset` dataclass** (or a generic `groups` array).

2. **Modify `_load_from_excel` in `scripts/train.py`** to read and propagate the star identifier column.

3. **Update `split_dataset`** to accept an optional `groups` parameter and pass it as `GroupShuffleSplit` or use `train_test_split(..., stratify=groups)` to ensure same-star samples stay together.

4. **Update `cross_validate_model`** to pass `groups` to `StratifiedKFold.split(X, y, groups=groups)`.

### P1 — Fix CANDIDATE Label Handling (L1) ✅

**Scope:** `scripts/train.py` — `_load_from_excel`

**Change:** Replaced `--exclude-candidates` with `--candidate-policy {exclude,negative,separate}`. The `exclude` policy (default) filters out rows where `koi_disposition == "CANDIDATE"`, training only on CONFIRMED vs FALSE POSITIVE. The `negative` policy maps CANDIDATE to class 0.0 alongside FALSE POSITIVE. The `separate` policy raises `NotImplementedError` (reserved for future three-class support).

### P2 — Add Provenance Tracking

**Scope:** New `Provenance` dataclass, integrated into `inference.py`

**Change:** Every prediction output should include:
- Target/Source ID
- Pipeline version (git commit hash)
- Feature list hash
- Preprocessing parameters
- Prediction timestamp

---

## 8. Validation Roadmap

```
Phase 1: Fix Leakage (Current Sprint)
├── Add groups (star_id) to Dataset
├── Fix split_dataset with GroupShuffleSplit
├── Fix cross_validate_model with groups
└── Retrain and re-evaluate with honest metrics

Phase 2: Label Quality (Current)
├── Add `--candidate-policy` CLI (exclude / negative / separate)
└── Evaluate impact on model performance

Phase 3: Scientific Benchmarking
├── Evaluate against known Kepler planets
├── Compare with published catalogs (Thompson et al. 2018)
├── Compute precision/recall vs period, SNR, stellar type
├── Measure false positive rate on known eclipsing binaries
└── Publish benchmark metrics

Phase 4: Provenance
├── Add Provenance dataclass
├── Log preprocessing parameters to prediction output
├── Add pipeline version tracking
└── Make every prediction fully reproducible

Phase 5: Feature Engineering Review
├── Audit all features for predictive power
├── Identify redundant / weak features
├── Remove scientifically questionable features
└── Validate feature stability across similar targets
```

---

## 9. Appendix: Code References

| Component | File | Key Lines |
|-----------|------|-----------|
| Preprocessing | `src/preprocessing.py` | `preprocess_pipeline`, `detrend`, `normalize`, `sigma_clip` |
| Feature extraction | `src/features.py` | `extract_features`, `extract_features_from_batch` |
| Dataset preparation | `src/model.py` | 118–152: `prepare_dataset` |
| Train/test split | `src/model.py` | 160–189: `split_dataset` (V3) |
| Cross-validation | `src/model.py` | 414–487: `cross_validate_model` (V4) |
| Training script | `scripts/train.py` | 49–72: `_load_from_excel` (L1) |
| Inference | `src/inference.py` | `predict_from_lightcurve`, `predict_file` |
