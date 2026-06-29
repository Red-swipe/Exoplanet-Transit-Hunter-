"""Feature engineering for exoplanet transit classification.

This module transforms preprocessed light curves into a fixed-length vector
of numeric features suitable for classical machine learning classifiers.
Features are grouped into five categories:

*   **Statistical** — mean, variance, skew, percentiles, and similar descriptors
    of the flux distribution.
*   **Noise** — RMS, MAD, point-to-point scatter, and signal-to-noise estimates.
*   **Transit-heuristic** — sliding-window dip detection for candidate events.
*   **Time-series** — autocorrelation at small lags and Lomb-Scargle
    periodogram peak.
*   **Distribution** — histogram entropy, tail mass, and concentration.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt
from scipy import signal, stats

from src.logging_utils import get_logger
from src.preprocessing import LightCurveBatch


logger = get_logger(__name__)

FloatArray = npt.NDArray[np.float64]


def _validate_arrays(time: FloatArray, flux: FloatArray) -> tuple[FloatArray, FloatArray]:
    """Validate and convert input arrays to float64, checking for emptiness and NaNs."""
    time_arr = np.asarray(time, dtype=np.float64).ravel()
    flux_arr = np.asarray(flux, dtype=np.float64).ravel()

    if time_arr.size == 0 or flux_arr.size == 0:
        raise ValueError("Time and flux arrays must not be empty.")

    if time_arr.shape != flux_arr.shape:
        raise ValueError(
            f"Time shape {time_arr.shape} does not match flux shape {flux_arr.shape}."
        )

    valid = np.isfinite(time_arr) & np.isfinite(flux_arr)
    if not np.any(valid):
        raise ValueError("No finite (time, flux) pairs available.")

    return time_arr, flux_arr


def _robust_std(values: FloatArray) -> float:
    """Robust standard deviation estimate via MAD (1.4826 * median|d|)."""
    med = float(np.median(values))
    mad = float(np.median(np.abs(values - med)))
    return 1.4826 * mad if mad > 0 else 0.0


# ---------------------------------------------------------------------------
# Public feature-group extractors
# ---------------------------------------------------------------------------


def extract_statistical_features(flux: FloatArray) -> dict[str, float]:
    """Statistical distribution descriptors of the flux values.

    Parameters
    ----------
    flux : np.ndarray
        Preprocessed (normalised, detrended) flux values.

    Returns
    -------
    dict[str, float]
        Features keyed with the ``stat_`` prefix.

    Raises
    ------
    ValueError
        If the flux array has no finite values.
    """
    finite = np.asarray(flux, dtype=np.float64).ravel()
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        raise ValueError("Flux array has no finite values.")

    p05 = float(np.percentile(finite, 5))
    p25 = float(np.percentile(finite, 25))
    p75 = float(np.percentile(finite, 75))
    p95 = float(np.percentile(finite, 95))

    return {
        "stat_mean": float(np.mean(finite)),
        "stat_median": float(np.median(finite)),
        "stat_std": float(np.std(finite)),
        "stat_var": float(np.var(finite)),
        "stat_min": float(np.min(finite)),
        "stat_max": float(np.max(finite)),
        "stat_range": float(np.ptp(finite)),
        "stat_skew": float(stats.skew(finite)),
        "stat_kurtosis": float(stats.kurtosis(finite)),
        "stat_p05": p05,
        "stat_p25": p25,
        "stat_p75": p75,
        "stat_p95": p95,
        "stat_iqr": p75 - p25,
    }


def extract_noise_features(flux: FloatArray) -> dict[str, float]:
    """Noise and scatter descriptors of the flux.

    Parameters
    ----------
    flux : np.ndarray
        Preprocessed (normalised, detrended) flux values.

    Returns
    -------
    dict[str, float]
        Features keyed with the ``noise_`` prefix.

    Raises
    ------
    ValueError
        If fewer than two finite flux values are available.
    """
    finite = np.asarray(flux, dtype=np.float64).ravel()
    finite = finite[np.isfinite(finite)]
    if finite.size < 2:
        raise ValueError("At least two finite values are required for noise estimation.")

    rms = float(np.sqrt(np.mean(finite ** 2)))
    robust_sigma = _robust_std(finite)
    diffs = np.diff(finite)
    ptp_scatter = float(np.mean(np.abs(diffs)))

    return {
        "noise_rms": rms,
        "noise_mad": float(np.median(np.abs(finite - np.median(finite)))),
        "noise_robust_std": robust_sigma,
        "noise_ptp_scatter": ptp_scatter,
        "noise_snr": float(np.abs(np.mean(finite)) / max(robust_sigma, 1e-12)),
        "noise_ptp_rms_ratio": float(np.std(diffs, ddof=1) / max(np.std(finite, ddof=1), 1e-12)),
    }


def extract_transit_features(
    time: FloatArray,
    flux: FloatArray,
    window_size: int = 13,
    n_sigma: float = 2.5,
    min_dip_points: int = 3,
) -> dict[str, float]:
    """Transit-heuristic features via sliding-window dip detection.

    A dip is defined as a contiguous block of at least ``min_dip_points``
    samples whose flux lies below ``-n_sigma * robust_std``.

    Parameters
    ----------
    time : np.ndarray
        Observation timestamps.
    flux : np.ndarray
        Normalised, detrended flux values.
    window_size : int
        **Unused**; retained for API stability and future local-context logic.
    n_sigma : float
        Number of robust-standard-deviations below zero for the dip threshold.
    min_dip_points : int
        Minimum number of consecutive under-threshold samples for a valid dip.

    Returns
    -------
    dict[str, float]
        Features keyed with the ``transit_`` prefix.

    Raises
    ------
    ValueError
        If ``window_size < 1``, ``n_sigma <= 0``, or ``min_dip_points < 1``.
    """
    _time, flux_arr = _validate_arrays(time, flux)

    if window_size < 1:
        raise ValueError("window_size must be at least 1.")
    if n_sigma <= 0:
        raise ValueError("n_sigma must be positive.")
    if min_dip_points < 1:
        raise ValueError("min_dip_points must be at least 1.")

    robust_sigma = _robust_std(flux_arr)

    # Early exit if the light curve is nearly constant
    if robust_sigma == 0.0:
        return {
            "transit_dip_count": 0.0,
            "transit_dip_depth_max": 0.0,
            "transit_dip_depth_mean": 0.0,
            "transit_dip_width_max": 0.0,
            "transit_dip_width_mean": 0.0,
            "transit_dip_significance_max": 0.0,
        }

    threshold = -n_sigma * robust_sigma
    n = flux_arr.size
    below = flux_arr < threshold

    # Walk through the array to find contiguous dip regions
    dip_ranges: list[tuple[int, int]] = []
    i = 0
    while i < n:
        if below[i]:
            start = i
            i += 1
            while i < n and below[i]:
                i += 1
            end = i - 1
            if (end - start + 1) >= min_dip_points:
                dip_ranges.append((start, end))
        else:
            i += 1

    num_dips = len(dip_ranges)

    if num_dips == 0:
        return {
            "transit_dip_count": 0.0,
            "transit_dip_depth_max": 0.0,
            "transit_dip_depth_mean": 0.0,
            "transit_dip_width_max": 0.0,
            "transit_dip_width_mean": 0.0,
            "transit_dip_significance_max": 0.0,
        }

    depths: list[float] = []
    widths: list[float] = []
    significances: list[float] = []

    for start, end in dip_ranges:
        dip_flux = flux_arr[start : end + 1]
        depth = float(abs(np.min(dip_flux)))
        width = float(_time[end] - _time[start])
        depths.append(depth)
        widths.append(width)
        significances.append(depth / max(robust_sigma, 1e-12))

    max_depth_idx = int(np.argmax(depths))

    return {
        "transit_dip_count": float(num_dips),
        "transit_dip_depth_max": depths[max_depth_idx],
        "transit_dip_depth_mean": float(np.mean(depths)),
        "transit_dip_width_max": widths[max_depth_idx],
        "transit_dip_width_mean": float(np.mean(widths)),
        "transit_dip_significance_max": significances[max_depth_idx],
    }


def extract_timeseries_features(time: FloatArray, flux: FloatArray) -> dict[str, float]:
    """Time-series features including autocorrelation and periodicity.

    Parameters
    ----------
    time : np.ndarray
        Observation timestamps.
    flux : np.ndarray
        Normalised, detrended flux values.

    Returns
    -------
    dict[str, float]
        Features keyed with the ``ts_`` prefix.

    Raises
    ------
    ValueError
        If fewer than three finite samples are available.
    """
    time_arr, flux_arr = _validate_arrays(time, flux)
    n = flux_arr.size

    if n < 3:
        raise ValueError("At least three samples are required for time-series features.")

    # Autocorrelation at small lags
    acf_vals: dict[str, float] = {}
    for lag in (1, 2, 3):
        if lag >= n:
            acf_vals[f"ts_acf_lag{lag}"] = 0.0
        else:
            coeff = float(np.corrcoef(flux_arr[:-lag], flux_arr[lag:])[0, 1])
            acf_vals[f"ts_acf_lag{lag}"] = coeff if np.isfinite(coeff) else 0.0

    # Lomb-Scargle periodogram
    try:
        base_freq = 1.0 / max(time_arr[-1] - time_arr[0], 1e-12)
        freqs = np.linspace(base_freq, 1.0, 5000)
        pgram = signal.lombscargle(time_arr, flux_arr, freqs)
        peak_power = float(np.max(pgram))
        peak_freq = float(freqs[np.argmax(pgram)])
        peak_period = 1.0 / peak_freq if peak_freq > 0 else 0.0
    except Exception:
        logger.warning("Lomb-Scargle periodogram computation failed.")
        peak_power = 0.0
        peak_period = 0.0

    variability_index = float(np.std(flux_arr) / max(np.mean(np.abs(flux_arr)), 1e-12))

    return {
        **acf_vals,
        "ts_ls_peak_power": peak_power,
        "ts_ls_peak_period": peak_period,
        "ts_variability_index": variability_index,
    }


def extract_distribution_features(
    flux: FloatArray,
    n_bins: int = 20,
) -> dict[str, float]:
    """Flux-distribution shape features (entropy, tails, concentration).

    Parameters
    ----------
    flux : np.ndarray
        Preprocessed (normalised, detrended) flux values.
    n_bins : int
        Number of histogram bins for distribution analysis.

    Returns
    -------
    dict[str, float]
        Features keyed with the ``dist_`` prefix.

    Raises
    ------
    ValueError
        If no finite flux values exist or ``n_bins < 2``.
    """
    finite = np.asarray(flux, dtype=np.float64).ravel()
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        raise ValueError("Flux array has no finite values.")
    if n_bins < 2:
        raise ValueError("n_bins must be at least 2.")

    counts, edges = np.histogram(finite, bins=n_bins, density=True)
    probs = counts / max(np.sum(counts), 1e-12)

    # Entropy of the binned distribution (uniform → high, peaked → low)
    entropy = float(-np.sum(probs[probs > 0] * np.log(probs[probs > 0])))
    max_entropy = float(np.log(n_bins))
    entropy_ratio = entropy / max_entropy if max_entropy > 0 else 0.0

    # Tail mass: fraction of histogram mass in outermost bins
    tail_k = max(1, n_bins // 10)
    tail_mass = float(np.sum(counts[:tail_k]) + np.sum(counts[-tail_k:]))

    # Concentration: mass within the central quartile
    centers = (edges[:-1] + edges[1:]) / 2.0
    q25, q75 = float(np.percentile(finite, 25)), float(np.percentile(finite, 75))
    inner = (centers >= q25) & (centers <= q75)
    concentration = float(np.sum(counts[inner])) / max(np.sum(counts), 1e-12)

    return {
        "dist_entropy": entropy,
        "dist_entropy_ratio": entropy_ratio,
        "dist_tail_mass": tail_mass,
        "dist_concentration": concentration,
    }


# ---------------------------------------------------------------------------
# Aggregate entry point
# ---------------------------------------------------------------------------


def extract_features(
    time: FloatArray,
    flux: FloatArray,
    flux_error: FloatArray | None = None,
    window_size: int = 13,
    n_sigma: float = 2.5,
    min_dip_points: int = 3,
    n_bins: int = 20,
) -> dict[str, float]:
    """Extract a complete feature vector from a preprocessed light curve.

    Convenience wrapper that calls all five category extractors and merges
    their results into a single flat dictionary.

    Parameters
    ----------
    time : np.ndarray
        Observation timestamps.
    flux : np.ndarray
        Normalised, detrended flux values.
    flux_error : np.ndarray or None
        Flux uncertainty (currently unused; reserved for future use).
    window_size : int
        Passed to :func:`extract_transit_features`.
    n_sigma : float
        Passed to :func:`extract_transit_features`.
    min_dip_points : int
        Passed to :func:`extract_transit_features`.
    n_bins : int
        Passed to :func:`extract_distribution_features`.

    Returns
    -------
    dict[str, float]
        Flat dictionary of all extracted features.
    """
    _validate_arrays(time, flux)

    result: dict[str, float] = {}
    result.update(extract_statistical_features(flux))
    result.update(extract_noise_features(flux))
    result.update(extract_transit_features(time, flux, window_size, n_sigma, min_dip_points))
    result.update(extract_timeseries_features(time, flux))
    result.update(extract_distribution_features(flux, n_bins))

    logger.info("Extracted %d features from light curve.", len(result))
    return result


def extract_features_from_batch(
    batch: LightCurveBatch,
    **kwargs: Any,
) -> list[dict[str, float]]:
    """Convenience: extract features for every light curve in a batch.

    Parameters
    ----------
    batch : LightCurveBatch
        Batch of preprocessed light curves.
    **kwargs
        Additional keyword arguments forwarded to :func:`extract_features`.

    Returns
    -------
    list[dict[str, float]]
        One feature dictionary per light curve in the batch.
    """
    results: list[dict[str, float]] = []
    for i in range(len(batch.time)):
        error = None if batch.flux_error is None else batch.flux_error[i]
        feats = extract_features(
            batch.time[i],
            batch.flux[i],
            flux_error=error,
            **kwargs,
        )
        results.append(feats)
    return results
