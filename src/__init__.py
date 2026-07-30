"""Single source package for NeoEng-D-Trace.

All runtime implementation lives under :mod:`src`.  The product/distribution
name is NeoEng-D-Trace; no duplicate package tree or compatibility bridge is
used.
"""

from .core.app_identity import (
    APP_AUTHOR,
    APP_DISPLAY_NAME,
    APP_ID,
    APP_NAME,
    APP_UI_EDITION,
    APP_VERSION,
    CONFIG_DIR_NAME,
    GLTF_GENERATOR,
    LEGACY_APP_NAMES,
    LOGGER_NAME,
    PROJECT_FORMAT_ID,
    PROJECT_FORMAT_VERSION,
    build_window_title,
    normalize_language,
)

__version__ = APP_VERSION

__all__ = [
    "APP_AUTHOR",
    "APP_DISPLAY_NAME",
    "APP_ID",
    "APP_NAME",
    "APP_UI_EDITION",
    "APP_VERSION",
    "CONFIG_DIR_NAME",
    "GLTF_GENERATOR",
    "LEGACY_APP_NAMES",
    "LOGGER_NAME",
    "PROJECT_FORMAT_ID",
    "PROJECT_FORMAT_VERSION",
    "build_window_title",
    "normalize_language",
    "__version__",
]
