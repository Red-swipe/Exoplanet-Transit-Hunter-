# Comprehensive Architectural and Technical Review: Exoplanet Transit Hunter

## Executive Summary
The Exoplanet Transit Hunter project is a well-structured Python-based pipeline for the automated classification of exoplanet transits. It demonstrates a clear separation between data acquisition, preprocessing, feature engineering, and inference. The codebase is generally high quality, with consistent logging and a modular design. However, there are significant opportunities for improvement in high-scale performance, scientific robustness (particularly in detrending and feature engineering), and machine learning lifecycle management.

---

## 1. Repository Architecture
*   **Module Organization:** The project follows a clean separation of concerns. `src/` contains the core business logic, while `api/` handles the RESTful interface. This structure supports maintainability and testing.
*   **Separation of Responsibilities:**
    *   `download.py`: Data acquisition from MAST via Lightkurve.
    *   `preprocessing.py`: Signal processing (normalization, detrending, outlier removal).
    *   `features.py`: Engineering of 36 distinct astrophysical features.
    *   `model.py`: Model training, evaluation, and persistence logic.
*   **Dependency Flow:** Flow is generally unidirectional (API -> Source -> Config), which is excellent for reducing circular dependencies.
*   **Configuration:** Managed via `config.py` and `dotenv`.
    *   *Issue:* Lack of schema validation for environment variables.
    *   *Recommendation:* Use Pydantic's `BaseSettings` for robust configuration management.
*   **Coupling:** Some tight coupling exists between the inference logic and the Lightkurve library's internal objects, which could make future transitions to other data sources (like simulated data or TESS-SPOC) more difficult.

---

## 2. Data Pipeline Review
1.  **Target → Search:** Uses `lk.search_lightcurve`.
    *   *Risk:* Bare numeric IDs cause significant latency (up to 8x slower than prefixed IDs).
2.  **Download → FITS:** Downloads are cached in `data/raw`.
    *   *Risk:* No check for partial downloads; a corrupted FITS file might be cached and re-used.
3.  **Preprocessing:** Includes NaN removal, median normalization, Savgol detrending, and sigma clipping.
    *   *Risk:* `remove_nan` (src/preprocessing.py:31) simply drops non-finite samples. This ignores the temporal gaps, which can introduce artifacts in frequency-domain features (like Lomb-Scargle).
4.  **Feature Extraction:** Merges five categories of features (Statistical, Noise, Transit, Time-series, Distribution).
    *   *Risk:* Frequency-domain features (`ts_ls_peak_power`) are computed on potentially irregularly sampled data after NaN removal.
5.  **Model Training:** Supports Random Forest and Gradient Boosting.
    *   *Assumption:* Assumes a balanced or representative dataset, but no explicit class-weighting or oversampling logic is visible in `model.py`.

---

## 3. Code Quality
*   **Technical Debt:**
    *   `extract_transit_features` in `src/features.py:126` contains an unused `window_size` parameter.
    *   Broad `except Exception:` blocks in `src/features.py:304` and `src/inference.py:78` can swallow critical errors (e.g., `MemoryError` or `KeyboardInterrupt`).
*   **Naming Consistency:** Generally very good, following PEP 8.
*   **Complexity:** Functions are well-sized and focused. `preprocess_pipeline` is a good example of an orchestrator function.

---

## 4. Performance Review
*   **I/O Bottleneck:** The API (`api/routes.py:83`) reads uploaded files into memory, writes them to a temporary disk location, and then the inference engine reads them back. For a high-throughput API, this double-I/O is a significant waste of IOPS.
*   **Search Latency:** The lack of identifier normalization (e.g., ensuring "KIC " prefix) adds seconds to every search.
*   **Concurrency:** The batch downloader (`src/download.py:228`) is purely sequential. Scaling to the full Kepler catalogue (200k+ targets) is impossible with this implementation.
*   **Redundant Computations:** Features are calculated independently; many share the same prerequisite calculations (like `robust_std`).

---

## 5. Reliability Review
*   **External Dependency Risk:** MAST (the data provider) can be unstable. The pipeline lacks sophisticated retry/backoff logic for HTTP 429 or 503 errors.
*   **Input Validation:** The API lacks deep validation of the FITS file content before processing. A malformed FITS file can cause a crash deep in the preprocessing pipeline.
*   **Race Conditions:** Multiple instances of the batch downloader writing to the same `data/raw` directory without file-locking could lead to corrupted files.

---

## 6. Machine Learning Pipeline
*   **Feature Leakage:** No explicit check to ensure that multiple observations of the same target are kept within the same fold during cross-validation or training.
*   **Evaluation:** ROC-AUC and F1 macro are used, which is good for potentially imbalanced exoplanet data.
*   **Reproducibility:** Seeded with 42, but `joblib` serialization can be sensitive to library versions.
*   **Preprocessing:** The same pipeline is used for both training and inference, which is a strength.

---

## 7. Scientific Review
*   **Detrending:** Savitzky-Golay is used with a fixed window of 101.
    *   *Critique:* This window is arbitrary. For long-period planets, the transit might be longer than the window, causing the detrender to "eat" the transit signal.
*   **Normalization:** Median normalization is appropriate for transit detection.
*   **Transit Heuristic:** The dip detector (`src/features.py:165`) uses a simple threshold. This is prone to false positives from stellar activity or instrument noise and doesn't distinguish between planetary transits and eclipsing binaries (V-shape vs U-shape).
*   **Cadence:** The code assumes a single continuous light curve. Kepler data is often split into quarters; joining them requires careful handling of offsets, which is not explicitly visible.

---

## 8. Scalability
*   **100 Targets:** Works perfectly.
*   **10,000 Targets:** Bottlenecked by sequential downloads and MAST latency.
*   **100,000 Targets:** Requires a complete architectural shift to a distributed system (e.g., Ray or Dask) and moving away from local FITS file storage to a dedicated database or object store (S3/GCS).

---

## 9. Security & Configuration
*   **Configuration:** `.env` usage is secure and standard.
*   **API Security:** No authentication or rate-limiting is implemented on the FastAPI endpoints.
*   **Path Traversal:** The API uses `tempfile.NamedTemporaryFile`, which is secure against common path traversal attacks during file upload.

---

## 10. Final Report

### Strengths
1.  **Modularity:** Very easy to plug in new models or feature extractors.
2.  **Maintainability:** Clean, well-documented code with consistent logging.
3.  **User Experience:** Includes a Vite-based frontend and a clean FastAPI backend.
4.  **Verification:** Solid test suite for core features.

### Weaknesses
1.  **Scalability:** Sequential processing prevents large-scale analysis.
2.  **I/O Efficiency:** Excessive disk writes during API inference.
3.  **Scientific Depth:** Simplified detrending and feature engineering.
4.  **Error Handling:** Broad exception catching and lack of external service resilience.

### Top 10 Highest Priority Improvements

| Rank | Improvement | Impact | Difficulty | Implementation Time |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **ID Normalization (KIC/TIC prefixes)** | High | Low | 1 hour |
| 2 | **Async Batch Downloading** | High | Medium | 1 day |
| 3 | **In-Memory API Inference** | High | Medium | 4 hours |
| 4 | **Target-based Train/Test Split** | High | Medium | 2 hours |
| 5 | **Adaptive Detrending Windows** | Medium | Medium | 1 day |
| 6 | **Specific Exception Handling** | Medium | Low | 4 hours |
| 7 | **DVC for Dataset Management** | Medium | Medium | 1 day |
| 8 | **Local Context Transit Features** | Medium | High | 2 days |
| 9 | **Pydantic Settings for Config** | Medium | Low | 2 hours |
| 10 | **API Authentication/Rate-limiting** | Low | Low | 2 hours |

### Single Highest-Leverage Improvement
**Async Batch Downloading & ID Normalization.**
Accelerating the data acquisition phase is the prerequisite for all large-scale scientific validation. Prefixed IDs will reduce MAST latency by seconds per target, and `asyncio` will allow hundreds of concurrent metadata queries, turning a multi-day download task into a multi-hour one.
