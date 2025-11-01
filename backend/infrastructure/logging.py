"""Utilities for configuring backend logging output."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Iterable


LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
LOG_FILE_NAME = "backend.log"
MAX_LOG_BYTES = 1_000_000
BACKUP_COUNT = 3


def _has_handler(handlers: Iterable[logging.Handler], log_path: Path) -> bool:
    """Return ``True`` when a matching file handler is already registered."""

    for handler in handlers:
        if isinstance(handler, RotatingFileHandler) and getattr(
            handler, "baseFilename", None
        ) == str(log_path):
            return True
    return False


def configure_logging(level: int = logging.INFO) -> Path:
    """Configure application wide logging.

    The backend writes structured log entries to ``backend/logs/backend.log`` while
    still emitting records to standard output via uvicorn's default configuration.
    ``uvicorn`` loggers are configured to propagate so that the same handler setup
    applies to access and application logs.

    Parameters
    ----------
    level:
        The log level to apply to the root logger. ``logging.INFO`` is the default
        as it provides actionable signals without being too verbose.

    Returns
    -------
    Path
        The path to the log file. This enables callers to surface the location in
        documentation or during startup.
    """

    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / LOG_FILE_NAME

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not _has_handler(root_logger.handlers, log_path):
        file_handler = RotatingFileHandler(
            log_path, maxBytes=MAX_LOG_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(file_handler)

    # Forward uvicorn logs (both application and access logs) to the root logger so
    # the rotating file handler receives them as well.
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(logger_name).propagate = True

    return log_path


__all__ = ["configure_logging"]

