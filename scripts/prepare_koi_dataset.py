#!/usr/bin/env python3
"""Prepare the KOI dataset as a three-sheet Excel workbook with star IDs.

Reads the KOI cumulative CSV from the NASA Exoplanet Archive, maps
``koi_disposition`` to binary labels (CONFIRMED = 1, everything else = 0),
and writes an Excel file with three sheets:

* ``tce_features`` — feature matrix
* ``tce_training_labels`` — binary label column
* ``star_ids`` — star (Kepler) IDs for grouped cross-validation
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from config import settings
from src.logging_utils import configure_logging, get_logger

logger = get_logger(__name__)


def _resolve_koi_csv() -> Path:
    return settings.paths.root / "misca" / "datasets" / "KOI" / "cumulative_2026.07.01_09.24.36.csv"


def _select_feature_columns(df: pd.DataFrame) -> list[str]:
    koi_cols = [c for c in df.columns if c.startswith("koi_")]
    drop_cols = {"koi_disposition", "koi_score", "koi_tce_delivery",
                 "kepler_name", "kepid"}
    return [c for c in koi_cols if c not in drop_cols]


def _map_label(v: str) -> float:
    return 1.0 if str(v).strip().upper() == "CONFIRMED" else 0.0


def _resolve_star_id(row: pd.Series) -> str:
    kepid = row.get("kepid") or row.get("kepler_id")
    if pd.isna(kepid):
        return ""
    return str(int(float(kepid)))


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(
        description="Prepare KOI dataset as a 3-sheet Excel file with star IDs.",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Path to the KOI cumulative CSV (default: project path).",
    )
    parser.add_argument(
        "--output",
        default="data/processed/kepler_candidates.xlsx",
        help="Output Excel path (default: data/processed/kepler_candidates.xlsx).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N rows (for debugging).",
    )
    args = parser.parse_args()

    csv_path = Path(args.input) if args.input else _resolve_koi_csv()
    if not csv_path.exists():
        logger.error("KOI CSV not found: %s", csv_path)
        raise SystemExit(1)

    logger.info("Reading KOI CSV: %s", csv_path)
    df = pd.read_csv(csv_path, comment="#", dtype={"kepid": str})

    if args.limit:
        df = df.head(args.limit)
        logger.info("Limited to %d rows.", args.limit)

    logger.info("Loaded %d rows.", len(df))

    feature_cols = _select_feature_columns(df)
    logger.info("Selected %d feature columns.", len(feature_cols))

    df_features = df[feature_cols].copy()
    df_features = df_features.select_dtypes(include=[float, int])

    df_labels = df["koi_disposition"].apply(_map_label)
    df_star_ids = df.apply(_resolve_star_id, axis=1)

    out_path = _resolve_path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df_features.to_excel(writer, sheet_name="tce_features", index=False)
        df_labels.to_excel(writer, sheet_name="tce_training_labels", index=False)
        df_star_ids.to_excel(writer, sheet_name="star_ids", index=False)

    n_confirmed = int(df_labels.sum())
    n_total = len(df_labels)
    n_unique_stars = df_star_ids.nunique()
    logger.info(
        "Wrote %d samples (%d confirmed) from %d unique stars → %s",
        n_total, n_confirmed, n_unique_stars, out_path,
    )


def _resolve_path(candidate: str) -> Path:
    path = Path(candidate)
    if not path.is_absolute():
        path = settings.paths.root / path
    return path.resolve()


if __name__ == "__main__":
    main()
