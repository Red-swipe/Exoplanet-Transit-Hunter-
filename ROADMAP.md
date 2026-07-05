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
