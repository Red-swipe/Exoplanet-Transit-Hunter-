# Exoplanet Transit Hunter

Exoplanet Transit Hunter is a production-oriented machine learning project for
detecting exoplanet transit signals from real NASA Kepler and TESS light curve
data. The project is designed as a professional portfolio system, not a toy
notebook: data processing, modeling, inference, API serving, and future
visualization are separated into clear modules.

## Project Goal

Detect the periodic dimming of stars caused by orbiting planets crossing in
front of them. The system will combine astrophysical signal processing with ML
classification to distinguish true transit events from stellar variability,
instrument noise, and other false positives.

## Architecture

The project is organized as a modular pipeline:

1. Data ingestion downloads or loads public Kepler/TESS light curve files.
2. Preprocessing cleans, detrends, normalizes, and validates light curves.
3. Modeling trains classifiers for transit detection.
4. Inference scores unseen light curves and returns confidence values.
5. API serving exposes model predictions through FastAPI.
6. Frontend visualization will display light curves and flagged transit regions.

Configuration lives in `config.py`, and shared logging utilities live in
`src/logging_utils.py`. Paths are derived from the project root so the code can
run across machines without hardcoded local paths.

## Folder Structure

```text
exoplanet-hunter/
|-- api/
|   |-- __init__.py
|   `-- main.py
|-- data/
|   |-- raw/
|   `-- processed/
|-- frontend/
|-- notebooks/
|-- src/
|   |-- __init__.py
|   |-- inference.py
|   |-- logging_utils.py
|   |-- model.py
|   `-- preprocessing.py
|-- tests/
|   |-- __init__.py
|   `-- test_imports.py
|-- .env.example
|-- .gitignore
|-- config.py
|-- README.md
`-- requirements.txt
```

## Installation

Create and activate a virtual environment with Python 3.12:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

Optional local configuration:

```bash
copy .env.example .env
```

## How to Run

Start the FastAPI service:

```bash
uvicorn api.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/health
```

Run tests:

```bash
pytest
```

## Future Roadmap

- Add NASA archive ingestion for Kepler and TESS light curves.
- Implement FITS parsing with Astropy and Lightkurve.
- Add detrending, sigma clipping, interpolation, and phase folding.
- Build baseline scikit-learn models for interpretable benchmarks.
- Train PyTorch CNN and sequence models for light curve classification.
- Add model evaluation with precision, recall, ROC-AUC, and confusion matrices.
- Serve inference endpoints with validation and versioned model loading.
- Build frontend charts for inspecting flux, folded phase, and candidate dips.
- Add CI checks for tests, formatting, typing, and documentation.

## How to Contribute

1. Create a virtual environment and install dependencies.
2. Add changes in small, focused commits.
3. Use type hints and Google style docstrings for new public functions.
4. Use logging instead of `print()`.
5. Add or update tests for behavior changes.
6. Run `pytest` before opening a pull request.

## Development Standards

- Python 3.12
- Type hints throughout the codebase
- Google style docstrings
- PEP8-compatible formatting
- Central configuration through `config.py`
- Project logging through `src/logging_utils.py`
- No hardcoded machine-specific paths
