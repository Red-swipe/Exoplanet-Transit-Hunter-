#!/usr/bin/env python3
"""Prepare the Kepler dataset for the Exoplanet Transit Hunter pipeline.

Reads the KOI cumulative table from the NASA Exoplanet Archive, extracts
unique Kepler IDs (KepIDs), and downloads light curves into ``data/raw/``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from config import settings
from src.download import _ensure_download_dir, download_lightcurve
from src.logging_utils import configure_logging, get_logger

logger = get_logger(__name__)


def _resolve_koi_csv() -> Path:
    """Return the path to the KOI cumulative CSV shipped with the project."""
    return settings.paths.root / "misc" / "datasets" / "KOI" / "cumulative_2026.07.01_09.24.36.csv"


def read_unique_kepids(csv_path: Path, confirmed_only: bool = False) -> list[str]:
    """Read the KOI CSV and return a deduplicated list of KepIDs.

    Args:
        csv_path: Path to the KOI cumulative CSV (NASA Exoplanet Archive format).
        confirmed_only: If True, only keep rows where disposition is CONFIRMED.

    Returns:
        Sorted list of unique KepID strings.
    """
    logger.info("Reading KOI CSV: %s", csv_path)
    df = pd.read_csv(csv_path, comment="#", dtype={"kepid": str})
    logger.info("Loaded %d KOI rows.", len(df))

    if confirmed_only:
        before = len(df)
        df = df[df["koi_disposition"] == "CONFIRMED"].copy()
        logger.info("Filtered to CONFIRMED only: %d -> %d rows.", before, len(df))

    unique = sorted(df["kepid"].unique())
    logger.info("Unique KepIDs after deduplication: %d.", len(unique))
    return unique


def main() -> None:
    configure_logging()

    parser = argparse.ArgumentParser(
        description="Download Kepler light curves from the KOI catalogue."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of targets to download (default: all).",
    )
    parser.add_argument(
        "--confirmed-only",
        action="store_true",
        help="Only download targets with CONFIRMED disposition.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-download light curves even if already present.",
    )
    args = parser.parse_args()

    csv_path = _resolve_koi_csv()
    if not csv_path.exists():
        logger.error("KOI CSV not found: %s", csv_path)
        raise SystemExit(1)

    target_ids = read_unique_kepids(csv_path, confirmed_only=args.confirmed_only)

    if args.limit and args.limit < len(target_ids):
        logger.info("Limiting to %d target(s) as requested.", args.limit)
        target_ids = target_ids[: args.limit]

    logger.info(
        "Dataset preparation: %d target(s), overwrite=%s.",
        len(target_ids),
        args.overwrite,
    )

    download_dir = _ensure_download_dir()
    logger.info("Download directory: %s", download_dir)

    downloaded: list[Path] = []
    failed: list[str] = []

    for i, kepid in enumerate(target_ids, start=1):
        logger.info("[%d/%d] Processing KepID %s.", i, len(target_ids), kepid)

        if args.overwrite:
            for f in download_dir.glob(f"{kepid}_Kepler*.fits"):
                f.unlink()
                logger.info("Removed existing file: %s", f)

        try:
            path = download_lightcurve(kepid, mission="Kepler")
            downloaded.append(path)
        except (ValueError, RuntimeError) as exc:
            logger.error("Failed to download KepID %s: %s", kepid, exc)
            failed.append(kepid)

    logger.info(
        "Dataset preparation finished: %d succeeded, %d failed.",
        len(downloaded),
        len(failed),
    )
    if failed:
        logger.warning("Failed targets (%d): %s", len(failed), ", ".join(failed))


if __name__ == "__main__":
    main()
