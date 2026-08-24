#!/usr/bin/env python3
"""Create and validate an immutable evidence package for an official phase run.

The command intentionally has no force, bypass, skip, ignore or overwrite mode.
An official package must be written to a new directory and must contain explicit
traceability, test results, fallback reporting, performance data and hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ID_PATTERN = re.compile(
    r"\b(?:MOD|REQ|FEAT|CMP|TEST|EVID|BUILD|BASE|ADR|RISK)-[A-Z0-9]+(?:-[A-Z0-9]+)+\b"
)
PHASE_PATTERN = re.compile(r"^F(?:0|[1-9][0-9]*)$", re.IGNORECASE)


class EvidenceError(RuntimeError):
    """A package cannot be accepted as official evidence."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_inside(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise EvidenceError(f"path outside workspace: {path}") from exc
    return resolved


def git_commit(workspace: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvidenceError("unable to resolve audited git commit") from exc
    commit = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise EvidenceError(f"invalid audited commit: {commit!r}")
    return commit


def find_ids(text: str) -> list[str]:
    return sorted(set(ID_PATTERN.findall(text)))


def load_registry_ids(path: Path) -> set[str]:
    if not path.is_file():
        raise EvidenceError(f"ID registry not found: {path}")
    ids = find_ids(path.read_text(encoding="utf-8"))
    if not ids:
        raise EvidenceError("ID registry contains no recognized stable IDs")
    if len(ids) != len(set(ids)):
        raise EvidenceError("ID registry contains duplicate IDs")
    for identifier in ids:
        if identifier != identifier.upper() or " " in identifier:
            raise EvidenceError(f"invalid ID spelling: {identifier}")
    return set(ids)


def load_json(path: Path, label: str) -> Any:
    if not path.is_file():
        raise EvidenceError(f"{label} not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"invalid JSON in {label}: {path}: {exc}") from exc


def validate_traceability(path: Path, registry_ids: set[str]) -> dict[str, Any]:
    payload = load_json(path, "traceability")
    records = payload.get("requirements") if isinstance(payload, dict) else payload
    if not isinstance(records, list) or not records:
        raise EvidenceError("traceability must contain a non-empty requirements list")

    seen_requirements: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            raise EvidenceError("traceability record must be an object")
        requirement_id = record.get("requirement_id")
        if not isinstance(requirement_id, str) or not requirement_id.startswith("REQ-"):
            raise EvidenceError("traceability record has invalid requirement_id")
        if requirement_id in seen_requirements:
            raise EvidenceError(f"duplicate traceability requirement: {requirement_id}")
        seen_requirements.add(requirement_id)
        identifiers = [requirement_id]
        for field in ("feature_ids", "component_ids", "test_ids", "evidence_ids"):
            value = record.get(field, [])
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise EvidenceError(f"{requirement_id}: {field} must be a list of IDs")
            identifiers.extend(value)
        missing = sorted(set(identifiers) - registry_ids)
        if missing:
            raise EvidenceError(f"{requirement_id}: IDs absent from registry: {missing}")
        if not record.get("test_ids"):
            raise EvidenceError(f"{requirement_id}: no tests linked")
        if not record.get("evidence_ids"):
            raise EvidenceError(f"{requirement_id}: no evidence linked")
        normalized.append(record)
    return {"requirements": normalized}


def parse_junit(path: Path, approved_skips: set[str]) -> dict[str, int]:
    if not path.is_file():
        raise EvidenceError(f"JUnit result not found: {path}")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise EvidenceError(f"invalid JUnit XML: {path}: {exc}") from exc
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    skipped_names: list[str] = []
    for suite in suites:
        for case in suite.findall("testcase"):
            totals["tests"] += 1
            name = case.attrib.get("classname", "") + "::" + case.attrib.get("name", "")
            if case.find("failure") is not None:
                totals["failures"] += 1
            if case.find("error") is not None:
                totals["errors"] += 1
            if case.find("skipped") is not None:
                totals["skipped"] += 1
                skipped_names.append(name)
    unapproved = sorted(set(skipped_names) - approved_skips)
    if unapproved:
        raise EvidenceError(f"unapproved skipped tests: {unapproved}")
    return totals


def percentile(samples: list[float], percentile_value: float) -> float:
    if not samples:
        raise EvidenceError("performance samples are empty")
    ordered = sorted(samples)
    rank = (len(ordered) - 1) * percentile_value
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def validate_performance(path: Path) -> dict[str, Any]:
    payload = load_json(path, "performance")
    raw_samples = payload.get("frame_time_ms")
    if not isinstance(raw_samples, list) or not raw_samples or not all(
        isinstance(item, (int, float)) and math.isfinite(float(item)) and float(item) >= 0
        for item in raw_samples
    ):
        raise EvidenceError("performance.frame_time_ms must contain finite non-negative samples")
    samples = [float(item) for item in raw_samples]
    minimum_samples = int(payload.get("minimum_samples", 1))
    if len(samples) < minimum_samples:
        raise EvidenceError(
            f"insufficient performance samples: {len(samples)} < {minimum_samples}"
        )
    result = {
        "sample_count": len(samples),
        "p50_ms": percentile(samples, 0.50),
        "p95_ms": percentile(samples, 0.95),
        "p99_ms": percentile(samples, 0.99),
        "worst_ms": max(samples),
        "minimum_samples": minimum_samples,
        "backend": payload.get("backend", "UNKNOWN"),
        "hardware": payload.get("hardware", "UNKNOWN"),
    }
    return result


def copy_sources(sources: Iterable[Path], workspace: Path, package_root: Path) -> list[Path]:
    copied: list[Path] = []
    for source in sources:
        source = resolve_inside(source, workspace)
        if source == package_root or package_root in source.parents:
            raise EvidenceError("source overlaps output package")
        if source.is_file():
            relative = source.relative_to(workspace)
            target = package_root / "input" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target)
        elif source.is_dir():
            for item in sorted(source.rglob("*")):
                if item.is_file():
                    relative = item.relative_to(workspace)
                    target = package_root / "input" / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
                    copied.append(target)
        else:
            raise EvidenceError(f"source does not exist: {source}")
    return copied


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_manifest(package_root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(package_root.rglob("*")):
        if not path.is_file() or path.name in {"manifest.json", "hashes.sha256"}:
            continue
        entries.append(
            {
                "path": path.relative_to(package_root).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return entries


def write_hashes(package_root: Path, manifest: list[dict[str, Any]]) -> None:
    lines = [f"{entry['sha256']}  {entry['path']}" for entry in manifest]
    (package_root / "hashes.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--phase", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--traceability", type=Path, required=True)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--fallback-report", type=Path, required=True)
    parser.add_argument("--performance", type=Path, required=True)
    parser.add_argument("--source", type=Path, action="append", required=True)
    parser.add_argument("--approved-skip", action="append", default=[])
    parser.add_argument("--expected-commit")
    parser.add_argument("--official", action="store_true")
    return parser.parse_args(argv)


def run(argv: list[str]) -> int:
    args = parse_args(argv)
    workspace = args.workspace.resolve()
    if not PHASE_PATTERN.fullmatch(args.phase.upper()):
        raise EvidenceError(f"invalid phase: {args.phase}; expected F<number>")
    phase = args.phase.upper()
    output = resolve_inside(args.output, workspace)
    if output.exists() and any(output.iterdir()):
        raise EvidenceError(f"output must be new and empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    commit = git_commit(workspace)
    if args.expected_commit and args.expected_commit != commit:
        raise EvidenceError(f"commit mismatch: expected {args.expected_commit}, got {commit}")
    registry = resolve_inside(args.registry, workspace)
    traceability = resolve_inside(args.traceability, workspace)
    junit = resolve_inside(args.junit, workspace)
    fallback = resolve_inside(args.fallback_report, workspace)
    performance = resolve_inside(args.performance, workspace)
    registry_ids = load_registry_ids(registry)
    traceability_payload = validate_traceability(traceability, registry_ids)
    approved_skips = set(args.approved_skip)
    junit_summary = parse_junit(junit, approved_skips)
    if args.official and (junit_summary["failures"] or junit_summary["errors"]):
        raise EvidenceError(f"JUnit failures/errors: {junit_summary}")
    fallback_payload = load_json(fallback, "fallback report")
    if not isinstance(fallback_payload, dict) or "backend" not in fallback_payload:
        raise EvidenceError("fallback report must identify the backend")
    performance_summary = validate_performance(performance)
    copied = copy_sources(args.source, workspace, output)
    for source in (registry, traceability, junit, fallback, performance):
        copied.append(copy_sources([source], workspace, output)[0])

    environment = {
        "phase": phase,
        "commit": commit,
        "generated_at_utc": utc_now(),
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "official": bool(args.official),
    }
    write_json(output / "environment.json", environment)
    write_json(output / "traceability.json", traceability_payload)
    write_json(output / "junit-summary.json", junit_summary)
    write_json(output / "fallback-summary.json", fallback_payload)
    write_json(output / "performance.json", performance_summary)
    manifest = build_manifest(output)
    write_json(output / "manifest.json", manifest)
    write_hashes(output, manifest)
    report = {
        "status": "PASS",
        "phase": phase,
        "commit": commit,
        "official": bool(args.official),
        "manifest_entries": len(manifest),
        "junit": junit_summary,
        "performance": performance_summary,
        "fallback_backend": fallback_payload.get("backend"),
        "source_files": len(copied),
    }
    write_json(output / "package-report.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def main() -> int:
    try:
        return run(sys.argv[1:])
    except EvidenceError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
