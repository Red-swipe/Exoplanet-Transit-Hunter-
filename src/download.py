"""Data acquisition pipeline for Kepler and TESS light curves.

This module provides a robust interface for searching and downloading
public NASA light curve data using the Lightkurve library. Results are
saved as FITS files in the project's raw data directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from config import settings
from src.logging_utils import get_logger


if TYPE_CHECKING:
    import lightkurve as lk


logger = get_logger(__name__)


def _import_lightkurve() -> Any:
    """Import Lightkurve lazily.

    Returns:
        Imported Lightkurve module.

    Raises:
        ImportError: If Lightkurve is not installed.
    """

    try:
        import lightkurve as lk  # noqa: F811
    except ImportError as exc:
        logger.exception("Lightkurve is required to download light curves.")
        raise ImportError(
            "Lightkurve is required for data download. Install dependencies "
            "with `pip install -r requirements.txt`."
        ) from exc

    return lk


def _ensure_download_dir(download_dir: Path | None = None) -> Path:
    """Ensure the download directory exists and return its resolved path.

    Args:
        download_dir: Optional download directory. Defaults to the project's
            raw data directory from application settings.

    Returns:
        Resolved download directory path.
    """

    if download_dir is None:
        download_dir = settings.paths.raw_data
    download_dir = Path(download_dir).expanduser().resolve()
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


def _fits_filename(target_id: str, mission: str, author: str = "") -> str:
    """Build a descriptive filename for a downloaded FITS light curve.

    Args:
        target_id: Target identifier (e.g., ``"Kepler-10"``, ``"TIC 123456789"``).
        mission: Mission name (``"Kepler"``, ``"K2"``, or ``"TESS"``).
        author: Optional pipeline author (e.g., ``"SPOC"``, ``"QLP"``).

    Returns:
        Filename with ``.fits`` extension.
    """

    safe_id = target_id.replace(" ", "_")
    parts = [safe_id, mission]
    if author:
        parts.append(author)
    return "_".join(parts) + ".fits"


def _is_downloaded(target_id: str, mission: str, download_dir: Path) -> bool:
    """Check whether a light curve for this target has been downloaded.

    Args:
        target_id: Target identifier.
        mission: Mission name.
        download_dir: Directory to scan.

    Returns:
        ``True`` if at least one matching FITS file exists.
    """

    search_pattern = f"{target_id.replace(' ', '_')}_{mission}*.fits"
    return len(list(download_dir.glob(search_pattern))) > 0


def search_target(
    target_id: str,
    mission: str = "Kepler",
) -> list[dict[str, Any]]:
    """Search for available light curves for a given target.

    Args:
        target_id: Target identifier. Accepts Kepler IDs (e.g.,
            ``"Kepler-10"``, ``"KIC 11904151"``), TIC IDs (e.g.,
            ``"TIC 150428135"``), or common target names.
        mission: Mission to search. One of ``"Kepler"``, ``"K2"``,
            ``"TESS"``.

    Returns:
        List of search result metadata dictionaries. Each entry contains
        keys such as ``target_name``, ``mission``, ``author``,
        ``exptime``, and ``distance``. Returns an empty list when no
        results are found.

    Raises:
        ImportError: If Lightkurve is not installed.
        RuntimeError: If the search fails due to a network or server error.
    """

    lk = _import_lightkurve()
    logger.info("Searching for %s in %s mission data.", target_id, mission)

    logger.debug("Calling lk.search_lightcurve(target_id=%s, mission=%s) ...", target_id, mission)
    try:
        search_result = lk.search_lightcurve(target_id, mission=mission)
    except Exception as exc:
        logger.exception(
            "Search failed for target %s in mission %s.", target_id, mission
        )
        raise RuntimeError(
            f"Failed to search for target {target_id} in {mission} data."
        ) from exc
    logger.debug("lk.search_lightcurve returned %d result(s).", 0 if search_result is None else len(search_result))

    if search_result is None or len(search_result) == 0:
        logger.warning("No light curves found for %s in %s.", target_id, mission)
        return []

    results: list[dict[str, Any]] = []
    for row in search_result:
        try:
            metadata = {
                "target_name": str(getattr(row, "target_name", target_id)),
                "mission": str(getattr(row, "mission", mission)),
                "author": str(getattr(row, "author", "")),
                "exptime": float(getattr(row, "exptime", 0.0)),
                "year": str(getattr(row, "year", "")),
                "description": str(getattr(row, "description", "")),
                "distance": float(getattr(row, "distance", -1.0)),
            }
        except (TypeError, ValueError) as exc:
            logger.warning("Skipping malformed search result row: %s", exc)
            continue
        results.append(metadata)

    logger.info(
        "Found %d light curve(s) for %s in %s.",
        len(results),
        target_id,
        mission,
    )
    return results


def download_lightcurve(
    target_id: str,
    mission: str = "Kepler",
    download_dir: Path | None = None,
    quality_bitmask: str = "default",
) -> Path:
    """Download the highest-quality light curve for a target.

    Searches the specified mission archive and downloads the best available
    light curve. The result is saved as a FITS file in ``download_dir``.
    Duplicate downloads are detected and skipped.

    Args:
        target_id: Target identifier (Kepler ID, TIC ID, or target name).
        mission: Mission to search. One of ``"Kepler"``, ``"K2"``,
            ``"TESS"``.
        download_dir: Optional download directory. Defaults to the
            project's ``data/raw/`` directory.
        quality_bitmask: Bitmask for quality filtering. Passed directly to
            Lightkurve's ``download()`` method.

    Returns:
        Path to the downloaded (or pre-existing) FITS file.

    Raises:
        ImportError: If Lightkurve is not installed.
        ValueError: If no light curves are found for the target.
        RuntimeError: If the download fails due to a network error,
            corrupted data, or file write failure.
    """

    lk = _import_lightkurve()
    output_dir = _ensure_download_dir(download_dir)

    if _is_downloaded(target_id, mission, output_dir):
        existing = sorted(
            output_dir.glob(f"{target_id.replace(' ', '_')}_{mission}*.fits")
        )
        logger.info(
            "Light curve already downloaded: %s. Returning existing file.",
            existing[0],
        )
        return existing[0]

    logger.info("Downloading light curve for %s (%s).", target_id, mission)

    from astroquery.mast import Mast
    Mast.TIMEOUT = 120
    logger.info(
        "Calling lk.search_lightcurve(target_id=%s, mission=%s) ...",
        target_id,
        mission,
    )
    try:
        search_result = lk.search_lightcurve(target_id, mission=mission)
    except Exception as exc:
        logger.exception("Search failed for target %s.", target_id)
        raise RuntimeError(f"Failed to search for target {target_id}.") from exc
    logger.info(
        "lk.search_lightcurve returned %d result(s).",
        0 if search_result is None else len(search_result),
    )

    if search_result is None or len(search_result) == 0:
        logger.error(
            "No light curves found for target %s in %s.", target_id, mission
        )
        raise ValueError(
            f"No light curves found for target '{target_id}' in {mission} data."
        )

    logger.info(
        "Calling search_result[0].download(quality_bitmask=%s) ...",
        quality_bitmask,
    )
    try:
        lightcurve = search_result[0].download(quality_bitmask=quality_bitmask)
    except Exception as exc:
        logger.exception("Download failed for target %s.", target_id)
        raise RuntimeError(
            f"Failed to download light curve for {target_id}."
        ) from exc
    logger.info("search_result[0].download returned successfully.")

    if lightcurve is None:
        logger.error("Download returned None for target %s.", target_id)
        raise RuntimeError(f"Download returned empty result for target {target_id}.")

    try:
        author = str(getattr(search_result[0], "author", ""))
    except (TypeError, ValueError):
        author = ""

    filename = _fits_filename(target_id, mission, author)
    output_path = output_dir / filename

    try:
        lightcurve.to_fits(output_path, overwrite=True)
    except Exception as exc:
        logger.exception("Failed to write FITS file: %s", output_path)
        raise RuntimeError(
            f"Failed to write FITS file to {output_path}."
        ) from exc

    try:
        lk.read(output_path)
    except Exception as exc:
        logger.exception("Downloaded file is corrupted: %s", output_path)
        output_path.unlink(missing_ok=True)
        raise RuntimeError(f"Downloaded file is corrupted: {output_path}") from exc

    logger.info(
        "Successfully downloaded light curve for %s to %s (%d samples).",
        target_id,
        output_path,
        len(lightcurve),
    )
    return output_path


def download_batch(
    target_ids: list[str],
    mission: str = "Kepler",
) -> list[Path]:
    """Download light curves for multiple targets.

    Each target is downloaded independently so that a single failure does
    not abort the entire batch.

    Args:
        target_ids: List of target identifiers.
        mission: Mission to search for all targets.

    Returns:
        Paths to successfully downloaded FITS files.

    Raises:
        ImportError: If Lightkurve is not installed.
    """

    logger.info(
        "Starting batch download of %d targets for %s.", len(target_ids), mission
    )

    downloaded: list[Path] = []
    failed: list[tuple[str, str]] = []

    for target_id in target_ids:
        try:
            path = download_lightcurve(target_id, mission=mission)
            downloaded.append(path)
        except (ValueError, RuntimeError) as exc:
            logger.error("Failed to download %s: %s", target_id, exc)
            failed.append((target_id, str(exc)))

    if failed:
        logger.warning(
            "Batch download completed with %d success(es) and %d failure(s): %s",
            len(downloaded),
            len(failed),
            [f[0] for f in failed],
        )
    else:
        logger.info(
            "Batch download completed successfully for all %d targets.",
            len(downloaded),
        )

    return downloaded


def list_downloaded(download_dir: Path | None = None) -> list[Path]:
    """List all downloaded light curve FITS files.

    Args:
        download_dir: Optional directory to scan. Defaults to the
            project's ``data/raw/`` directory.

    Returns:
        Sorted list of paths to FITS files in the download directory.
    """

    scan_dir = _ensure_download_dir(download_dir)
    fits_files = sorted(scan_dir.glob("*.fits"))
    logger.info(
        "Found %d downloaded light curve(s) in %s.", len(fits_files), scan_dir
    )
    return fits_files
