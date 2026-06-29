"""Light curve preprocessing utilities.

This module prepares Kepler and TESS light curves for downstream transit
detection. It loads FITS files with Lightkurve, extracts time and flux arrays,
removes invalid samples, normalizes flux, removes slow stellar variability,
clips statistical outliers, and optionally smooths the final signal.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import numpy.typing as npt
from scipy.signal import medfilt, savgol_filter

from src.logging_utils import get_logger


if TYPE_CHECKING:
    from lightkurve import LightCurve


logger = get_logger(__name__)

FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True)
class LightCurveBatch:
    """Container for light curve arrays.

    This class is retained for tests and array-level workflows. The public
    preprocessing pipeline returns a Lightkurve ``LightCurve`` object.

    Attributes:
        time: Observation timestamps.
        flux: Flux values aligned to ``time``.
        flux_error: Optional flux uncertainty values.
    """

    time: FloatArray
    flux: FloatArray
    flux_error: FloatArray | None = None


def _import_lightkurve() -> Any:
    """Import Lightkurve lazily.

    Returns:
        Imported Lightkurve module.

    Raises:
        ImportError: If Lightkurve is not installed.
    """

    try:
        import lightkurve as lk
    except ImportError as exc:
        logger.exception("Lightkurve is required to load FITS light curves.")
        raise ImportError(
            "Lightkurve is required for preprocessing. Install dependencies "
            "with `pip install -r requirements.txt`."
        ) from exc

    return lk


def _as_float_array(values: Any, field_name: str) -> FloatArray:
    """Convert Lightkurve or Astropy values into a one-dimensional float array.

    Args:
        values: Raw values, possibly with an Astropy ``value`` attribute.
        field_name: Name used in error messages.

    Returns:
        One-dimensional float64 array.

    Raises:
        ValueError: If values cannot be converted into a non-empty array.
    """

    raw_values = values.value if hasattr(values, "value") else values
    try:
        array = np.asarray(raw_values, dtype=np.float64).reshape(-1)
    except (TypeError, ValueError) as exc:
        logger.exception("Could not convert %s values to float array.", field_name)
        raise ValueError(f"{field_name} values must be numeric.") from exc

    if array.size == 0:
        logger.error("%s array is empty.", field_name)
        raise ValueError(f"{field_name} array cannot be empty.")

    return array


def _extract_arrays(lightcurve: "LightCurve") -> LightCurveBatch:
    """Extract numeric arrays from a Lightkurve object.

    Args:
        lightcurve: Source Lightkurve object.

    Returns:
        Extracted numeric arrays.

    Raises:
        ValueError: If required arrays are missing or misaligned.
    """

    try:
        time = _as_float_array(lightcurve.time, "time")
        flux = _as_float_array(lightcurve.flux, "flux")
        flux_error = None
        if getattr(lightcurve, "flux_err", None) is not None:
            flux_error = _as_float_array(lightcurve.flux_err, "flux_error")
    except AttributeError as exc:
        logger.exception("Input object does not look like a Lightkurve curve.")
        raise ValueError("Expected a Lightkurve LightCurve object.") from exc

    if time.shape != flux.shape:
        logger.error(
            "Time shape %s does not match flux shape %s.",
            time.shape,
            flux.shape,
        )
        raise ValueError("Time and flux arrays must have the same shape.")

    if flux_error is not None and flux_error.shape != flux.shape:
        logger.error(
            "Flux error shape %s does not match flux shape %s.",
            flux_error.shape,
            flux.shape,
        )
        raise ValueError("Flux error and flux arrays must have the same shape.")

    return LightCurveBatch(time=time, flux=flux, flux_error=flux_error)


def _build_lightcurve(
    time: FloatArray,
    flux: FloatArray,
    flux_error: FloatArray | None = None,
) -> "LightCurve":
    """Build a Lightkurve object from numeric arrays.

    Args:
        time: Observation timestamps.
        flux: Flux values.
        flux_error: Optional flux uncertainty values.

    Returns:
        Lightkurve ``LightCurve`` object.
    """

    lk = _import_lightkurve()
    kwargs: dict[str, FloatArray] = {"time": time, "flux": flux}
    if flux_error is not None:
        kwargs["flux_err"] = flux_error

    return lk.LightCurve(**kwargs)


def _validate_positive_odd_window(window_length: int, array_size: int) -> int:
    """Validate and adjust a filter window length.

    Args:
        window_length: Requested filter window length.
        array_size: Number of samples in the target array.

    Returns:
        Valid odd window length no larger than ``array_size``.

    Raises:
        ValueError: If no valid window can be created.
    """

    if window_length < 3:
        logger.error("Filter window length %d is too small.", window_length)
        raise ValueError("Filter window length must be at least 3.")

    window = min(window_length, array_size)
    if window % 2 == 0:
        window -= 1

    if window < 3:
        logger.error("Not enough samples for filter window. Samples: %d.", array_size)
        raise ValueError("At least 3 samples are required for filtering.")

    return window


def load_lightcurve(path: str | Path) -> "LightCurve":
    """Load a Kepler or TESS FITS light curve with Lightkurve.

    Args:
        path: Path to a FITS light curve file.

    Returns:
        Loaded Lightkurve ``LightCurve`` object.

    Raises:
        FileNotFoundError: If the provided file does not exist.
        ValueError: If the file cannot be parsed as a light curve.
        ImportError: If Lightkurve is not installed.
    """

    fits_path = Path(path).expanduser().resolve()
    if not fits_path.is_file():
        logger.error("Light curve file not found: %s", fits_path)
        raise FileNotFoundError(f"Light curve file not found: {fits_path}")

    lk = _import_lightkurve()
    try:
        read_lightcurve = getattr(lk, "read", None)
        if read_lightcurve is not None:
            lightcurve = read_lightcurve(fits_path)
        else:
            lightcurve = lk.LightCurve.read(fits_path)
    except Exception as exc:
        logger.exception("Failed to load light curve FITS file: %s", fits_path)
        raise ValueError(f"Failed to load light curve FITS file: {fits_path}") from exc

    logger.info("Loaded light curve from %s with %d samples.", fits_path, len(lightcurve))
    return lightcurve


def remove_nan(lightcurve: "LightCurve") -> "LightCurve":
    """Remove samples with non-finite time, flux, or flux error values.

    Args:
        lightcurve: Input Lightkurve ``LightCurve`` object.

    Returns:
        Lightkurve ``LightCurve`` object with invalid samples removed.

    Raises:
        ValueError: If the light curve arrays are empty or misaligned.
    """

    arrays = _extract_arrays(lightcurve)
    mask = np.isfinite(arrays.time) & np.isfinite(arrays.flux)
    if arrays.flux_error is not None:
        mask &= np.isfinite(arrays.flux_error)

    removed_count = int(mask.size - mask.sum())
    if not np.any(mask):
        logger.error("All samples were removed during NaN filtering.")
        raise ValueError("Light curve has no finite samples.")

    logger.info("Removed %d non-finite light curve samples.", removed_count)
    flux_error = arrays.flux_error[mask] if arrays.flux_error is not None else None
    return _build_lightcurve(arrays.time[mask], arrays.flux[mask], flux_error)


def normalize(lightcurve: "LightCurve") -> "LightCurve":
    """Normalize flux values around zero using median scaling.

    Args:
        lightcurve: Input Lightkurve ``LightCurve`` object.

    Returns:
        Lightkurve ``LightCurve`` object with normalized flux.

    Raises:
        ValueError: If the median flux is zero or not finite.
    """

    arrays = _extract_arrays(lightcurve)
    median_flux = float(np.nanmedian(arrays.flux))
    if not np.isfinite(median_flux) or median_flux == 0.0:
        logger.error("Invalid median flux for normalization: %s", median_flux)
        raise ValueError("Flux median must be finite and non-zero.")

    normalized_flux = (arrays.flux / median_flux) - 1.0
    normalized_error = None
    if arrays.flux_error is not None:
        normalized_error = arrays.flux_error / abs(median_flux)

    logger.info("Normalized flux with median value %.8f.", median_flux)
    return _build_lightcurve(arrays.time, normalized_flux, normalized_error)


def detrend(
    lightcurve: "LightCurve",
    window_length: int = 101,
    polyorder: int = 2,
) -> "LightCurve":
    """Remove slow stellar variability using Savitzky-Golay filtering.

    Args:
        lightcurve: Input Lightkurve ``LightCurve`` object.
        window_length: Odd smoothing window length in samples.
        polyorder: Polynomial order used by the Savitzky-Golay filter.

    Returns:
        Lightkurve ``LightCurve`` object with detrended flux.

    Raises:
        ValueError: If the filter configuration is invalid.
    """

    arrays = _extract_arrays(lightcurve)
    window = _validate_positive_odd_window(window_length, arrays.flux.size)
    if polyorder < 0 or polyorder >= window:
        logger.error("Invalid polyorder %d for window length %d.", polyorder, window)
        raise ValueError("polyorder must be non-negative and smaller than window_length.")

    try:
        trend = savgol_filter(arrays.flux, window_length=window, polyorder=polyorder)
    except Exception as exc:
        logger.exception("Savitzky-Golay detrending failed.")
        raise ValueError("Failed to detrend light curve.") from exc

    detrended_flux = arrays.flux - trend
    valid_mask = np.isfinite(detrended_flux)
    if not np.all(valid_mask):
        logger.warning(
            "Removed %d samples with invalid detrended flux.",
            int(valid_mask.size - valid_mask.sum()),
        )

    if not np.any(valid_mask):
        logger.error("Detrending produced no finite samples.")
        raise ValueError("Detrending produced no finite samples.")

    flux_error = arrays.flux_error[valid_mask] if arrays.flux_error is not None else None
    logger.info(
        "Detrended light curve using Savitzky-Golay window=%d polyorder=%d.",
        window,
        polyorder,
    )
    return _build_lightcurve(
        arrays.time[valid_mask],
        detrended_flux[valid_mask],
        flux_error,
    )


def sigma_clip(lightcurve: "LightCurve", sigma: float = 5.0) -> "LightCurve":
    """Remove flux outliers using median absolute deviation sigma clipping.

    Args:
        lightcurve: Input Lightkurve ``LightCurve`` object.
        sigma: Number of robust standard deviations to keep.

    Returns:
        Lightkurve ``LightCurve`` object with outliers removed.

    Raises:
        ValueError: If ``sigma`` is not positive or clipping removes all data.
    """

    if sigma <= 0.0:
        logger.error("Invalid sigma clipping threshold: %.4f", sigma)
        raise ValueError("sigma must be positive.")

    arrays = _extract_arrays(lightcurve)
    median_flux = float(np.nanmedian(arrays.flux))
    mad = float(np.nanmedian(np.abs(arrays.flux - median_flux)))

    if not np.isfinite(mad):
        logger.error("Median absolute deviation is not finite.")
        raise ValueError("Cannot sigma clip a light curve with non-finite MAD.")

    if mad == 0.0:
        logger.info("Skipping sigma clipping because MAD is zero.")
        return lightcurve

    robust_std = 1.4826 * mad
    mask = np.abs(arrays.flux - median_flux) <= sigma * robust_std
    removed_count = int(mask.size - mask.sum())
    if not np.any(mask):
        logger.error("Sigma clipping removed every sample.")
        raise ValueError("Sigma clipping removed every sample.")

    flux_error = arrays.flux_error[mask] if arrays.flux_error is not None else None
    logger.info("Sigma clipping removed %d outlier samples.", removed_count)
    return _build_lightcurve(arrays.time[mask], arrays.flux[mask], flux_error)


def median_filter(lightcurve: "LightCurve", kernel_size: int = 5) -> "LightCurve":
    """Optionally smooth flux with a median filter.

    Args:
        lightcurve: Input Lightkurve ``LightCurve`` object.
        kernel_size: Odd median filter kernel size in samples.

    Returns:
        Lightkurve ``LightCurve`` object with median-filtered flux.

    Raises:
        ValueError: If the kernel size is invalid.
    """

    arrays = _extract_arrays(lightcurve)
    kernel = _validate_positive_odd_window(kernel_size, arrays.flux.size)
    filtered_flux = medfilt(arrays.flux, kernel_size=kernel)
    logger.info("Applied median filter with kernel size %d.", kernel)
    return _build_lightcurve(arrays.time, filtered_flux, arrays.flux_error)


def preprocess_pipeline(
    path: str | Path,
    *,
    savgol_window_length: int = 101,
    savgol_polyorder: int = 2,
    sigma: float = 5.0,
    apply_median_filter: bool = False,
    median_kernel_size: int = 5,
) -> "LightCurve":
    """Run the full light curve preprocessing pipeline.

    Args:
        path: Path to a Kepler or TESS FITS light curve file.
        savgol_window_length: Savitzky-Golay detrending window length.
        savgol_polyorder: Savitzky-Golay polynomial order.
        sigma: Sigma clipping threshold.
        apply_median_filter: Whether to smooth the final flux values.
        median_kernel_size: Median filter kernel size when enabled.

    Returns:
        Clean preprocessed Lightkurve ``LightCurve`` object.

    Raises:
        FileNotFoundError: If the input path does not exist.
        ImportError: If Lightkurve is not installed.
        ValueError: If preprocessing fails due to invalid data or parameters.
    """

    logger.info("Starting preprocessing pipeline for %s.", path)
    lightcurve = load_lightcurve(path)
    lightcurve = remove_nan(lightcurve)
    lightcurve = normalize(lightcurve)
    lightcurve = detrend(
        lightcurve,
        window_length=savgol_window_length,
        polyorder=savgol_polyorder,
    )
    lightcurve = sigma_clip(lightcurve, sigma=sigma)

    if apply_median_filter:
        lightcurve = median_filter(lightcurve, kernel_size=median_kernel_size)

    logger.info("Completed preprocessing pipeline with %d samples.", len(lightcurve))
    return lightcurve


def normalize_flux(flux: FloatArray) -> FloatArray:
    """Normalize a raw flux array around zero using median scaling.

    Args:
        flux: Raw or detrended flux array.

    Returns:
        Median-normalized flux array.

    Raises:
        ValueError: If the input array is empty or has an invalid median.
    """

    flux_array = np.asarray(flux, dtype=np.float64)
    if flux_array.size == 0:
        logger.error("Flux array cannot be empty.")
        raise ValueError("Flux array cannot be empty.")

    median_flux = float(np.nanmedian(flux_array))
    if not np.isfinite(median_flux) or median_flux == 0.0:
        logger.error("Invalid median flux for normalization: %s", median_flux)
        raise ValueError("Flux median must be finite and non-zero.")

    logger.info("Normalized flux array with median value %.8f.", median_flux)
    return (flux_array / median_flux) - 1.0


def remove_nan_samples(time: FloatArray, flux: FloatArray) -> LightCurveBatch:
    """Remove samples where time or flux is not finite.

    Args:
        time: Observation timestamps.
        flux: Flux values aligned to ``time``.

    Returns:
        Cleaned array batch.

    Raises:
        ValueError: If ``time`` and ``flux`` have different shapes.
    """

    time_array = np.asarray(time, dtype=np.float64)
    flux_array = np.asarray(flux, dtype=np.float64)
    if time_array.shape != flux_array.shape:
        logger.error(
            "Time shape %s does not match flux shape %s.",
            time_array.shape,
            flux_array.shape,
        )
        raise ValueError("Time and flux arrays must have the same shape.")

    mask = np.isfinite(time_array) & np.isfinite(flux_array)
    if not np.any(mask):
        logger.error("Light curve arrays have no finite samples.")
        raise ValueError("Light curve arrays have no finite samples.")

    logger.info("Removed %d non-finite array samples.", int(mask.size - mask.sum()))
    return LightCurveBatch(time=time_array[mask], flux=flux_array[mask])
