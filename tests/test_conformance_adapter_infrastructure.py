"""Stage C2B tests for the generic conformance adapter boundary."""

from __future__ import annotations

import pytest

from scripts.conformance import (
    AdaptedConformance,
    AdapterContext,
    AdapterResult,
    ConformanceAxis,
    ConformanceCheck,
    ConformanceStatus,
    HistoricalEvidence,
    combine_adapter_results,
    run_adapter,
)


def _check(
    check_id: str,
    axis: ConformanceAxis,
    domain: str,
    status: ConformanceStatus = ConformanceStatus.PASS,
    *,
    source: str = "tests/fake-auditor",
) -> ConformanceCheck:
    return ConformanceCheck(
        check_id=check_id,
        axis=axis,
        domain=domain,
        status=status,
        source=source,
        summary=f"fixture {check_id}",
        evidence=("fixture-evidence",),
    )


class _FakeAdapter:
    name = "fixture-auditor"

    def adapt(self, payload, *, context: AdapterContext) -> AdapterResult:
        assert payload == {"ok": True}
        assert context.source_reference == "artifacts/fixture/report.json"
        return AdapterResult(
            adapter_name=self.name,
            checks=(
                _check(
                    "G-LAYOUT-001",
                    ConformanceAxis.GEOMETRY_PHYSICS,
                    "layout",
                ),
            ),
            historical_evidence=(
                HistoricalEvidence(
                    source="fixture-history",
                    reference="schema-3",
                    summary="Historical context remains non-blocking.",
                ),
            ),
        )


def test_adapter_context_requires_provenance() -> None:
    with pytest.raises(ValueError, match="source_baseline"):
        AdapterContext(source_baseline="", source_reference="report.json")
    with pytest.raises(ValueError, match="source_reference"):
        AdapterContext(source_baseline="39002f1", source_reference=" ")


def test_adapter_result_requires_stable_slug_and_unique_ids() -> None:
    check = _check(
        "V-TOKEN-001",
        ConformanceAxis.VISUAL_SYSTEM,
        "token",
    )
    with pytest.raises(ValueError, match="adapter_name"):
        AdapterResult(adapter_name="Bad Adapter", checks=(check,))
    with pytest.raises(ValueError, match="duplicate check IDs"):
        AdapterResult(adapter_name="fixture", checks=(check, check))


def test_run_adapter_preserves_atomic_checks_and_history() -> None:
    context = AdapterContext(
        source_baseline="39002f1",
        source_reference="artifacts/fixture/report.json",
    )
    result = run_adapter(_FakeAdapter(), {"ok": True}, context=context)
    assert result.adapter_name == "fixture-auditor"
    assert tuple(check.check_id for check in result.checks) == ("G-LAYOUT-001",)
    assert len(result.historical_evidence) == 1


def test_run_adapter_rejects_invalid_result_type() -> None:
    class BadAdapter:
        name = "bad-adapter"

        def adapt(self, payload, *, context):
            return {"status": "PASS"}

    context = AdapterContext("39002f1", "fixture.json")
    with pytest.raises(TypeError, match="must return AdapterResult"):
        run_adapter(BadAdapter(), {}, context=context)


def test_run_adapter_rejects_identity_mismatch() -> None:
    class MismatchAdapter:
        name = "declared-adapter"

        def adapt(self, payload, *, context):
            return AdapterResult(adapter_name="other-adapter")

    context = AdapterContext("39002f1", "fixture.json")
    with pytest.raises(ValueError, match="identity mismatch"):
        run_adapter(MismatchAdapter(), {}, context=context)


def test_combine_adapter_results_is_deterministic() -> None:
    first = AdapterResult(
        adapter_name="z-adapter",
        checks=(
            _check(
                "V-PALETTE-002",
                ConformanceAxis.VISUAL_SYSTEM,
                "palette",
            ),
        ),
        historical_evidence=(
            HistoricalEvidence("z-history", "ref-z", "Z context"),
        ),
    )
    second = AdapterResult(
        adapter_name="a-adapter",
        checks=(
            _check(
                "B-ACTION-001",
                ConformanceAxis.BEHAVIOR_INTERACTION,
                "action",
            ),
            _check(
                "G-LAYOUT-001",
                ConformanceAxis.GEOMETRY_PHYSICS,
                "layout",
            ),
        ),
        historical_evidence=(
            HistoricalEvidence("a-history", "ref-a", "A context"),
        ),
    )

    combined = combine_adapter_results(
        (first, second),
        source_baseline="39002f1",
    )
    assert isinstance(combined, AdaptedConformance)
    assert combined.adapter_names == ("a-adapter", "z-adapter")
    assert tuple(check.check_id for check in combined.report.checks) == (
        "B-ACTION-001",
        "G-LAYOUT-001",
        "V-PALETTE-002",
    )
    assert tuple(item.source for item in combined.historical_evidence) == (
        "a-history",
        "z-history",
    )


def test_combine_adapter_results_rejects_cross_adapter_duplicate_check_ids() -> None:
    duplicate = _check(
        "B-COMMAND-001",
        ConformanceAxis.BEHAVIOR_INTERACTION,
        "command",
    )
    left = AdapterResult(adapter_name="left", checks=(duplicate,))
    right = AdapterResult(adapter_name="right", checks=(duplicate,))
    with pytest.raises(ValueError, match="duplicate conformance check ID"):
        combine_adapter_results((left, right), source_baseline="39002f1")


def test_adapter_bundle_serializes_via_canonical_c2a_schema() -> None:
    result = AdapterResult(
        adapter_name="fixture",
        checks=(
            _check(
                "G-LAYOUT-001",
                ConformanceAxis.GEOMETRY_PHYSICS,
                "layout",
            ),
            _check(
                "V-CONTRAST-001",
                ConformanceAxis.VISUAL_SYSTEM,
                "contrast",
                ConformanceStatus.APPROVED_BASELINE_CHANGE,
            ),
            _check(
                "B-ACTION-001",
                ConformanceAxis.BEHAVIOR_INTERACTION,
                "action",
            ),
        ),
        historical_evidence=(
            HistoricalEvidence(
                source="legacy-schema-reader",
                reference="schema-3",
                summary="Historical reader evidence only.",
            ),
        ),
    )
    combined = combine_adapter_results((result,), source_baseline="39002f1")
    document = combined.build_evidence_document(producer="tests/c2b")

    assert document["status"] == "APPROVED_BASELINE_CHANGE"
    assert tuple(document["axes"]) == ("G", "V", "B")
    assert document["historical_evidence"] == [
        {
            "source": "legacy-schema-reader",
            "reference": "schema-3",
            "summary": "Historical reader evidence only.",
        }
    ]
    assert "H" not in document["axes"]
