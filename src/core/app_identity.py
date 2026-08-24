"""Centralized product identity for NeoEng-D-Trace.

This module contains approved product, display, and project-format identity.
It does not define installer identity beyond the decisions already approved.
``LEGACY_APP_NAMES`` is restricted to compatibility checks and historical
references.
"""

from __future__ import annotations

from typing import Final

APP_NAME: Final[str] = "NeoEng-D-Trace"
APP_DISPLAY_NAME: Final[str] = APP_NAME
APP_VERSION: Final[str] = "0.3.0"
APP_UI_EDITION: Final[str] = "v2"
APP_ID: Final[str] = "neoeng_d_trace"
APP_AUTHOR: Final[str] = "NeoEng-D-Trace Maintainer"
CONFIG_DIR_NAME: Final[str] = APP_DISPLAY_NAME
LOGGER_NAME: Final[str] = APP_DISPLAY_NAME
GLTF_GENERATOR: Final[str] = f"{APP_DISPLAY_NAME} GLTF Exporter"

# Approved by the Stage 3 project-format ADR.
PROJECT_FORMAT_ID: Final[str] = "neoeng-d-trace-project"
PROJECT_FORMAT_VERSION: Final[int] = 1

LEGACY_APP_NAMES: Final[tuple[str, ...]] = (
    "PolygonTool",
    "PolygonTool v2",
)

_SUPPORTED_LANGUAGES: Final[tuple[str, ...]] = ("en", "pt")
_ENGINE_MODE_LABELS: Final[dict[str, str]] = {
    "en": "Engine Mode",
    "pt": "Modo Engine",
}


def normalize_language(language: str | None) -> str:
    """Return a supported UI language, falling back to English."""

    if language in _SUPPORTED_LANGUAGES:
        return language
    return "en"


def build_window_title(
    language: str | None = "en",
    document_name: str | None = None,
) -> str:
    """Build the main-window title in English or Portuguese.

    The document title intentionally contains no translated format-specific
    text, preventing the visual brand from becoming a project-file identifier.
    """

    if document_name:
        return f"{APP_DISPLAY_NAME} - {document_name}"
    # The reference shell uses the product brand alone in the native title
    # bar. The edition and engine-mode labels remain metadata for
    # About/diagnostic surfaces and must not change the reference chrome.
    return APP_DISPLAY_NAME
