# Engineering Audit Report: Exoplanet Transit Hunter

## Executive Summary
The `exoplanet-transit-hunter` repository is a well-structured, production-oriented project for exoplanet detection. It demonstrates high professional standards in modularity, logging, and configuration. However, the system is currently **unfit for production release** due to critical mathematical bugs in the feature engineering pipeline and incomplete implementation of the core API and Frontend integration.

---

## 1. Bugs & Critical Issues

### [Critical] Physical/Mathematical Bug in Lomb-Scargle Computation
*   **File:** `src/features.py` (Line 300)
*   **Description:** The code uses `scipy.signal.lombscargle` with linear frequencies (cycles/day), but the function strictly expects **angular frequencies** (radians/day).
*   **Why it is a problem:** Periodicity features (e.g., `ts_ls_peak_period`) will be incorrect by a factor of $2\pi$. The ML model will be trained on physically invalid data, leading to total failure on real-world validation.
*   **Recommended Fix:** Multiply the frequency array by `2 * np.pi` before passing it to `lombscargle`.

### [Critical] Incomplete System Implementation
*   **Files:** `api/main.py`, `frontend/src/main.jsx`
*   **Description:** The API contains only a health check endpoint. The Frontend is a static mockup with hardcoded data and no communication logic.
*   **Why it is a problem:** The primary goal (detecting transits and serving results) is entirely unimplemented at the system level.
*   **Recommended Fix:** Implement `POST /predict` and `GET /search` endpoints in FastAPI and connect the React frontend using state-managed data fetching.

### [High] NaN-Propagation Bug in Feature Validation
*   **File:** `src/features.py` (Lines 44-55)
*   **Description:** `_validate_arrays` identifies non-finite (NaN/Inf) values but returns the original arrays without filtering them.
*   **Why it is a problem:** `np.median` and `np.min` in downstream functions are not NaN-aware. A single NaN in the input will cause the entire feature vector to become `NaN`.
*   **Recommended Fix:** Apply the `valid` boolean mask to `time_arr` and `flux_arr` inside `_validate_arrays`.

### [High] Mathematical Error in Probability Mass
*   **File:** `src/features.py` (Lines 349-350, 365)
*   **Description:** `tail_mass` and `concentration` sum histogram **densities** instead of actual probability masses.
*   **Why it is a problem:** The sum of densities is not 1.0 (it depends on bin width); these features are mathematically inconsistent across different data scales.
*   **Recommended Fix:** Use `density=False` and normalize by the sum, or multiply densities by bin width.

### [High] Missing CORS Middleware
*   **File:** `api/main.py`
*   **Description:** No Cross-Origin Resource Sharing (CORS) configuration in the FastAPI app.
*   **Why it is a problem:** Browser security (SOP) will block the React frontend from calling the API, preventing any integration from working.
*   **Recommended Fix:** Add `fastapi.middleware.cors.CORSMiddleware`.

---

## 2. Machine Learning & Performance

### [Medium] Weak Model Architecture (Architecture Smell)
*   **File:** `src/model.py` (Lines 43-55)
*   **Description:** `TransitClassifier` uses a single 1D conv layer followed by global average pooling.
*   **Why it is a problem:** Global average pooling washes out localized, short-duration transit signals. This significantly limits model performance on small transit events.
*   **Recommended Fix:** Use a deeper architecture with Max-Pooling or multiple blocks to preserve signal resolution.

### [Medium] Aggressive NaN Removal in Preprocessing
*   **File:** `src/preprocessing.py` (Lines 244-248)
*   **Description:** `remove_nan` discards samples if `flux_error` is NaN, even if `flux` is valid.
*   **Why it is a problem:** Kepler/TESS data often have missing error bars while flux remains valid. This causes unnecessary data loss.
*   **Recommended Fix:** Make `flux_error` filtering optional.

### [Medium] Unpinned Dependencies
*   **File:** `requirements.txt`
*   **Description:** No versions are pinned for core libraries (numpy, pandas, torch, etc.).
*   **Why it is a problem:** Future installs may pull incompatible versions, breaking the pipeline (e.g., NumPy 2.0 breaking changes).
*   **Recommended Fix:** Pin all dependencies to specific versions (e.g., `numpy==1.26.4`).

---

## 3. Improvements & Style

### [Medium] Dead Dependency
*   **File:** `requirements.txt`
*   **Description:** `torchvision` is included but never imported or used.
*   **Recommended Fix:** Remove `torchvision`.

### [Low] Unused Parameters
*   **File:** `src/features.py` (Line 114)
*   **Description:** `window_size` is explicitly marked as "unused".
*   **Recommended Fix:** Remove the parameter or implement the intended local-context logic.

### [Low] Magic Numbers
*   **File:** `src/features.py`
*   **Description:** Value `1.4826` (MAD to STD conversion) is used without explanation.
*   **Recommended Fix:** Define a constant `MAD_TO_STD = 1.4826`.

---

## Conclusion
The project has a solid engineering foundation but requires high-priority fixes to the mathematical logic in `src/features.py` and the implementation of core API endpoints before it can be considered production-ready.

**Audit Phase Complete.** No code changes have been made.
