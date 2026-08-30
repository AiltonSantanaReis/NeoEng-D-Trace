"""Stage C2D adapter for the Stage 1 visual-system contract.

The Stage 1 contract audit is already scoped to application-chrome tokens,
palette, contrast, and QSS visual states. This adapter translates its *atomic*
``checks`` booleans into canonical V-axis checks. It deliberately ignores the
legacy report's aggregate ``current_contract_result`` and
``consolidated_decision`` fields, and keeps historical-comparator context
outside the blocking G/V/B axes.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from scripts.conformance.adapters import AdapterContext, AdapterResult
from scripts.conformance.contracts import (
    ConformanceAxis,
    ConformanceCheck,
    ConformanceStatus,
)
from scripts.conformance.evidence import HistoricalEvidence

_SOURCE = "scripts/audit_stage1_contract.py"


@dataclass(frozen=True, slots=True)
class _VisualAtom:
    check_id: str
    domain: str
    summary: str


_VISUAL_ATOMS: dict[str, _VisualAtom] = {
    "required_token_schema": _VisualAtom(
        "V-TOKEN_STAGE1_REQUIRED_SCHEMA-001",
        "token",
        "Stage 1 required visual-token schema matches the canonical chrome roles.",
    ),
    "hex_colors_valid": _VisualAtom(
        "V-TOKEN_STAGE1_HEX_COLORS_VALID-001",
        "token",
        "Stage 1 theme token colors use valid six-digit hexadecimal values.",
    ),
    "token_colors_unique": _VisualAtom(
        "V-PALETTE_STAGE1_TOKEN_COLORS_UNIQUE-001",
        "palette",
        "Stage 1 theme palette does not alias distinct token roles to duplicate colors.",
    ),
    "primary_text_contrast": _VisualAtom(
        "V-CONTRAST_STAGE1_PRIMARY_TEXT-001",
        "contrast",
        "Stage 1 primary text contrast meets the legacy WCAG-oriented threshold.",
    ),
    "secondary_text_contrast": _VisualAtom(
        "V-CONTRAST_STAGE1_SECONDARY_TEXT-001",
        "contrast",
        "Stage 1 secondary text contrast meets the legacy WCAG-oriented threshold.",
    ),
    "focus_contrast": _VisualAtom(
        "V-CONTRAST_STAGE1_FOCUS-001",
        "contrast",
        "Stage 1 focus indicator contrast meets the legacy non-text threshold.",
    ),
    "qss_is_generated_from_tokens": _VisualAtom(
        "V-TOKEN_STAGE1_QSS_FROM_TOKENS-001",
        "token",
        "Stage 1 application QSS is generated from the canonical theme tokens.",
    ),
    "qss_required_states": _VisualAtom(
        "V-VISUAL_STATE_STAGE1_QSS_REQUIRED_STATES-001",
        "visual-state",
        "Stage 1 QSS contains every required visual interaction state selector.",
    ),
    "qss_required_roles": _VisualAtom(
        "V-VISUAL_STATE_STAGE1_QSS_REQUIRED_ROLES-001",
        "visual-state",
        "Stage 1 QSS contains the required application-chrome role selectors.",
    ),
    "forbidden_colors_absent": _VisualAtom(
        "V-PALETTE_STAGE1_FORBIDDEN_COLORS_ABSENT-001",
        "palette",
        "Stage 1 application QSS excludes the retired forbidden palette colors.",
    ),
    "no_inline_application_styles": _VisualAtom(
        "V-TOKEN_STAGE1_NO_INLINE_STYLES-001",
        "token",
        "Stage 1 application chrome does not bypass the theme system with inline styles.",
    ),
    "no_unclassified_direct_chrome_colors": _VisualAtom(
        "V-PALETTE_STAGE1_NO_UNCLASSIFIED_CHROME_COLORS-001",
        "palette",
        "Stage 1 application chrome contains no unclassified direct color literals.",
    ),
}

_EXPECTED_ATOMS = tuple(_VISUAL_ATOMS)


class Stage1VisualSystemAdapter:
    """Translate Stage 1 atomic visual-contract checks into canonical V checks."""

    name = "stage1-visual-system"

    def adapt(self, payload: Any, *, context: AdapterContext) -> AdapterResult:
        report = _require_mapping(payload, "stage1 visual payload")
        raw_checks = _require_mapping(report.get("checks"), "stage1 visual payload checks")

        unexpected = tuple(sorted(set(raw_checks) - set(_EXPECTED_ATOMS)))
        if unexpected:
            raise ValueError(
                "unmapped Stage 1 visual check(s) require explicit classification: "
                f"{unexpected!r}"
            )

        evidence = report.get("evidence")
        evidence_map = evidence if isinstance(evidence, Mapping) else {}

        checks = tuple(
            _adapt_atom(
                atom_name,
                raw_checks,
                evidence_map,
                context=context,
            )
            for atom_name in _EXPECTED_ATOMS
        )

        historical = _historical_evidence(report.get("historical_result"), context=context)
        return AdapterResult(
            adapter_name=self.name,
            checks=checks,
            historical_evidence=historical,
        )


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _status(raw_checks: Mapping[str, Any], atom_name: str) -> ConformanceStatus:
    if atom_name not in raw_checks:
        return ConformanceStatus.FAIL
    return (
        ConformanceStatus.PASS
        if raw_checks.get(atom_name) is True
        else ConformanceStatus.FAIL
    )


def _evidence_prefix(
    context: AdapterContext,
    *,
    atom_name: str,
) -> list[str]:
    return [
        f"source_baseline={context.source_baseline}",
        f"source_reference={context.source_reference}",
        f"legacy_atom=checks.{atom_name}",
    ]


def _atom_evidence(
    atom_name: str,
    evidence: Mapping[str, Any],
) -> tuple[str, ...]:
    if atom_name == "required_token_schema":
        return (f"token_schema={_json(evidence.get('token_schema'))}",)
    if atom_name in {"hex_colors_valid", "token_colors_unique"}:
        return (f"token_values={_json(evidence.get('token_values'))}",)
    if atom_name == "primary_text_contrast":
        ratios = evidence.get("contrast_ratios")
        ratio = ratios.get("primary_on_window") if isinstance(ratios, Mapping) else None
        return (f"primary_on_window={ratio!r}", "threshold=>=4.5")
    if atom_name == "secondary_text_contrast":
        ratios = evidence.get("contrast_ratios")
        ratio = ratios.get("secondary_on_surface") if isinstance(ratios, Mapping) else None
        return (f"secondary_on_surface={ratio!r}", "threshold=>=4.5")
    if atom_name == "focus_contrast":
        ratios = evidence.get("contrast_ratios")
        ratio = ratios.get("focus_on_window") if isinstance(ratios, Mapping) else None
        return (f"focus_on_window={ratio!r}", "threshold=>=3.0")
    if atom_name == "qss_is_generated_from_tokens":
        return (f"qss_sha256={evidence.get('qss_sha256')!r}",)
    if atom_name == "qss_required_states":
        return (f"qss_states={_json(evidence.get('qss_states'))}",)
    if atom_name == "qss_required_roles":
        return ("required_role=QPushButton[uiRole=\"tool\"]",)
    if atom_name == "forbidden_colors_absent":
        return (f"forbidden_colors={_json(evidence.get('forbidden_colors'))}",)
    if atom_name == "no_inline_application_styles":
        return (f"inline_style_files={_json(evidence.get('inline_style_files'))}",)
    if atom_name == "no_unclassified_direct_chrome_colors":
        inventory = evidence.get("direct_color_inventory")
        if isinstance(inventory, Mapping):
            chrome = inventory.get("application_chrome_review_entries")
            return (
                f"application_chrome_review_entries={_json(chrome)}",
                f"inventory_pass={inventory.get('pass')!r}",
            )
        return ("direct_color_inventory=null",)
    return ()


def _adapt_atom(
    atom_name: str,
    raw_checks: Mapping[str, Any],
    evidence: Mapping[str, Any],
    *,
    context: AdapterContext,
) -> ConformanceCheck:
    specification = _VISUAL_ATOMS[atom_name]
    atom_evidence = _evidence_prefix(context, atom_name=atom_name)
    if atom_name not in raw_checks:
        atom_evidence.append("missing_atomic_check=true")
    else:
        atom_evidence.append(f"legacy_value={raw_checks.get(atom_name)!r}")
    atom_evidence.extend(_atom_evidence(atom_name, evidence))

    return ConformanceCheck(
        check_id=specification.check_id,
        axis=ConformanceAxis.VISUAL_SYSTEM,
        domain=specification.domain,
        status=_status(raw_checks, atom_name),
        source=_SOURCE,
        summary=specification.summary,
        evidence=tuple(atom_evidence),
    )


def _historical_evidence(
    raw_historical: Any,
    *,
    context: AdapterContext,
) -> tuple[HistoricalEvidence, ...]:
    if not isinstance(raw_historical, Mapping):
        return ()

    status = raw_historical.get("status", "UNKNOWN")
    classification = raw_historical.get("classification", "UNCLASSIFIED")
    finding_count = raw_historical.get("finding_count")
    unexpected_geometry_delta_count = raw_historical.get(
        "unexpected_geometry_delta_count"
    )
    interpretation = raw_historical.get("interpretation")
    historical_source = raw_historical.get("source")
    reference = (
        str(historical_source)
        if isinstance(historical_source, str) and historical_source.strip()
        else f"{context.source_reference}#historical_result"
    )

    summary = (
        f"Stage 1 historical comparator context: status={status!r}; "
        f"classification={classification!r}; finding_count={finding_count!r}; "
        "unexpected_geometry_delta_count="
        f"{unexpected_geometry_delta_count!r}"
    )
    if isinstance(interpretation, str) and interpretation.strip():
        summary += f"; interpretation={interpretation.strip()}"

    return (
        HistoricalEvidence(
            source=_SOURCE,
            reference=reference,
            summary=summary,
        ),
    )
