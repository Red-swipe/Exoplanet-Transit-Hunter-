"""Tests for the feature engineering module."""

from __future__ import annotations

import numpy as np
import pytest

from src.features import (
    extract_distribution_features,
    extract_features,
    extract_features_from_batch,
    extract_noise_features,
    extract_statistical_features,
    extract_timeseries_features,
    extract_transit_features,
)
from src.preprocessing import LightCurveBatch


def _make_curve(n: int = 500, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 24, n)
    flux = rng.normal(0.0, 0.01, n)
    return t, flux


# ---------------------------------------------------------------------------
# Statistical
# ---------------------------------------------------------------------------


class TestExtractStatisticalFeatures:
    def test_returns_expected_keys(self):
        _, flux = _make_curve()
        feats = extract_statistical_features(flux)
        prefix = "stat_"
        assert all(k.startswith(prefix) for k in feats)
        assert len(feats) == 14

    def test_rejects_empty_flux(self):
        with pytest.raises(ValueError, match="no finite values"):
            extract_statistical_features(np.array([]))

    def test_rejects_all_nan(self):
        with pytest.raises(ValueError, match="no finite values"):
            extract_statistical_features(np.array([np.nan, np.nan]))

    def test_constant_flux(self):
        flux = np.full(100, 1.0)
        feats = extract_statistical_features(flux)
        assert feats["stat_std"] == 0.0

    def test_handles_some_nan(self):
        flux = np.array([1.0, np.nan, 2.0, np.nan, 3.0])
        feats = extract_statistical_features(flux)
        assert feats["stat_mean"] == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# Noise
# ---------------------------------------------------------------------------


class TestExtractNoiseFeatures:
    def test_returns_expected_keys(self):
        _, flux = _make_curve()
        feats = extract_noise_features(flux)
        assert all(k.startswith("noise_") for k in feats)
        assert len(feats) == 6

    def test_rejects_too_few_points(self):
        with pytest.raises(ValueError, match="At least two"):
            extract_noise_features(np.array([1.0]))

    def test_constant_zero(self):
        flux = np.zeros(100)
        feats = extract_noise_features(flux)
        assert feats["noise_rms"] == 0.0
        assert feats["noise_snr"] == 0.0


# ---------------------------------------------------------------------------
# Transit heuristic
# ---------------------------------------------------------------------------


class TestExtractTransitFeatures:
    def test_returns_expected_keys(self):
        t, flux = _make_curve()
        feats = extract_transit_features(t, flux)
        assert all(k.startswith("transit_") for k in feats)
        assert len(feats) == 6

    def test_no_dip_returns_zeros(self):
        t = np.linspace(0, 10, 200)
        flux = np.random.default_rng(42).normal(0, 0.01, 200)
        feats = extract_transit_features(t, flux, n_sigma=5.0)
        assert feats["transit_dip_count"] == 0

    def test_detects_synthetic_dip(self):
        t = np.linspace(0, 10, 500)
        flux = np.random.default_rng(1).normal(0, 0.01, 500)
        flux[200:215] -= 0.05
        feats = extract_transit_features(t, flux, n_sigma=2.0)
        assert feats["transit_dip_count"] >= 1
        assert feats["transit_dip_depth_max"] > 0.04

    def test_invalid_window_size(self):
        t, flux = _make_curve(100)
        with pytest.raises(ValueError, match="window_size"):
            extract_transit_features(t, flux, window_size=0)

    def test_invalid_n_sigma(self):
        t, flux = _make_curve(100)
        with pytest.raises(ValueError, match="n_sigma"):
            extract_transit_features(t, flux, n_sigma=0)

    def test_invalid_min_dip_points(self):
        t, flux = _make_curve(100)
        with pytest.raises(ValueError, match="min_dip_points"):
            extract_transit_features(t, flux, min_dip_points=0)

    def test_empty_arrays(self):
        with pytest.raises(ValueError, match="empty"):
            extract_transit_features(np.array([]), np.array([]))


# ---------------------------------------------------------------------------
# Timeseries
# ---------------------------------------------------------------------------


class TestExtractTimeseriesFeatures:
    def test_returns_expected_keys(self):
        t, flux = _make_curve()
        feats = extract_timeseries_features(t, flux)
        assert all(k.startswith("ts_") for k in feats)
        assert len(feats) == 6

    def test_rejects_fewer_than_three(self):
        t = np.array([1.0, 2.0])
        flux = np.array([0.0, 0.0])
        with pytest.raises(ValueError, match="At least three"):
            extract_timeseries_features(t, flux)

    def test_autocorrelation(self):
        t = np.linspace(0, 10, 100)
        flux = np.random.default_rng(42).normal(0, 1, 100)
        feats = extract_timeseries_features(t, flux)
        assert -1.0 <= feats["ts_acf_lag1"] <= 1.0

    def test_lomb_scargle_detects_known_period(self):
        period = 5.0
        t = np.linspace(0, 30, 1000)
        flux = np.sin(2 * np.pi * t / period) + np.random.default_rng(42).normal(0, 0.05, 1000)
        feats = extract_timeseries_features(t, flux)
        assert feats["ts_ls_peak_period"] == pytest.approx(period, rel=0.1)


# ---------------------------------------------------------------------------
# Distribution
# ---------------------------------------------------------------------------


class TestExtractDistributionFeatures:
    def test_returns_expected_keys(self):
        _, flux = _make_curve()
        feats = extract_distribution_features(flux)
        assert all(k.startswith("dist_") for k in feats)
        assert len(feats) == 4

    def test_uniform_has_high_entropy_ratio(self):
        flux = np.linspace(-1, 1, 1000)
        feats = extract_distribution_features(flux)
        assert feats["dist_entropy_ratio"] > 0.9

    def test_peaked_has_low_entropy_ratio(self):
        flux = np.zeros(1000)
        flux[::2] = 0.0
        feats = extract_distribution_features(flux, n_bins=50)
        assert feats["dist_entropy_ratio"] < 0.3

    def test_rejects_fewer_than_two_bins(self):
        _, flux = _make_curve()
        with pytest.raises(ValueError, match="n_bins"):
            extract_distribution_features(flux, n_bins=1)

    def test_tail_mass_is_fraction_in_unit_interval(self):
        _, flux = _make_curve(1000)
        feats = extract_distribution_features(flux)
        assert 0.0 <= feats["dist_tail_mass"] <= 1.0

    def test_uniform_tail_mass_is_reasonable(self):
        flux = np.linspace(-1, 1, 10000)
        feats = extract_distribution_features(flux, n_bins=20)
        assert feats["dist_tail_mass"] == pytest.approx(0.2, abs=0.02)


# ---------------------------------------------------------------------------
# Aggregate entry point
# ---------------------------------------------------------------------------


class TestExtractFeatures:
    def test_returns_all_36_features(self):
        t, flux = _make_curve()
        feats = extract_features(t, flux)
        assert len(feats) == 36
        assert isinstance(feats, dict)
        assert all(isinstance(v, (float, np.floating)) for v in feats.values())

    def test_prefixed_groups_present(self):
        t, flux = _make_curve()
        feats = extract_features(t, flux)
        prefixes = ["stat_", "noise_", "transit_", "ts_", "dist_"]
        for prefix in prefixes:
            assert any(k.startswith(prefix) for k in feats), f"Missing {prefix}"

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="empty"):
            extract_features(np.array([]), np.array([]))

    def test_mismatched_shapes(self):
        t = np.linspace(0, 10, 100)
        flux = np.linspace(0, 1, 50)
        with pytest.raises(ValueError, match="shape"):
            extract_features(t, flux)

    def test_handles_nan_in_time_and_flux(self):
        rng = np.random.default_rng(42)
        t = np.linspace(0, 24, 500)
        flux = rng.normal(0, 0.01, 500)
        flux[::10] = np.nan
        t[::15] = np.nan
        feats = extract_features(t, flux)
        assert all(np.isfinite(v) for v in feats.values())

    def test_all_nan_still_raises(self):
        t = np.array([1.0, 2.0])
        flux = np.array([np.nan, np.nan])
        with pytest.raises(ValueError, match="No finite"):
            extract_features(t, flux)


class TestExtractFeaturesFromBatch:
    def test_returns_list_of_dicts(self):
        rng = np.random.default_rng(42)
        batch = LightCurveBatch(
            time=np.array([np.linspace(0, 10, 100)] * 2),
            flux=np.array([rng.normal(0, 0.01, 100) for _ in range(2)]),
            flux_error=np.array([np.full(100, 0.01)] * 2),
        )
        results = extract_features_from_batch(batch)
        assert len(results) == 2
        assert all(len(r) == 36 for r in results)

    def test_empty_batch_returns_empty_list(self):
        batch = LightCurveBatch(
            time=np.empty((0, 10)),
            flux=np.empty((0, 10)),
        )
        result = extract_features_from_batch(batch)
        assert result == []
