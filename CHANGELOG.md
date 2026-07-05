# Changelog

All notable changes to the Exoplanet Transit Hunter project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
