"""Canonical contracts for NeoEng's multiaxis conformance tooling.

Only Geometry/Physics (G), Visual System (V), and Behavior/Interaction (B)
are blocking product axes. Historical compatibility remains supporting evidence
and is deliberately not represented as a fourth axis here.
"""

from scripts.conformance.adapters import (
    AdaptedConformance,
    AdapterContext,
    AdapterResult,
    ConformanceAdapter,
    combine_adapter_results,
    run_adapter,
)
from scripts.conformance.contracts import (
    AXIS_DOMAINS,
    AXIS_ORDER,
    AxisResult,
    ConformanceAxis,
    ConformanceCheck,
    ConformanceStatus,
    MultiAxisConformance,
    aggregate_status,
)
from scripts.conformance.stage1_visual_adapter import Stage1VisualSystemAdapter
from scripts.conformance.stage9_geometry_adapter import Stage9ResponsiveGeometryAdapter
from scripts.conformance.evidence import (
    EVIDENCE_KIND,
    EVIDENCE_SCHEMA_VERSION,
    HistoricalEvidence,
    build_evidence_document,
    read_evidence_json,
    validate_evidence_document,
    write_evidence_json,
)

__all__ = [
    "AdaptedConformance",
    "AdapterContext",
    "AdapterResult",
    "ConformanceAdapter",
    "AXIS_DOMAINS",
    "AXIS_ORDER",
    "AxisResult",
    "ConformanceAxis",
    "ConformanceCheck",
    "ConformanceStatus",
    "Stage1VisualSystemAdapter",
    "Stage9ResponsiveGeometryAdapter",
    "MultiAxisConformance",
    "aggregate_status",
    "combine_adapter_results",
    "run_adapter",
    "EVIDENCE_KIND",
    "EVIDENCE_SCHEMA_VERSION",
    "HistoricalEvidence",
    "build_evidence_document",
    "read_evidence_json",
    "validate_evidence_document",
    "write_evidence_json",
]
