"""Centralized product identity for NeoEng-D-Trace.

This module contains identity and display helpers only. It does not invent a
project-file schema or installer identity that the product has not approved.
``LEGACY_APP_NAMES`` is restricted to compatibility checks and historical
references.
"""

from __future__ import annotations

from typing import Final, Optional

APP_NAME: Final[str] = "NeoEng-D-Trace"
APP_DISPLAY_NAME: Final[str] = APP_NAME
APP_VERSION: Final[str] = "0.2.0"
APP_UI_EDITION: Final[str] = "v2"
APP_ID: Final[str] = "neoeng_d_trace"
APP_AUTHOR: Final[str] = "NeoEng-D-Trace Maintainer"
CONFIG_DIR_NAME: Final[str] = APP_DISPLAY_NAME
LOGGER_NAME: Final[str] = APP_DISPLAY_NAME
GLTF_GENERATOR: Final[str] = f"{APP_DISPLAY_NAME} GLTF Exporter"

# Deliberately undefined until the format ADR is approved.
PROJECT_FORMAT_ID: Final[Optional[str]] = None
PROJECT_FORMAT_VERSION: Final[Optional[int]] = None

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
    lang = normalize_language(language)
    return f"{APP_DISPLAY_NAME} {APP_UI_EDITION} - " f"{_ENGINE_MODE_LABELS[lang]}"
