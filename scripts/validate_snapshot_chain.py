"""Validate an incremental baseline snapshot and its artifact hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON raiz não é objeto: {path}")
    return value


def validate(snapshot_path: Path, final_target_path: Path, parent_path: Path | None = None) -> list[str]:
    errors: list[str] = []
    snapshot_root = snapshot_path.parent.resolve()
    snapshot = read(snapshot_path)
    report_ref = snapshot.get("stage0_report") or snapshot.get("report")
    inventory_ref = snapshot.get("inventory")
    if not isinstance(report_ref, dict) or not isinstance(inventory_ref, dict):
        errors.append("snapshot precisa referenciar stage0_report/report e inventory")
        return errors

    match = re.match(r"STAGE_(\d+)_SNAPSHOT:([0-9a-f]+)$", str(snapshot.get("snapshot_id", "")))
    if not match:
        errors.append("snapshot_id inválido")
        return errors
    stage = int(match.group(1))
    report_path = (snapshot_root / str(report_ref.get("path"))).resolve()
    inventory_path = (snapshot_root / str(inventory_ref.get("path"))).resolve()
    for label, path, expected in (("report", report_path, report_ref.get("sha256")), ("inventory", inventory_path, inventory_ref.get("sha256"))):
        if snapshot_root not in path.parents:
            errors.append(f"{label} fora da raiz do snapshot")
        elif not path.is_file():
            errors.append(f"{label} inexistente: {path}")
        elif sha256(path) != expected:
            errors.append(f"hash divergente do {label}")

    final_target_sha = snapshot.get("final_target_manifest_sha256")
    if final_target_sha != sha256(final_target_path.resolve()):
        errors.append("snapshot não aponta para o hash atual de FINAL_TARGET")

    if stage == 0:
        if snapshot.get("parent_snapshot_id") is not None:
            errors.append("STAGE_0_SNAPSHOT não pode possuir pai")
        if parent_path is not None:
            errors.append("snapshot raiz não deve receber parent_path")
    else:
        if not snapshot.get("parent_snapshot_id"):
            errors.append("snapshot posterior requer parent_snapshot_id")
        if parent_path is None:
            errors.append("snapshot posterior requer parent_path para validação")
        else:
            parent = read(parent_path)
            if parent.get("snapshot_id") != snapshot.get("parent_snapshot_id"):
                errors.append("parent_snapshot_id não corresponde ao manifesto pai")
            if snapshot.get("parent_manifest_sha256") != sha256(parent_path.resolve()):
                errors.append("parent_manifest_sha256 divergente")

    report = read(report_path) if report_path.is_file() else {}
    if report.get("parent_snapshot_id") != snapshot.get("parent_snapshot_id"):
        errors.append("parent_snapshot_id diverge entre snapshot e relatório")
    if report.get("baseline_id") != "FINAL_TARGET":
        errors.append("relatório não usa FINAL_TARGET")
    seen: set[str] = set()
    for artifact in snapshot.get("artifacts", []):
        if not isinstance(artifact, dict):
            errors.append("artefato inválido")
            continue
        raw = str(artifact.get("path", ""))
        path = (snapshot_root / raw).resolve()
        if raw in seen:
            errors.append(f"artefato duplicado: {raw}")
        seen.add(raw)
        if snapshot_root not in path.parents or not path.is_file():
            errors.append(f"artefato inexistente ou fora da raiz: {raw}")
        elif sha256(path) != artifact.get("sha256"):
            errors.append(f"hash divergente do artefato: {raw}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--final-target", type=Path, default=Path("docs/evidence/final-target-baseline-v1.json"))
    parser.add_argument("--parent", type=Path)
    args = parser.parse_args()
    try:
        errors = validate(args.snapshot.resolve(), args.final_target.resolve(), args.parent.resolve() if args.parent else None)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors = [str(exc)]
    result = {"decision": "PASS" if not errors else "FAIL", "errors": errors, "snapshot": str(args.snapshot)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
