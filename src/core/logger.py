"""Logging configuration for the single-tree NeoEng-D-Trace runtime."""

from __future__ import annotations

import functools
import logging
import os
import sys
from typing import Any, Callable, Optional

from src.core.app_identity import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)
_OWNED_HANDLER_ATTR = "_neoeng_d_trace_owned"


def _owned_handlers(target: logging.Logger):
    return [
        handler
        for handler in target.handlers
        if getattr(handler, _OWNED_HANDLER_ATTR, False)
    ]


def _add_handler(
    target: logging.Logger,
    handler: logging.Handler,
    formatter: logging.Formatter,
    level: int,
) -> None:
    handler.setFormatter(formatter)
    handler.setLevel(level)
    setattr(handler, _OWNED_HANDLER_ATTR, True)
    target.addHandler(handler)


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = False,
    log_file_path: Optional[str] = None,
):
    """Configure one route for app logs and one route for module logs.

    The named application logger does not propagate to the root logger. Module
    loggers continue to propagate to the root logger. This prevents the same
    record from being emitted once by NeoEng-D-Trace and again by a root handler.
    """

    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    level = level_map.get(str(log_level).upper(), logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    root = logging.getLogger()
    logger.setLevel(level)
    root.setLevel(level)
    logger.propagate = False

    # Reconfiguration is deterministic and removes only handlers owned here.
    for target in (logger, root):
        for handler in _owned_handlers(target):
            target.removeHandler(handler)
            handler.close()

    _add_handler(logger, logging.StreamHandler(sys.stdout), formatter, level)
    _add_handler(root, logging.StreamHandler(sys.stdout), formatter, level)

    if log_to_file and log_file_path:
        try:
            log_dir = os.path.dirname(log_file_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            _add_handler(
                logger,
                logging.FileHandler(log_file_path, encoding="utf-8"),
                formatter,
                level,
            )
            _add_handler(
                root,
                logging.FileHandler(log_file_path, encoding="utf-8"),
                formatter,
                level,
            )
        except Exception as exc:
            logger.warning("Failed to setup file logging: %s", exc)


def log_errors(func: Callable) -> Callable:
    """Decorate a critical function and retain a complete traceback."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            logger.error("Error in %s: %s", func.__name__, exc, exc_info=True)
            raise

    return wrapper
