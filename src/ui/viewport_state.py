"""Structured viewport state and compatibility formatters.

The dataclass is the canonical contract. Text formatters are presentation and
legacy adapters only; tests and editor logic should consume :class:`ViewportState`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ViewportState:
    """Immutable snapshot of the user-visible viewport state."""

    view_mode: str
    zoom: float
    snap_enabled: bool
    snap_grid_size: int
    grid_visible: bool
    gizmo_enabled: bool
    pan_x: float
    pan_y: float
    selection_ids: tuple[str, ...]
    cursor_x: int
    cursor_y: int

    @property
    def selection_count(self) -> int:
        return len(self.selection_ids)


def format_legacy_viewport_state(state: ViewportState) -> str:
    """Return the historical Stage-5 summary string.

    This is a compatibility surface for existing consumers. It is deliberately
    kept separate from the canonical state contract.
    """

    return f"VIEW: {state.view_mode}  |  ZOOM: {state.zoom:.2f}x"


def format_viewport_details(state: ViewportState) -> str:
    """Return the complete human-readable viewport details."""

    snap = "ON" if state.snap_enabled else "OFF"
    grid = "ON" if state.grid_visible else "OFF"
    gizmo = "ON" if state.gizmo_enabled else "OFF"
    selection = ",".join(state.selection_ids) if state.selection_ids else "NONE"
    return (
        f"{format_legacy_viewport_state(state)}  |  SNAP: {snap}  |  GRID: {grid}"
        f"  |  GIZMO: {gizmo}  |  PAN: {state.pan_x:.0f},{state.pan_y:.0f}"
        f"  |  SEL: {selection}  |  CURSOR: {state.cursor_x},{state.cursor_y}"
    )


def format_compact_viewport_details(state: ViewportState) -> str:
    """Return a compact label representation for constrained status bars."""

    compact_modes = {
        "LIT": "LIT",
        "X-RAY 1": "XR1",
        "X-RAY 2": "XR2",
        "X-RAY 3": "XR3",
        "COLLISION": "COL",
    }
    snap = "ON" if state.snap_enabled else "OFF"
    grid = "ON" if state.grid_visible else "OFF"
    gizmo = "ON" if state.gizmo_enabled else "OFF"
    mode = compact_modes.get(state.view_mode, state.view_mode)
    return (
        f"VIEW:{mode} | Z:{state.zoom:.2f}x | S:{snap} | G:{grid} | "
        f"GIZ:{gizmo} | SEL:{state.selection_count} | "
        f"CUR:{state.cursor_x},{state.cursor_y}"
    )


__all__ = [
    "ViewportState",
    "format_compact_viewport_details",
    "format_legacy_viewport_state",
    "format_viewport_details",
]
