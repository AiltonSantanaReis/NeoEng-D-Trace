"""Validate machine-readable stage evidence against FINAL_TARGET.

This validator is deliberately independent from the product runtime. It checks
the evidence contract and refuses to convert incomplete or unclassified results
into a pass. It does not rewrite reports or alter production files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"JSON raiz precisa ser objeto: {path}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate(baseline: dict[str, Any], report: dict[str, Any], report_path: Path) -> list[str]:
    errors: list[str] = []
    allowed = set(baseline.get("allowed_classifications", []))
    blocking = set(baseline.get("blocking_classifications", []))
    required = list(baseline.get("minimum_evidence", {}).get("required_fields", []))

    for field in required:
        if field not in report:
            fail(errors, f"campo obrigatório ausente: {field}")

    if report.get("baseline_id") not in {None, "FINAL_TARGET"}:
        fail(errors, f"baseline incompatível: {report.get('baseline_id')!r}")

    checks = report.get("checks")
    if not isinstance(checks, list) or not checks:
        fail(errors, "checks precisa conter pelo menos uma verificação")
    else:
        for index, check in enumerate(checks):
            if not isinstance(check, dict):
                fail(errors, f"checks[{index}] não é objeto")
                continue
            classification = check.get("classification")
            if classification not in allowed:
                fail(errors, f"checks[{index}] possui classificação inválida: {classification!r}")
            if classification in blocking:
                fail(errors, f"checks[{index}] bloqueia aprovação: {classification}")
            if not check.get("id"):
                fail(errors, f"checks[{index}] sem id")
            if check.get("result") not in {"PASS", "FAIL", "REVIEW_REQUIRED", "NOT_APPLICABLE"}:
                fail(errors, f"checks[{index}] possui result inválido: {check.get('result')!r}")
            if classification == "EXPECTED_EVOLUTION" and not check.get("justification"):
                fail(errors, f"checks[{index}] evolução sem justification")

    artifacts = report.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        fail(errors, "artifacts precisa conter pelo menos um artefato")
    else:
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                fail(errors, f"artifacts[{index}] não é objeto")
                continue
            raw_path = artifact.get("path")
            expected_hash = artifact.get("sha256")
            if not raw_path or not expected_hash:
                fail(errors, f"artifacts[{index}] requer path e sha256")
                continue
            artifact_path = (report_path.parent / raw_path).resolve()
            if not artifact_path.is_file():
                fail(errors, f"artefato inexistente: {raw_path}")
                continue
            actual_hash = sha256(artifact_path)
            if actual_hash != expected_hash:
                fail(errors, f"hash divergente em {raw_path}: esperado {expected_hash}, obtido {actual_hash}")
            if artifact.get("visual") and artifact_path.suffix.lower() != ".png":
                fail(errors, f"artefato visual não é PNG: {raw_path}")

    decision = report.get("decision")
    if decision in {"PASS", "FORMALLY_COMPLETE"}:
        for classification in blocking:
            if any(check.get("classification") == classification for check in checks or [] if isinstance(check, dict)):
                fail(errors, f"decision {decision} incompatível com classificação bloqueadora: {classification}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Relatório JSON da etapa")
    parser.add_argument("--baseline", type=Path, default=Path("docs/evidence/final-target-baseline-v1.json"))
    args = parser.parse_args()

    try:
        baseline = load_json(args.baseline)
        report = load_json(args.report)
        errors = validate(baseline, report, args.report.resolve())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"decision": "FAIL", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2

    result = {"decision": "PASS" if not errors else "FAIL", "errors": errors, "report": str(args.report)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
