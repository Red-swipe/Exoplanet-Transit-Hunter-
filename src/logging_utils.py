"""Logging helpers for Exoplanet Transit Hunter.

All modules should use these helpers instead of configuring logging locally.
"""

from __future__ import annotations

import functools
import logging
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

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


@contextmanager
def timer(logger: logging.Logger, label: str, **extra: Any) -> Iterator[None]:
    """Context manager that logs elapsed time on exit.

    Usage::

        logger = get_logger(__name__)
        with timer(logger, "search_target", target_id="KIC 12345"):
            search_target(...)

    Args:
        logger: Logger instance to write the timing message to.
        label: Short label describing the timed operation.
        **extra: Additional key=value pairs appended to the log message.
    """

    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    extra_str = ", ".join(f"{k}={v}" for k, v in extra.items()) if extra else ""
    suffix = f" ({extra_str})" if extra_str else ""
    logger.info("[timing] %s: %.3fs%s", label, elapsed, suffix)


def log_duration(
    logger: logging.Logger,
    label: str | None = None,
    log_level: int = logging.INFO,
) -> Any:
    """Decorator that logs the duration of each call to the decorated function.

    Usage::

        logger = get_logger(__name__)

        @log_duration(logger, "my_function")
        def my_function() -> int:
            ...

    Args:
        logger: Logger instance to write the timing message to.
        label: Optional label for the log message (defaults to ``func.__name__``).
        log_level: Logging level to use (default ``logging.INFO``).

    Returns:
        Decorated function.
    """

    def decorator(func: Any) -> Any:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            name = label or func.__name__
            logger.log(log_level, "[timing] %s: %.3fs", name, elapsed)
            return result

        return wrapper

    return decorator
