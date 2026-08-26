"""Stage C2E adapter for Stage 9 functional UI behavior.

The Stage 9 functional UI audit mixes behavior and geometry in one report. This
adapter translates only atomic interaction results owned by B — Behavior &
Interaction. It deliberately ignores aggregate ``checks``, ``automated_status``
and top-level ``status`` values, and it excludes geometry-owned menu placement
and visual/capture evidence from the B axis.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from scripts.conformance.adapters import AdapterContext, AdapterResult
from scripts.conformance.contracts import (
    ConformanceAxis,
    ConformanceCheck,
    ConformanceStatus,
)

_SOURCE = "scripts/audit_stage9_functional_ui.py"

_TOOL_NAMES = (
    "selection",
    "rect_selection",
    "ellipse_selection",
    "lasso_tool",
    "polygonal_lasso",
    "magnetic_lasso",
    "pen_tool",
    "polygon_edit",
    "collision_brush",
)

_XRAY_MODES = {
    0: "LIT",
    1: "XRAY_1",
    2: "XRAY_2",
    3: "XRAY_3",
}

_MASK_MODES = (0, 1, 2, 3)

# These Stage 9 functional sections are explicitly classified. New sections are
# rejected until they are assigned to G, V, B, H-support, or X.
_EXPECTED_FUNCTIONAL_SECTIONS = frozenset(
    {
        "tool_palette",
        "main_xray_actions",
        "gizmo_gesture_transaction",
        "gizmo_action",
        "menus_on_screen",       # G-owned geometry; intentionally excluded.
        "inspector_scroll",
        "scenario_layer_actions",
        "mask_viewer_capture",   # Evidence producer; intentionally excluded.
        "mask_viewer_modes",
    }
)


@dataclass(frozen=True, slots=True)
class _DirectAtom:
    check_id: str
    domain: str
    summary: str


_DIRECT_ATOMS: dict[str, _DirectAtom] = {
    "gizmo_gesture_transaction": _DirectAtom(
        "B-GIZMO_STAGE9_TRANSACTION_UNDO-001",
        "gizmo",
        "Stage 9 gizmo gesture commits a real transform transaction and restores it through undo.",
    ),
    "gizmo_action": _DirectAtom(
        "B-GIZMO_STAGE9_ACTION_STATE-001",
        "gizmo",
        "Stage 9 gizmo QAction state remains consistent with viewport and semantic command context.",
    ),
    "inspector_scroll": _DirectAtom(
        "B-INTERACTION_STATE_STAGE9_INSPECTOR_SCROLL-001",
        "interaction-state",
        "Stage 9 inspector scroll areas accept and retain the requested scroll state.",
    ),
    "scenario_layer_actions": _DirectAtom(
        "B-ACTION_STAGE9_SCENARIO_LAYER-001",
        "action",
        "Stage 9 scenario add/remove actions update the authoring document through the dedicated editor.",
    ),
}


class Stage9FunctionalBehaviorAdapter:
    """Translate Stage 9 atomic functional results into canonical B checks."""

    name = "stage9-functional-behavior"

    def adapt(self, payload: Any, *, context: AdapterContext) -> AdapterResult:
        report = _require_mapping(payload, "stage9 functional payload")
        functional = _require_mapping(
            report.get("functional"), "stage9 functional payload functional"
        )

        unexpected = tuple(sorted(set(functional) - _EXPECTED_FUNCTIONAL_SECTIONS))
        if unexpected:
            raise ValueError(
                "unmapped Stage 9 functional section(s) require explicit classification: "
                f"{unexpected!r}"
            )

        checks: list[ConformanceCheck] = []
        checks.extend(_tool_checks(functional.get("tool_palette"), context=context))
        checks.extend(_xray_checks(functional.get("main_xray_actions"), context=context))
        for atom_name, atom in _DIRECT_ATOMS.items():
            checks.append(
                _direct_check(
                    atom_name,
                    atom,
                    functional.get(atom_name),
                    present=atom_name in functional,
                    context=context,
                )
            )
        checks.extend(_mask_mode_checks(functional.get("mask_viewer_modes"), context=context))

        return AdapterResult(adapter_name=self.name, checks=tuple(checks))


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _legacy_status(value: Any) -> ConformanceStatus:
    if isinstance(value, Mapping) and value.get("status") == "PASS":
        return ConformanceStatus.PASS
    return ConformanceStatus.FAIL


def _prefix(context: AdapterContext, *, atom: str) -> list[str]:
    return [
        f"source_baseline={context.source_baseline}",
        f"source_reference={context.source_reference}",
        f"legacy_atom={atom}",
    ]


def _tool_checks(raw: Any, *, context: AdapterContext) -> list[ConformanceCheck]:
    states = raw if isinstance(raw, Mapping) else {}
    unexpected = tuple(sorted(set(states) - set(_TOOL_NAMES)))
    if unexpected:
        raise ValueError(
            "unmapped Stage 9 tool palette action(s) require explicit classification: "
            f"{unexpected!r}"
        )

    checks: list[ConformanceCheck] = []
    for tool_name in _TOOL_NAMES:
        state = states.get(tool_name)
        evidence = _prefix(context, atom=f"functional.tool_palette.{tool_name}")
        if tool_name not in states:
            evidence.append("missing_atomic_state=true")
        elif isinstance(state, Mapping):
            evidence.extend(
                (
                    f"legacy_status={state.get('status')!r}",
                    f"checked={state.get('checked')!r}",
                    f"tool_object_created={state.get('tool_object_created')!r}",
                    f"button_text={state.get('button_text')!r}",
                )
            )
        else:
            evidence.append(f"invalid_atomic_state={state!r}")

        checks.append(
            ConformanceCheck(
                check_id=f"B-ACTION_STAGE9_TOOL_{tool_name.upper()}-001",
                axis=ConformanceAxis.BEHAVIOR_INTERACTION,
                domain="action",
                status=_legacy_status(state),
                source=_SOURCE,
                summary=(
                    f"Stage 9 tool action {tool_name!r} selects its button and creates "
                    "a real canvas tool."
                ),
                evidence=tuple(evidence),
            )
        )
    return checks


def _xray_checks(raw: Any, *, context: AdapterContext) -> list[ConformanceCheck]:
    states = raw if isinstance(raw, Mapping) else {}
    by_expected: dict[int, Mapping[str, Any]] = {}
    for label, state in states.items():
        if not isinstance(state, Mapping):
            raise ValueError(f"Stage 9 X-Ray state {label!r} must be an object")
        expected = state.get("expected")
        if not isinstance(expected, int) or expected not in _XRAY_MODES:
            raise ValueError(
                f"unexpected Stage 9 X-Ray expected mode for {label!r}: {expected!r}"
            )
        if expected in by_expected:
            raise ValueError(f"duplicate Stage 9 X-Ray expected mode: {expected}")
        by_expected[expected] = state

    checks: list[ConformanceCheck] = []
    for expected, token in _XRAY_MODES.items():
        state = by_expected.get(expected)
        evidence = _prefix(
            context,
            atom=f"functional.main_xray_actions.expected={expected}",
        )
        if state is None:
            evidence.append("missing_atomic_state=true")
        else:
            evidence.extend(
                (
                    f"legacy_status={state.get('status')!r}",
                    f"expected={expected}",
                    f"actual_mode={state.get('mode')!r}",
                )
            )
        checks.append(
            ConformanceCheck(
                check_id=f"B-INTERACTION_STATE_STAGE9_VIEW_{token}-001",
                axis=ConformanceAxis.BEHAVIOR_INTERACTION,
                domain="interaction-state",
                status=_legacy_status(state),
                source=_SOURCE,
                summary=(
                    f"Stage 9 view action for {token} transitions the canvas to the "
                    "expected render mode."
                ),
                evidence=tuple(evidence),
            )
        )
    return checks


def _direct_check(
    atom_name: str,
    atom: _DirectAtom,
    raw: Any,
    *,
    present: bool,
    context: AdapterContext,
) -> ConformanceCheck:
    evidence = _prefix(context, atom=f"functional.{atom_name}")
    if not present:
        evidence.append("missing_atomic_state=true")
    elif isinstance(raw, Mapping):
        evidence.append(f"legacy_status={raw.get('status')!r}")
        evidence.append(f"detail={_json(raw.get('detail'))}")
    else:
        evidence.append(f"invalid_atomic_state={raw!r}")
    return ConformanceCheck(
        check_id=atom.check_id,
        axis=ConformanceAxis.BEHAVIOR_INTERACTION,
        domain=atom.domain,
        status=_legacy_status(raw),
        source=_SOURCE,
        summary=atom.summary,
        evidence=tuple(evidence),
    )


def _mask_mode_checks(raw: Any, *, context: AdapterContext) -> list[ConformanceCheck]:
    states: dict[int, Mapping[str, Any]] = {}
    if raw is not None:
        if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
            raise ValueError("stage9 functional mask_viewer_modes must be an array")
        for state in raw:
            if not isinstance(state, Mapping):
                raise ValueError("Stage 9 mask viewer mode state must be an object")
            index = state.get("index")
            if not isinstance(index, int) or index not in _MASK_MODES:
                raise ValueError(f"unexpected Stage 9 mask viewer mode index: {index!r}")
            if index in states:
                raise ValueError(f"duplicate Stage 9 mask viewer mode index: {index}")
            states[index] = state

    checks: list[ConformanceCheck] = []
    for index in _MASK_MODES:
        state = states.get(index)
        evidence = _prefix(
            context,
            atom=f"functional.mask_viewer_modes.index={index}",
        )
        if state is None:
            evidence.append("missing_atomic_state=true")
        else:
            evidence.extend(
                (
                    f"legacy_status={state.get('status')!r}",
                    f"checked={state.get('checked')!r}",
                    f"expected_mode={index}",
                    f"actual_mode={state.get('mode')!r}",
                    f"text={state.get('text')!r}",
                )
            )
        checks.append(
            ConformanceCheck(
                check_id=f"B-INTERACTION_STATE_STAGE9_MASK_MODE_{index}-001",
                axis=ConformanceAxis.BEHAVIOR_INTERACTION,
                domain="interaction-state",
                status=_legacy_status(state),
                source=_SOURCE,
                summary=(
                    f"Stage 9 Mask Viewer mode {index} updates display state and "
                    "keeps its control checked."
                ),
                evidence=tuple(evidence),
            )
        )
    return checks
