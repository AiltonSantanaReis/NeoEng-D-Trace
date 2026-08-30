"""Stage C2C adapter for Stage 9 responsive/layout geometry evidence.

The adapter translates *atomic* geometry subchecks already emitted by
``scripts.audit_stage9_responsive_dpi`` into the canonical G axis. It does not
trust or import the legacy report's aggregate ``automated_status`` and it does
not translate visual, functional, or human-review fields.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from scripts.audit_stage9_responsive_dpi import CRITICAL_WIDGETS, DPI_CASES, RESOLUTIONS
from scripts.conformance.adapters import AdapterContext, AdapterResult
from scripts.conformance.contracts import (
    ConformanceAxis,
    ConformanceCheck,
    ConformanceStatus,
)

_SOURCE = "scripts/audit_stage9_responsive_dpi.py"
_EXPECTED_DPI = tuple(label for label, _scale in DPI_CASES)
_EXPECTED_SCALE = {label: scale for label, scale in DPI_CASES}
_EXPECTED_RESOLUTION = tuple(RESOLUTIONS)


class Stage9ResponsiveGeometryAdapter:
    """Translate Stage 9 worker geometry atoms into canonical G checks.

    Scope is deliberately narrow for C2C:

    * capture/window dimensions -> ``G / viewport``;
    * visible critical-widget geometry -> ``G / layout``.

    Tab semantics, functional actions, visual-artifact status, and human review
    remain outside this first G adapter and are not inferred from legacy
    aggregate status.
    """

    name = "stage9-responsive-geometry"

    def adapt(self, payload: Any, *, context: AdapterContext) -> AdapterResult:
        report = _require_mapping(payload, "stage9 responsive payload")
        workers = _index_workers(report.get("workers"))

        checks: list[ConformanceCheck] = []
        for dpi_label in _EXPECTED_DPI:
            worker = workers.get(dpi_label)
            for resolution in _EXPECTED_RESOLUTION:
                checks.append(
                    _dimension_check(
                        worker,
                        dpi_label=dpi_label,
                        resolution=resolution,
                        context=context,
                    )
                )

                for widget in CRITICAL_WIDGETS:
                    checks.append(
                        _widget_check(
                            worker,
                            dpi_label=dpi_label,
                            resolution=resolution,
                            widget=widget,
                            context=context,
                        )
                    )

        return AdapterResult(adapter_name=self.name, checks=tuple(checks))


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _index_workers(raw_workers: Any) -> dict[str, Mapping[str, Any]]:
    if not isinstance(raw_workers, list):
        raise ValueError("stage9 responsive payload workers must be an array")

    indexed: dict[str, Mapping[str, Any]] = {}
    for index, raw_worker in enumerate(raw_workers):
        worker = _require_mapping(raw_worker, f"workers[{index}]")
        dpi = _require_mapping(worker.get("dpi"), f"workers[{index}].dpi")
        label = dpi.get("label")
        if not isinstance(label, str) or not label:
            raise ValueError(f"workers[{index}].dpi.label must be a non-empty string")
        if label not in _EXPECTED_DPI:
            raise ValueError(f"unexpected Stage 9 DPI worker label: {label!r}")
        if label in indexed:
            raise ValueError(f"duplicate Stage 9 DPI worker label: {label!r}")
        indexed[label] = worker
    return indexed



def _token(value: str) -> str:
    return value.upper().replace("-", "_")


def _dimension_check_id(dpi_label: str, resolution: str) -> str:
    return f"G-VIEWPORT_DPI{_token(dpi_label)}_{_token(resolution)}-001"


def _widget_check_id(dpi_label: str, resolution: str, widget: str) -> str:
    return (
        f"G-LAYOUT_DPI{_token(dpi_label)}_{_token(resolution)}_"
        f"{_token(widget)}-001"
    )

def _atomic_status(value: Any) -> ConformanceStatus:
    return (
        ConformanceStatus.PASS
        if value == "PASS"
        else ConformanceStatus.FAIL
    )


def _evidence_prefix(
    context: AdapterContext,
    *,
    dpi_label: str,
    resolution: str,
    atom: str,
) -> tuple[str, ...]:
    return (
        f"source_baseline={context.source_baseline}",
        f"source_reference={context.source_reference}",
        f"dpi={dpi_label}",
        f"resolution={resolution}",
        f"legacy_atom={atom}",
    )


def _dimension_check(
    worker: Mapping[str, Any] | None,
    *,
    dpi_label: str,
    resolution: str,
    context: AdapterContext,
) -> ConformanceCheck:
    atom = f"workers[{dpi_label}].capture_dimensions.states.{resolution}"
    evidence = list(
        _evidence_prefix(
            context,
            dpi_label=dpi_label,
            resolution=resolution,
            atom=atom,
        )
    )

    raw_state: Any = None
    if worker is not None:
        capture_dimensions = worker.get("capture_dimensions")
        if isinstance(capture_dimensions, Mapping):
            states = capture_dimensions.get("states")
            if isinstance(states, Mapping):
                raw_state = states.get(resolution)

    if isinstance(raw_state, Mapping):
        status = _atomic_status(raw_state.get("status"))
        for key in (
            "requested_logical",
            "expected_physical",
            "actual_window_size",
            "actual_capture_size",
        ):
            evidence.append(f"{key}={raw_state.get(key)!r}")
    else:
        status = ConformanceStatus.FAIL
        evidence.append("missing_atomic_state=true")
        width, height = RESOLUTIONS[resolution]
        scale = _EXPECTED_SCALE[dpi_label]
        evidence.extend(
            (
                f"expected_logical={[width, height]!r}",
                f"expected_physical={[round(width * scale), round(height * scale)]!r}",
            )
        )

    return ConformanceCheck(
        check_id=_dimension_check_id(dpi_label, resolution),
        axis=ConformanceAxis.GEOMETRY_PHYSICS,
        domain="viewport",
        status=status,
        source=_SOURCE,
        summary=(
            f"Stage 9 DPI {dpi_label} / {resolution} capture/window "
            "dimension contract."
        ),
        evidence=tuple(evidence),
    )


def _widget_check(
    worker: Mapping[str, Any] | None,
    *,
    dpi_label: str,
    resolution: str,
    widget: str,
    context: AdapterContext,
) -> ConformanceCheck:
    atom = f"workers[{dpi_label}].critical_widgets.states.{resolution}.{widget}"
    evidence = list(
        _evidence_prefix(
            context,
            dpi_label=dpi_label,
            resolution=resolution,
            atom=atom,
        )
    )

    raw_state: Any = None
    if worker is not None:
        critical_widgets = worker.get("critical_widgets")
        if isinstance(critical_widgets, Mapping):
            states = critical_widgets.get("states")
            if isinstance(states, Mapping):
                resolution_state = states.get(resolution)
                if isinstance(resolution_state, Mapping):
                    raw_state = resolution_state.get(widget)

    if isinstance(raw_state, Mapping):
        status = _atomic_status(raw_state.get("status"))
        snapshot = raw_state.get("snapshot")
        if isinstance(snapshot, Mapping):
            evidence.extend(
                (
                    f"visible={snapshot.get('visible')!r}",
                    f"geometry={snapshot.get('geometry')!r}",
                    f"frame_geometry={snapshot.get('frame_geometry')!r}",
                    f"root_geometry={snapshot.get('root_geometry')!r}",
                )
            )
        else:
            evidence.append(f"snapshot={snapshot!r}")
    else:
        status = ConformanceStatus.FAIL
        evidence.append("missing_atomic_state=true")

    return ConformanceCheck(
        check_id=_widget_check_id(dpi_label, resolution, widget),
        axis=ConformanceAxis.GEOMETRY_PHYSICS,
        domain="layout",
        status=status,
        source=_SOURCE,
        summary=(
            f"Stage 9 DPI {dpi_label} / {resolution} critical widget {widget!r} "
            "visibility/geometry contract."
        ),
        evidence=tuple(evidence),
    )
