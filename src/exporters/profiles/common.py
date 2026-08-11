"""Shared validation for engine-specific metadata profiles."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def normalized_rect_and_pivot(
    metadata: Mapping[str, Any],
) -> tuple[dict[str, float], tuple[float, float]]:
    """Return one validated top-left rectangle and local pixel pivot."""
    rect_raw = metadata.get("rect")
    if not isinstance(rect_raw, Mapping):
        raise ValueError("rect must be an object")

    rect = {
        field: _finite_number(rect_raw.get(field), f"rect.{field}")
        for field in ("x", "y", "w", "h")
    }
    if rect["w"] <= 0 or rect["h"] <= 0:
        raise ValueError("rect width and height must be positive")

    pivot_raw = metadata.get("pivot", {"x": rect["w"] / 2.0, "y": rect["h"] / 2.0})
    if isinstance(pivot_raw, Mapping):
        pivot = (
            _finite_number(pivot_raw.get("x"), "pivot.x"),
            _finite_number(pivot_raw.get("y"), "pivot.y"),
        )
    elif isinstance(pivot_raw, Sequence) and not isinstance(pivot_raw, (str, bytes)):
        if len(pivot_raw) != 2:
            raise ValueError("pivot must contain x and y")
        pivot = (
            _finite_number(pivot_raw[0], "pivot.x"),
            _finite_number(pivot_raw[1], "pivot.y"),
        )
    else:
        raise ValueError("pivot must be an object or x/y sequence")

    return rect, pivot
