"""Smoke tests for the project skeleton."""

from __future__ import annotations


def test_core_modules_import() -> None:
    """Verify core modules import successfully."""

    import config
    from api.main import app
    from src.model import prepare_dataset, save_model, load_model
    from src.preprocessing import normalize_flux

    assert config.settings.app_name == "Exoplanet Transit Hunter"
    assert app.title == "Exoplanet Transit Hunter API"
    assert callable(prepare_dataset)
    assert callable(save_model)
    assert callable(load_model)
    assert normalize_flux is not None
