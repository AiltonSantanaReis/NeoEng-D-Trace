from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pytest

from src.ui.theme_qss import QSS, build_qss
from src.ui.theme_tokens import (
    THEME_TOKENS,
    ThemeTokens,
    token_contrast_ratios,
)


def test_theme_tokens_are_unique_and_have_accessible_contrast() -> None:
    colors = THEME_TOKENS.colors
    assert len(colors) == len(set(colors))
    assert all(len(color) == 7 and color.startswith("#") for color in colors)

    ratios = token_contrast_ratios()
    assert ratios["primary_on_window"] >= 4.5
    assert ratios["secondary_on_surface"] >= 4.5
    assert ratios["focus_on_window"] >= 3.0


def test_qss_is_generated_from_tokens_and_exposes_focus_states() -> None:
    generated = build_qss(THEME_TOKENS)
    assert generated == QSS
    assert "QPushButton:focus" in generated
    assert "QToolButton:focus" in generated
    assert THEME_TOKENS.accent_hover in generated
    assert 'QPushButton[uiRole="tool"]' in generated
    assert "#FF4500" not in generated
    assert "#00BFFF" not in generated
    for color in THEME_TOKENS.audit_palette:
        assert color in generated


def test_rgba_rejects_invalid_color_or_alpha() -> None:
    with pytest.raises(ValueError):
        ThemeTokens.rgba("not-a-color", 32)
    with pytest.raises(ValueError):
        ThemeTokens.rgba(THEME_TOKENS.accent, 256)
    with pytest.raises(ValueError):
        ThemeTokens.rgba(THEME_TOKENS.accent, True)


def test_theme_token_schema_has_no_unreviewed_mutable_fields() -> None:
    assert tuple(field.name for field in fields(THEME_TOKENS)) == (
        "window",
        "canvas",
        "surface",
        "surface_alt",
        "surface_raised",
        "border",
        "border_strong",
        "text_primary",
        "text_secondary",
        "text_disabled",
        "accent",
        "accent_hover",
        "accent_pressed",
        "selection",
        "focus",
        "error",
        "warning",
        "success",
    )
    with pytest.raises((AttributeError, TypeError)):
        THEME_TOKENS.accent = "#ffffff"  # type: ignore[misc]


def test_application_chrome_does_not_reintroduce_inline_theme_styles() -> None:
    roots = (Path("src/ui"), Path("src/tools"))
    offenders: list[str] = []
    for root in roots:
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "setStyleSheet(" in text:
                offenders.append(path.as_posix())
    assert offenders == [], f"inline application styles remain: {offenders}"
