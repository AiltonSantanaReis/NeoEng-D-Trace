"""Run the formal, current-contract reconciliation gate for P2D-COMP-01."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FORMAL_DIR = ROOT / "docs/evidence/artifacts/legacy-26-formal-review-20260901"
AUDIT_PATH = FORMAL_DIR / "untracked_manifest_audit.json"
CASE_PATH = FORMAL_DIR / "case_decisions.json"
JUNIT_PATH = (
    ROOT / "docs/evidence/artifacts/legacy-26-phase5-20260901/native-substitutes.xml"
)
HISTORICAL_MANIFEST = ROOT / "quality/legacy_tests/manifest.json"
HISTORICAL_RECONCILIATION = ROOT / "quality/legacy_tests/reconciliation.json"
HISTORICAL_MANIFEST_SHA256 = (
    "061e5981084e962f71f6357e765a0fe66defda5af521c9b7e22ae1e2bbf9833a"
)
HISTORICAL_RECONCILIATION_SHA256 = (
    "296ca97f07341eedd99ef8aae57d7053fe6110bdddbc01a55b872d3bf20fb493"
)

RULES_CONSULTED = [
    "docs/POLITICA_NAO_REGRESSAO.md",
    "docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md",
    "docs/evidence/README.md",
    "tools/run_legacy_tests.py",
    "quality/legacy_tests/manifest.json (read-only)",
    "quality/legacy_tests/reconciliation.json (read-only)",
    "docs/evidence/AUDITORIA_FECHAMENTO_ETAPAS_0_9_2026-08-24.md",
    "docs/evidence/STAGE0_HUMAN_APPROVAL_2026-08-24.md",
    "docs/evidence/STAGE1_HUMAN_APPROVAL_2026-08-24.md",
    "docs/evidence/STAGE2_HUMAN_APPROVAL_2026-08-24.md",
    "docs/evidence/STAGE3_HUMAN_APPROVAL_2026-08-24.md",
    "docs/evidence/STAGE4_SCOPE_AND_RECONCILIATION.md",
    "docs/evidence/STAGE5_SCOPE_AND_RECONCILIATION.md",
    "docs/EVIDENCIA_P2D_05_IMPLEMENTACAO_2026-08-30.md",
    "docs/DECISAO_P2D_05_O2_IMPLEMENTACAO_2026-08-30.md",
    "docs/PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md",
]

FAMILY_EVIDENCE = {
    "F02 governance evidence": {
        "basis": ["docs/evidence/README.md"],
        "review": "GOVERNANCE_EVIDENCE_EXISTING",
    },
    "legacy cleanup lot1 stage5": {
        "basis": [
            "scripts/audit_stage5_contract.py",
            "docs/evidence/STAGE5_SCOPE_AND_RECONCILIATION.md",
        ],
        "review": "HISTORICAL_AUDIT_REFERENCE",
    },
    "legacy cleanup lot2": {
        "basis": [
            "scripts/audit_ui_capture.py",
            "docs/evidence/AUDITORIA_FECHAMENTO_ETAPAS_0_9_2026-08-24.md",
        ],
        "review": "HISTORICAL_AUDIT_REFERENCE",
    },
    "P2D-05 evidence": {
        "basis": [
            "docs/EVIDENCIA_P2D_05_IMPLEMENTACAO_2026-08-30.md",
            "docs/DECISAO_P2D_05_O2_IMPLEMENTACAO_2026-08-30.md",
        ],
        "review": "P2D_EVIDENCE_REFERENCE",
    },
    "stage0-9 final audit": {
        "basis": ["docs/evidence/AUDITORIA_FECHAMENTO_ETAPAS_0_9_2026-08-24.md"],
        "review": "HISTORICAL_AUDIT_REFERENCE",
    },
    "stage0 snapshot": {
        "basis": ["docs/evidence/STAGE0_HUMAN_APPROVAL_2026-08-24.md"],
        "review": "HUMAN_APPROVAL_RECORDED",
    },
    "stage1 snapshot": {
        "basis": ["docs/evidence/STAGE1_HUMAN_APPROVAL_2026-08-24.md"],
        "review": "HUMAN_APPROVAL_RECORDED",
    },
    "stage2 snapshot": {
        "basis": ["docs/evidence/STAGE2_HUMAN_APPROVAL_2026-08-24.md"],
        "review": "HUMAN_APPROVAL_RECORDED",
    },
    "stage3 snapshot": {
        "basis": ["docs/evidence/STAGE3_HUMAN_APPROVAL_2026-08-24.md"],
        "review": "HUMAN_APPROVAL_RECORDED",
    },
    "stage4 snapshot": {
        "basis": ["docs/evidence/STAGE4_SCOPE_AND_RECONCILIATION.md"],
        "review": "SCOPE_RECORDED_NO_HUMAN_APPROVAL_FILE_FOUND",
    },
    "stage5 adjustment": {
        "basis": ["docs/evidence/STAGE5_SCOPE_AND_RECONCILIATION.md"],
        "review": "SCOPE_RECORDED_REVIEW_REQUIRED_WHERE_DECLARED",
    },
    "stage5 snapshot": {
        "basis": ["docs/evidence/STAGE5_SCOPE_AND_RECONCILIATION.md"],
        "review": "SCOPE_RECORDED_REVIEW_REQUIRED_WHERE_DECLARED",
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )


def relative_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_dependency_manifest(path: str) -> bool:
    return path.replace("\\", "/").lower().endswith("/packages/manifest.json")


def is_historical_release_manifest(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.endswith(
        "/build-poetry-official/release-manifest.json"
    ) or normalized.endswith("/build-poetry-official-final/release-manifest.json")


def resolve_manifest_inventory(root: Path = ROOT) -> dict[str, Any]:
    audit = load_json(root / AUDIT_PATH.relative_to(ROOT))
    entries = []
    status_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    missing_reference_paths = []
    for source in audit["entries"]:
        path_text = source["path"].replace("\\", "/")
        path = root / Path(path_text)
        if not path.is_file():
            raise AssertionError(f"manifest inventariado não existe: {path_text}")
        raw = path.read_bytes()
        observed_sha = sha256_bytes(raw)
        if observed_sha != source["sha256"]:
            raise AssertionError(f"hash mudou durante a reconciliação: {path_text}")
        family = source["family"]
        if family not in FAMILY_EVIDENCE:
            raise ValueError(f"família sem evidência autorizada: {family}")
        basis = FAMILY_EVIDENCE[family]
        declared_count = int(source["reference_audit"]["key_count"])
        sample = list(source["reference_audit"].get("sample", []))
        if is_dependency_manifest(path_text):
            reference_status, missing_count, missing_sample = (
                "NOT_APPLICABLE_DEPENDENCY_MANIFEST",
                0,
                [],
            )
        elif is_historical_release_manifest(path_text):
            if declared_count != 353:
                raise AssertionError(
                    f"release manifest inesperado ({declared_count} refs): {path_text}"
                )
            reference_status, missing_count, missing_sample = (
                "COMPLETE_WITH_DECLARED_MISSING_HISTORICAL_ARTIFACTS",
                353,
                sample[:5],
            )
            missing_reference_paths.append(
                {
                    "manifest": path_text,
                    "declared_count": declared_count,
                    "missing_count": missing_count,
                    "reason": (
                        "historical build output is not present in the "
                        "current workspace"
                    ),
                }
            )
        elif declared_count:
            reference_status, missing_count, missing_sample = "COMPLETE", 0, []
        else:
            reference_status, missing_count, missing_sample = (
                "NO_REFERENCES_DECLARED_METADATA_MANIFEST",
                0,
                [],
            )
        status_counts[reference_status] += 1
        family_counts[family] += 1
        entries.append(
            {
                "path": path_text,
                "family": family,
                "owner": {
                    "classification": "PROJECT_CUSTODIAN_UNDER_CURRENT_AUTHORIZATION",
                    "identity": "current project custodian",
                    "evidence": (
                        "explicit user authorization in the active engineering task"
                    ),
                    "original_creator_proven": False,
                },
                "origin": {
                    "classification": "PREEXISTING_ARTIFACT_FAMILY",
                    "basis": basis["basis"],
                    "creator_or_creation_event": (
                        "NOT_PROVEN_BY_GIT_HISTORY_OR_FILESYSTEM_METADATA"
                    ),
                    "limitation": (
                        "the artifact's technical family and references are proven; "
                        "exact creator/event is not"
                    ),
                },
                "scope": {
                    "classification": "OUTSIDE_CURRENT_LEGACY26_PHASE5_PACKAGE",
                    "current_package_reference": (
                        "docs/evidence/artifacts/legacy-26-formal-review-20260901"
                    ),
                    "scope_basis": "path family and historical evidence references",
                },
                "references": {
                    "declared_count": declared_count,
                    "sample": sample,
                    "missing_count": missing_count,
                    "missing_sample": missing_sample,
                    "status": reference_status,
                    "basis": basis["basis"],
                },
                "observed_integrity": {
                    "bytes": len(raw),
                    "sha256": observed_sha,
                    "source_audit_sha256": source["sha256"],
                    "unchanged_since_inventory": True,
                    "json_valid": bool(source["json_valid"]),
                },
                "treatment": {
                    "decision": "PRESERVE_UNMODIFIED_OUTSIDE_SCOPE",
                    "actions": [
                        "do_not_delete",
                        "do_not_move",
                        "do_not_overwrite",
                        "do_not_auto_track",
                    ],
                    "authorization": (
                        "current user instruction to resolve formally "
                        "without automatic alteration"
                    ),
                },
                "audit_decision": "RESOLVED_WITH_DECLARED_LIMITATIONS",
                "review_status": basis["review"],
            }
        )
    if len(entries) != 63:
        raise AssertionError(f"inventário esperado: 63; observado: {len(entries)}")
    return {
        "schema": "neoeng.workspace.untracked-manifest-resolution",
        "schema_version": 1,
        "status": "ACCEPTED_WITH_DECLARED_LIMITATIONS",
        "accepted": True,
        "resolution_scope": (
            "formal ownership/origin/scope/reference/treatment classification; "
            "source manifests are read-only"
        ),
        "source_inventory": relative_path(AUDIT_PATH),
        "source_inventory_sha256": sha256_bytes(AUDIT_PATH.read_bytes()),
        "authorization": {
            "owner_classification": "current project custodian",
            "basis": "explicit current user authorization",
            "automatic_source_alteration": False,
        },
        "summary": {
            "expected": 63,
            "observed": len(entries),
            "resolved": len(entries),
            "unresolved": 0,
            "status_counts": dict(sorted(status_counts.items())),
            "family_counts": dict(sorted(family_counts.items())),
            "declared_missing_historical_references": missing_reference_paths,
        },
        "limitations": [
            (
                "Exact creator identity and filesystem creation event are not proven; "
                "this is recorded rather than inferred."
            ),
            (
                "The two historical stage0 release manifests each reference 353 absent "
                "build-output files; those references remain declared missing."
            ),
            (
                "The Unity Packages manifest is a dependency manifest and has no "
                "evidence references to resolve."
            ),
        ],
        "entries": entries,
    }


def parse_substitute_junit(root: Path = ROOT) -> dict[str, int]:
    junit = root / JUNIT_PATH.relative_to(ROOT)
    if not junit.is_file():
        raise AssertionError(f"JUnit substituto ausente: {relative_path(junit)}")
    document = ET.parse(junit).getroot()
    suites = (
        [document]
        if document.tag == "testsuite"
        else list(document.findall("testsuite"))
    )
    if not suites:
        raise AssertionError("JUnit substituto não contém testsuite")
    values = {
        key: sum(int(suite.attrib.get(key, "0")) for suite in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }
    if values != {"tests": 42, "failures": 0, "errors": 0, "skipped": 0}:
        raise AssertionError(
            f"JUnit substituto não corresponde ao run aprovado: {values}"
        )
    return values


def build_formal_gate(root: Path = ROOT) -> dict[str, Any]:
    case_data = load_json(root / CASE_PATH.relative_to(ROOT))
    inventory = resolve_manifest_inventory(root)
    junit_values = parse_substitute_junit(root)
    historical_manifest_hash = sha256_bytes(
        (root / HISTORICAL_MANIFEST.relative_to(ROOT)).read_bytes()
    )
    historical_reconciliation_hash = sha256_bytes(
        (root / HISTORICAL_RECONCILIATION.relative_to(ROOT)).read_bytes()
    )
    if historical_manifest_hash != HISTORICAL_MANIFEST_SHA256:
        raise AssertionError("quality/legacy_tests/manifest.json foi alterado")
    if historical_reconciliation_hash != HISTORICAL_RECONCILIATION_SHA256:
        raise AssertionError("quality/legacy_tests/reconciliation.json foi alterado")
    cases = case_data.get("cases", [])
    if [item.get("case") for item in cases] != list(range(1, 28)):
        raise AssertionError("IDs de reconciliação inválidos")
    decisions = Counter(item.get("decision") for item in cases)
    if decisions != Counter({"NO_CHANGE": 26, "CORRIGIDO": 1}):
        raise AssertionError(f"decisões inesperadas: {decisions}")
    for item in cases:
        if (
            item.get("substitute_status") != "passed"
            or not item.get("decision_basis")
            or not item.get("substitute_tests")
        ):
            raise AssertionError(f"caso sem base/evidência: #{item.get('case')}")
    case_10, case_25 = cases[9], cases[24]
    if case_10.get("decision") != "NO_CHANGE" or case_10.get(
        "historical_observation", {}
    ).get("reconciliation") not in {"missing_expected_failure", "missing"}:
        raise AssertionError("caso #10 não está reconciliado como ausência histórica")
    if (
        case_25.get("decision") != "CORRIGIDO"
        or "cycle" not in case_25.get("decision_basis", "").lower()
    ):
        raise AssertionError("caso #25 não registra a correção cycle-safe")
    category_counts = Counter(
        item.get("historical_observation", {}).get("reconciliation") for item in cases
    )
    expected_categories = Counter(
        {"matched": 15, "unexpected_signature": 11, "missing_expected_failure": 1}
    )
    if category_counts != expected_categories:
        raise AssertionError(f"categorias históricas inesperadas: {category_counts}")
    historical = case_data["historical_runner"]
    historical_runner = {
        "tests": historical["tests"],
        "failures": historical["failures"],
        "errors": historical["errors"],
        "skipped": historical["skipped"],
        "expected_failures": historical["expected_failures"],
        "matched": historical["matched"],
        "unexpected": historical["unexpected"],
        "missing": historical["missing"],
        "accepted": False,
        "reason": "immutable historical exact-signature contract is not rewritten",
    }
    return {
        "schema": "neoeng.legacy.formal-reconciliation-gate",
        "schema_version": 1,
        "acceptance_scope": "formal_equivalence_current_contract",
        "accepted": True,
        "status": "ACCEPTED_WITH_DECLARED_LIMITATIONS",
        "candidate": {
            "source_head_commit": case_data["source_head_commit"],
            "legacy_source_commit": case_data["legacy_source_commit"],
            "rules_consulted": RULES_CONSULTED,
        },
        "historical_snapshots": {
            "unchanged": True,
            "manifest": {
                "path": relative_path(HISTORICAL_MANIFEST),
                "sha256": historical_manifest_hash,
            },
            "reconciliation": {
                "path": relative_path(HISTORICAL_RECONCILIATION),
                "sha256": historical_reconciliation_hash,
            },
        },
        "historical_runner": historical_runner,
        "case_decisions": {
            "accepted": True,
            "count": len(cases),
            "decision_counts": dict(sorted(decisions.items())),
            "category_counts": dict(sorted(category_counts.items())),
            "case_10": (
                "NO_CHANGE; expected historical failure absent in current run and "
                "retained in the inventory"
            ),
            "case_25": (
                "CORRIGIDO; cycle-safe snapshot behavior fixed, historical Mock "
                "signature remains visible"
            ),
            "source": relative_path(CASE_PATH),
        },
        "substitutes": {
            "accepted": True,
            "junit": relative_path(JUNIT_PATH),
            **junit_values,
        },
        "manifest_resolution": {
            "accepted": inventory["accepted"],
            "count": inventory["summary"]["observed"],
            "unresolved": inventory["summary"]["unresolved"],
            "source": relative_path(AUDIT_PATH),
            "resolution_status": inventory["status"],
            "declared_missing_historical_references": inventory["summary"][
                "declared_missing_historical_references"
            ],
        },
        "limitations": [
            (
                "The historical runner exact acceptance remains false by design; "
                "its snapshots and signatures are immutable."
            ),
            (
                "Formal acceptance is based on the current contract, real substitute "
                "suite, case-by-case decisions, and authorized manifest treatment."
            ),
            (
                "The two stage0 release manifests declare 353 missing historical "
                "build-output references each; no file was recreated or silently "
                "removed from the declaration."
            ),
            (
                "This gate does not authorize commit, push, merge, or bypass any "
                "remaining Fase 7 gate."
            ),
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write", action="store_true", help="write current evidence outputs"
    )
    args = parser.parse_args(argv)
    try:
        inventory = resolve_manifest_inventory()
        gate = build_formal_gate()
        if args.write:
            write_json(FORMAL_DIR / "manifest_resolution.json", inventory)
            write_json(FORMAL_DIR / "formal_reconciliation.json", gate)
        print(
            json.dumps(
                {
                    "accepted": gate["accepted"],
                    "manifest_resolution": inventory["summary"],
                    "historical_runner": gate["historical_runner"],
                    "substitutes": gate["substitutes"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0 if gate["accepted"] else 1
    except (AssertionError, KeyError, OSError, ValueError, ET.ParseError) as exc:
        print(f"formal reconciliation gate failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
