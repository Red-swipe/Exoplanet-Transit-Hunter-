# Graph Report - E:\A.G\dev_projects\01-exoplanet-transit-hunter  (2026-07-02)

## Corpus Check
- 27 files · ~18,700 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 377 nodes · 610 edges · 19 communities (16 shown, 3 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_floatarray (64 nodes)|floatarray (64 nodes)]]
- [[_COMMUNITY_any (43 nodes)|any (43 nodes)]]
- [[_COMMUNITY_misca_pre_bug (36 nodes)|misca_pre_bug (36 nodes)]]
- [[_COMMUNITY_gradientboostingclassifier (34 nodes)|gradientboostingclassifier (34 nodes)]]
- [[_COMMUNITY_src_api (31 nodes)|src_api (31 nodes)]]
- [[_COMMUNITY_api_main (30 nodes)|api_main (30 nodes)]]
- [[_COMMUNITY_misca_exoplanet_audit_report (25 nodes)|misca_exoplanet_audit_report (25 nodes)]]
- [[_COMMUNITY_misca_project_status (23 nodes)|misca_project_status (23 nodes)]]
- [[_COMMUNITY_path (19 nodes)|path (19 nodes)]]
- [[_COMMUNITY_misca_engineeringaudit (18 nodes)|misca_engineeringaudit (18 nodes)]]
- [[_COMMUNITY_frontend_package (16 nodes)|frontend_package (16 nodes)]]
- [[_COMMUNITY_config (10 nodes)|config (10 nodes)]]
- [[_COMMUNITY_readme (10 nodes)|readme (10 nodes)]]
- [[_COMMUNITY_misca_b6_fix (6 nodes)|misca_b6_fix (6 nodes)]]
- [[_COMMUNITY_changelog (5 nodes)|changelog (5 nodes)]]
- [[_COMMUNITY_api_init (2 nodes)|api_init (2 nodes)]]
- [[_COMMUNITY_src_init (2 nodes)|src_init (2 nodes)]]
- [[_COMMUNITY_tests_init (2 nodes)|tests_init (2 nodes)]]

## God Nodes (most connected - your core abstractions)
1. `Exoplanet Transit Hunter â€” Full Repository Audit Report` - 16 edges
2. `LightCurveBatch` - 16 edges
3. `extract_features()` - 15 edges
4. `extract_transit_features()` - 14 edges
5. `predict_lightcurve()` - 14 edges
6. `_make_curve()` - 13 edges
7. `2. Bug Catalog` - 11 edges
8. `extract_features_from_batch()` - 11 edges
9. `predict_file()` - 11 edges
10. `preprocess_pipeline()` - 11 edges
11. `extract_statistical_features()` - 10 edges
12. `get_logger()` - 10 edges
13. `Pre-Fix Engineering Analysis â€” Exoplanet Transit Hunter` - 9 edges
14. `Exoplanet Transit Hunter` - 9 edges
15. `extract_noise_features()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `lifespan()` --calls--> `load_trained_model()`  [EXTRACTED]
  api/main.py → src/inference.py
- `TestExtractDistributionFeatures` --uses--> `LightCurveBatch`  [INFERRED]
  tests/test_features.py → src/preprocessing.py
- `TestExtractFeatures` --uses--> `LightCurveBatch`  [INFERRED]
  tests/test_features.py → src/preprocessing.py
- `TestExtractFeaturesFromBatch` --uses--> `LightCurveBatch`  [INFERRED]
  tests/test_features.py → src/preprocessing.py
- `TestExtractNoiseFeatures` --uses--> `LightCurveBatch`  [INFERRED]
  tests/test_features.py → src/preprocessing.py
- `TestExtractStatisticalFeatures` --uses--> `LightCurveBatch`  [INFERRED]
  tests/test_features.py → src/preprocessing.py
- `TestExtractTimeseriesFeatures` --uses--> `LightCurveBatch`  [INFERRED]
  tests/test_features.py → src/preprocessing.py
- `TestExtractTransitFeatures` --uses--> `LightCurveBatch`  [INFERRED]
  tests/test_features.py → src/preprocessing.py
- `predict_file()` --calls--> `extract_features_from_batch()`  [EXTRACTED]
  src/inference.py → src/features.py
- `predict_lightcurve()` --calls--> `extract_features_from_batch()`  [EXTRACTED]
  src/inference.py → src/features.py

## Import Cycles
- None detected.

## Communities (19 total, 3 thin omitted)

### Community 0 - "floatarray (64 nodes)"
Cohesion: 0.07
Nodes (34): FloatArray, ndarray, extract_distribution_features(), extract_features(), extract_features_from_batch(), extract_noise_features(), extract_statistical_features(), extract_timeseries_features() (+26 more)

### Community 1 - "any (43 nodes)"
Cohesion: 0.11
Nodes (41): Any, ClassifierMixin, LightCurve, BatchPredictionResult, _extract_arrays(), _import_lightkurve(), load_trained_model(), predict_batch() (+33 more)

### Community 2 - "misca_pre_bug (36 nodes)"
Cohesion: 0.06
Nodes (35): 1. Repository Overview, 2. Bug Catalog, 3. Engineering Audit Verification, 4. Dependency Review, 5. ML Pipeline Review, 6. Training Readiness, 7. Production Readiness, 8. Ordered Bug Fix Plan (+27 more)

### Community 3 - "gradientboostingclassifier (34 nodes)"
Cohesion: 0.08
Nodes (32): GradientBoostingClassifier, RandomForestClassifier, cross_validate_model(), CrossValidationResult, Dataset, _ensure_models_dir(), evaluate_model(), _main() (+24 more)

### Community 4 - "src_api (31 nodes)"
Cohesion: 0.08
Nodes (8): getHealth(), getMetrics(), predict(), AiPredictor(), MissionControl(), ModelMetrics(), navItems, SystemHealth()

### Community 5 - "api_main (30 nodes)"
Cohesion: 0.12
Nodes (26): lifespan(), FastAPI application for the Exoplanet Transit Hunter., health(), _is_allowed(), metrics(), predict(), predict_batch(), API route definitions for the Exoplanet Transit Hunter. (+18 more)

### Community 6 - "misca_exoplanet_audit_report (25 nodes)"
Cohesion: 0.08
Nodes (24): Core items, Core items (code exists but was NEVER EXECUTED), Engineering Audit Resolution Status (`engineeringaudit.md` cross-check), Exoplanet Transit Hunter â€” Full Repository Audit Report, Missing Checklist Items, Outstanding items, Outstanding items (all [ ]), Outstanding items (all still [ ]) (+16 more)

### Community 7 - "misca_project_status (23 nodes)"
Cohesion: 0.09
Nodes (22): Backend, DevOps, Exoplanet Transit Hunter â€” Project Status, Frontend, Future Roadmap (v1.1+), Instructions for AI, Machine Learning, Phase 10 â€” Integration (+14 more)

### Community 8 - "path (19 nodes)"
Cohesion: 0.17
Nodes (18): Path, download_batch(), download_lightcurve(), _ensure_download_dir(), _fits_filename(), _import_lightkurve(), _is_downloaded(), list_downloaded() (+10 more)

### Community 9 - "misca_engineeringaudit (18 nodes)"
Cohesion: 0.11
Nodes (17): 1. Bugs & Critical Issues, 2. Machine Learning & Performance, 3. Improvements & Style, Conclusion, [Critical] Incomplete System Implementation, [Critical] Physical/Mathematical Bug in Lomb-Scargle Computation, Engineering Audit Report: Exoplanet Transit Hunter, Executive Summary (+9 more)

### Community 10 - "frontend_package (16 nodes)"
Cohesion: 0.12
Nodes (15): dependencies, react, react-dom, typescript, vite, @vitejs/plugin-react, devDependencies, name (+7 more)

### Community 11 - "config (10 nodes)"
Cohesion: 0.27
Nodes (9): _build_paths(), get_settings(), ProjectPaths, Application configuration for Exoplanet Transit Hunter.  This module centralizes, Filesystem paths used by the project.      Attributes:         root: Absolute pr, Runtime settings for the ML pipeline and API.      Attributes:         app_name:, Build project paths from the current configuration file location.      Returns:, Create immutable runtime settings from environment variables.      Returns: (+1 more)

### Community 12 - "readme (10 nodes)"
Cohesion: 0.20
Nodes (9): Architecture, Development Standards, Exoplanet Transit Hunter, Folder Structure, Future Roadmap, How to Contribute, How to Run, Installation (+1 more)

### Community 13 - "misca_b6_fix (6 nodes)"
Cohesion: 0.33
Nodes (5): Affected Tests, B6 Fix â€” Dataset Split Before Shuffle, Fix Applied, Verification, Why the Fix Is Mathematically Correct

### Community 14 - "changelog (5 nodes)"
Cohesion: 0.40
Nodes (4): [1.0.0] â€” 2026-07-01, Added, Changed, Changelog

## Knowledge Gaps
- **106 isolated node(s):** `Added`, `Changed`, `name`, `private`, `version` (+101 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.