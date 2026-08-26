"""Semantic tokens for the controlled NeoEng-D-Trace dark theme.

The token set is intentionally small and immutable.  UI code should refer to
these semantic roles instead of introducing one-off colors in widget styles.
Canvas/scene rendering colors remain outside this module because they are
content semantics, not application chrome.
"""

from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass(frozen=True)
class ThemeTokens:
    """Single source of truth for application chrome colors."""

    window: str = "#171a1f"
    canvas: str = "#11161b"
    surface: str = "#1d2329"
    surface_alt: str = "#252c33"
    surface_raised: str = "#2d363e"
    border: str = "#3b4652"
    border_strong: str = "#526170"
    text_primary: str = "#e8edf2"
    text_secondary: str = "#a8b2bd"
    text_disabled: str = "#66717c"
    accent: str = "#59d8e8"
    accent_hover: str = "#76cef2"
    accent_pressed: str = "#3f93ad"
    selection: str = "#365f78"
    focus: str = "#7ce9f5"
    error: str = "#e77b86"
    warning: str = "#e4bb6a"
    success: str = "#75d99b"

    @property
    def audit_palette(self) -> tuple[str, ...]:
        """Colors expected in every non-modal UI capture."""

        return (
            self.window,
            self.surface,
            self.surface_alt,
            self.border,
            self.text_primary,
            self.accent,
        )

    @property
    def colors(self) -> tuple[str, ...]:
        """All declared hex colors, in declaration order."""

        return tuple(getattr(self, field.name) for field in fields(self))

    @staticmethod
    def rgba(color: str, alpha: int) -> str:
        """Return a QSS rgba() value derived from a declared token."""

        if (
            not isinstance(color, str)
            or len(color) != 7
            or not color.startswith("#")
            or any(character not in "0123456789abcdefABCDEF" for character in color[1:])
            or isinstance(alpha, bool)
            or not isinstance(alpha, int)
            or not 0 <= alpha <= 255
        ):
            raise ValueError("invalid theme color or alpha")
        red, green, blue = (int(color[index : index + 2], 16) for index in (1, 3, 5))
        return f"rgba({red}, {green}, {blue}, {alpha})"


THEME_TOKENS = ThemeTokens()


def _channel(value: int) -> float:
    normalized = value / 255.0
    return (
        normalized / 12.92
        if normalized <= 0.04045
        else ((normalized + 0.055) / 1.055) ** 2.4
    )


def _relative_luminance(color: str) -> float:
    red, green, blue = (int(color[index : index + 2], 16) for index in (1, 3, 5))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast_ratio(foreground: str, background: str) -> float:
    """Return the WCAG relative contrast ratio for two token colors."""

    foreground_luminance = _relative_luminance(foreground)
    background_luminance = _relative_luminance(background)
    lighter = max(foreground_luminance, background_luminance)
    darker = min(foreground_luminance, background_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def token_contrast_ratios(tokens: ThemeTokens = THEME_TOKENS) -> dict[str, float]:
    """Return the required primary text and focus contrast ratios."""

    return {
        "primary_on_window": contrast_ratio(tokens.text_primary, tokens.window),
        "secondary_on_surface": contrast_ratio(tokens.text_secondary, tokens.surface),
        "focus_on_window": contrast_ratio(tokens.focus, tokens.window),
    }


__all__ = ["THEME_TOKENS", "ThemeTokens", "contrast_ratio", "token_contrast_ratios"]
