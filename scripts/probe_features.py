"""Probe the existing trained model to identify which 10 KOI CSV columns it was trained on.

Strategy: train RandomForests with different feature sets from the KOI CSV and compare
feature importances to the stored model's importances [0.155, 0.115, 0.106, 0.103,
0.102, 0.095, 0.093, 0.092, 0.071, 0.068].
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

ROOT = Path(r"E:\A.G\dev_projects\01-exoplanet-transit-hunter")
CSV_PATH = ROOT / "misc" / "datasets" / "KOI" / "cumulative_2026.07.01_09.24.36.csv"
MODEL_PATH = ROOT / "models" / "random_forest.joblib"

TARGET_IMPORTANCES = np.array(
    [0.155, 0.115, 0.106, 0.103, 0.102, 0.095, 0.093, 0.092, 0.071, 0.068]
)

PRIMARY_PARAMS = [
    "koi_period",
    "koi_duration",
    "koi_depth",
    "koi_impact",
    "koi_prad",
    "koi_model_snr",
    "koi_teq",
    "koi_insol",
    "koi_srad",
    "koi_slogg",
    "koi_steff",
    "koi_kepmag",
    "koi_time0bk",
    "koi_score",
    "koi_tce_plnt_num",
]

FLAG_PARAMS = [
    "koi_fpflag_nt",
    "koi_fpflag_ss",
    "koi_fpflag_co",
    "koi_fpflag_ec",
]


def load_data():
    df = pd.read_csv(CSV_PATH, comment="#", low_memory=False)
    # Label: CONFIRMED=1, FALSE POSITIVE=0, drop CANDIDATE
    disc = df["koi_disposition"].astype(str).str.strip().str.upper()
    mask = disc.isin(["CONFIRMED", "FALSE POSITIVE"])
    df = df[mask].copy()
    df["_label"] = (disc[mask] == "CONFIRMED").astype(np.float64)
    return df


def try_features(df, features, label="candidate"):
    """Train a RF on given features and return (importances, accuracy)."""
    X = df[features].to_numpy(dtype=np.float64)
    y = df["_label"].to_numpy()

    # Drop rows with NaN
    valid = ~np.isnan(X).any(axis=1)
    X, y = X[valid], y[valid]

    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    acc = rf.score(X, y)

    # Sort importances descending for comparison
    imp = np.sort(rf.feature_importances_)[::-1]
    rmse = np.sqrt(np.mean((imp[:10] - TARGET_IMPORTANCES) ** 2))

    print(f"[{label:30s}] n_feat={len(features):2d}  acc={acc:.4f}  "
          f"imp_rmse={rmse:.5f}  sorted_imps={np.round(imp[:10], 4).tolist()}")
    return rmse, imp, rf


def main():
    print("=" * 80)
    print("Feature probe: matching existing model (10 features)")
    print(f"Target importances: {TARGET_IMPORTANCES.tolist()}")
    print("=" * 80)

    df = load_data()
    print(f"\nLoaded {len(df)} rows (CONFIRMED + FALSE POSITIVE only)")

    # Candidate 1: The most natural 10 physical params (no flags, no score)
    candidate_1 = [
        "koi_period", "koi_duration", "koi_depth", "koi_impact",
        "koi_prad", "koi_model_snr", "koi_teq", "koi_insol",
        "koi_srad", "koi_slogg",
    ]
    assert len(candidate_1) == 10, f"Expected 10, got {len(candidate_1)}"
    try_features(df, candidate_1, "10 phys params (core)")

    # Candidate 2: Replace koi_slogg with koi_steff
    candidate_2 = [
        "koi_period", "koi_duration", "koi_depth", "koi_impact",
        "koi_prad", "koi_model_snr", "koi_teq", "koi_insol",
        "koi_srad", "koi_steff",
    ]
    try_features(df, candidate_2, "swap slogg->steff")

    # Candidate 3: Include koi_score instead of koi_slogg
    candidate_3 = [
        "koi_period", "koi_duration", "koi_depth", "koi_impact",
        "koi_prad", "koi_model_snr", "koi_teq", "koi_insol",
        "koi_srad", "koi_score",
    ]
    try_features(df, candidate_3, "swap sloggl->score")

    # Candidate 4: Include koi_kepmag instead of koi_slogg
    candidate_4 = [
        "koi_period", "koi_duration", "koi_depth", "koi_impact",
        "koi_prad", "koi_model_snr", "koi_teq", "koi_insol",
        "koi_srad", "koi_kepmag",
    ]
    try_features(df, candidate_4, "swap sloggl->kepmag")

    # Candidate 5: Include koi_time0bk instead of koi_slogg
    candidate_5 = [
        "koi_period", "koi_duration", "koi_depth", "koi_impact",
        "koi_prad", "koi_model_snr", "koi_teq", "koi_insol",
        "koi_srad", "koi_time0bk",
    ]
    try_features(df, candidate_5, "swap sloggl->time0bk")

    # Candidate 6: All 15 primary params (train RF then see top 10 by importance)
    print("\n--- Training with all 15 primary params to see top importances ---")
    _, _, rf_all = try_features(df, PRIMARY_PARAMS, "ALL 15 params")
    named_imps = sorted(
        zip(PRIMARY_PARAMS, rf_all.feature_importances_),
        key=lambda x: x[1],
        reverse=True,
    )
    print("\nFeature importances (all 15, sorted):")
    for name, imp in named_imps:
        print(f"  {name:25s}  {imp:.4f}")

    # Candidate 7: Include koi_fpflag_* (too easy, but let's see)
    candidate_7 = candidate_1 + FLAG_PARAMS
    _, _, rf_flags = try_features(df, candidate_7, "10 phys + 4 flags")

    # Candidate 8: Subset based on top importances from all-15 run
    top_names = [n for n, _ in named_imps[:10]]
    print(f"\n--- Top 10 by importance: {top_names} ---")
    try_features(df, top_names, "top 10 from all-15")


if __name__ == "__main__":
    main()
