"""Logging helpers for Exoplanet Transit Hunter.

All modules should use these helpers instead of configuring logging locally.
"""

from __future__ import annotations

import logging
import sys

from config import settings


def configure_logging(log_level: str | None = None) -> None:
    """Configure application-wide structured console logging.

    Args:
        log_level: Optional logging level override. If omitted, the value from
            application settings is used.
    """

    level_name = log_level or settings.log_level
    logging.basicConfig(
        level=getattr(logging, level_name.upper(), logging.INFO),
        format=(
            "%(asctime)s | %(levelname)s | %(name)s | "
            "%(filename)s:%(lineno)d | %(message)s"
        ),
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured for the project.

    Args:
        name: Logger name, usually ``__name__``.

    Returns:
        Configured logger instance.
    """

    return logging.getLogger(name)
