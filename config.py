"""Application configuration for Exoplanet Transit Hunter.

This module centralizes filesystem paths and runtime settings so the
pipeline does not rely on hardcoded machine-specific locations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


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


class Settings(BaseSettings):
    """Runtime settings for the ML pipeline and API.

    Attributes:
        app_name: Human-readable application name.
        log_level: Logging level used across modules.
        random_seed: Seed for deterministic experiments where possible.
        api_host: Host used by the FastAPI development server.
        api_port: Port used by the FastAPI development server.
        download_timeout: HTTP timeout (seconds) for file downloads.
        download_max_retries: Maximum number of download retry attempts.
        download_retry_delay: Delay (seconds) between download retries.
        api_title: Title shown in the OpenAPI docs.
        api_version: Version string shown in the OpenAPI docs.
        model_name: Default model filename used by the API.
        savgol_window_length: Savitzky-Golay detrending window (samples).
        savgol_polyorder: Savitzky-Golay polynomial order.
        sigma: Sigma-clipping threshold in robust standard deviations.
        median_kernel_size: Median filter kernel size (samples).
        feature_window_size: Sliding window length for transit features.
        feature_n_sigma: Number of sigmas for dip detection threshold.
        feature_min_dip_points: Minimum consecutive samples for a valid dip.
        feature_n_bins: Number of histogram bins for distribution features.
        mast_timeout: HTTP timeout (seconds) for MAST archive queries.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Exoplanet Transit Hunter"
    log_level: str = "INFO"
    random_seed: int = 42
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    download_timeout: int = 120
    download_max_retries: int = 3
    download_retry_delay: float = 5.0

    api_title: str = "Exoplanet Transit Hunter API"
    api_version: str = "0.1.0"
    model_name: str = "random_forest.joblib"

    savgol_window_length: int = 101
    savgol_polyorder: int = 2
    sigma: float = 5.0
    median_kernel_size: int = 5

    feature_window_size: int = 13
    feature_n_sigma: float = 2.5
    feature_min_dip_points: int = 3
    feature_n_bins: int = 20

    mast_timeout: int = 120

    @property
    def paths(self) -> ProjectPaths:
        """Build project paths from the current configuration file location."""
        root = Path(__file__).resolve().parent
        data = root / "data"
        return ProjectPaths(
            root=root,
            data=data,
            raw_data=data / "raw",
            processed_data=data / "processed",
            notebooks=root / "notebooks",
        )


settings = Settings()
