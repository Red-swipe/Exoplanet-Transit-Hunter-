"""Application configuration for Exoplanet Transit Hunter.

This module centralizes filesystem paths and runtime settings so the
pipeline does not rely on hardcoded machine-specific locations.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class ProjectPaths:
    """Filesystem paths used by the project.

    Attributes:
        root: Absolute project root directory.
        data: Data directory containing raw and processed datasets.
        raw_data: Directory for downloaded Kepler/TESS files.
        processed_data: Directory for cleaned, model-ready datasets.
        notebooks: Directory for exploratory notebooks.
    """

    root: Path
    data: Path
    raw_data: Path
    processed_data: Path
    notebooks: Path


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the ML pipeline and API.

    Attributes:
        app_name: Human-readable application name.
        log_level: Logging level used across modules.
        random_seed: Seed for deterministic experiments where possible.
        api_host: Host used by the FastAPI development server.
        api_port: Port used by the FastAPI development server.
        paths: Project filesystem path configuration.
    """

    app_name: str
    log_level: str
    random_seed: int
    api_host: str
    api_port: int
    paths: ProjectPaths


def _build_paths() -> ProjectPaths:
    """Build project paths from the current configuration file location.

    Returns:
        Project path configuration.
    """

    root = Path(__file__).resolve().parent
    data = root / "data"
    return ProjectPaths(
        root=root,
        data=data,
        raw_data=data / "raw",
        processed_data=data / "processed",
        notebooks=root / "notebooks",
    )


def get_settings() -> Settings:
    """Create immutable runtime settings from environment variables.

    Returns:
        Application settings.
    """

    return Settings(
        app_name=os.getenv("APP_NAME", "Exoplanet Transit Hunter"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        random_seed=int(os.getenv("RANDOM_SEED", "42")),
        api_host=os.getenv("API_HOST", "127.0.0.1"),
        api_port=int(os.getenv("API_PORT", "8000")),
        paths=_build_paths(),
    )


settings = get_settings()
