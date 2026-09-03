#!/usr/bin/env python3
"""Run the immutable legacy suite and the reviewed current-contract gate.

The historical runner remains exact and may return a non-zero status when a
current failure has a changed signature or an old expected failure is absent.
This gate keeps that raw result visible, validates the reviewed current
outcomes without changing historical snapshots, and executes every real
replacement test before accepting the candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from tools.run_legacy_tests import (
    load_manifest,
    load_reconciliation,
    normalize_lf,
    parse_junit,
)

ROOT = Path(__file__).resolve().parents[1]
CURRENT_CONTRACT_RELATIVE = Path("quality/legacy_tests/current_contract.json")
NATIVE_CONTRACT_FILES = (
    "tests/test_legacy_phase1_contracts.py",
    "tests/test_legacy_phase2_contracts.py",
    "tests/test_legacy_phase3_contracts.py",
    "tests/test_legacy_phase4_contracts.py",
)


def write_json_lf(path: Path, value: Any) -> None:
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    path.write_bytes(payload.replace("\r\n", "\n").replace("\r", "\n").encode())


def load_current_contract(project_root: Path) -> tuple[Path, dict[str, Any]]:
    path = project_root / CURRENT_CONTRACT_RELATIVE
    if not path.is_file():
        raise FileNotFoundError(f"Current legacy contract not found: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Current legacy contract must be a JSON object")
    return path, value


def _canonical_sha256(path: Path) -> str:
    return hashlib.sha256(normalize_lf(path.read_bytes())).hexdigest()


def validate_current_contract(
    project_root: Path,
    contract: dict[str, Any],
    expectations: dict[str, dict],
) -> dict[str, Any]:
    if contract.get("schema") != "neoeng.legacy.current-contract-reconciliation":
        raise ValueError("Unsupported current legacy contract schema")
    if contract.get("schema_version") != 1:
        raise ValueError("Unsupported current legacy contract version")

    manifest_root, historical_manifest = load_manifest(project_root)
    snapshots = contract.get("historical_snapshots")
    if not isinstance(snapshots, dict):
        raise ValueError("Current contract is missing historical_snapshots")
    manifest_snapshot = snapshots.get("manifest")
    reconciliation_snapshot = snapshots.get("reconciliation")
    if not isinstance(manifest_snapshot, dict) or not isinstance(
        reconciliation_snapshot, dict
    ):
        raise ValueError("Current contract has invalid historical snapshot records")

    manifest_path = manifest_root / "manifest.json"
    reconciliation_path = manifest_root / "reconciliation.json"
    if manifest_snapshot.get("path") != "quality/legacy_tests/manifest.json":
        raise ValueError("Current contract points to an invalid historical manifest")
    if reconciliation_snapshot.get("path") != (
        "quality/legacy_tests/reconciliation.json"
    ):
        raise ValueError("Current contract points to an invalid reconciliation")
    if manifest_snapshot.get("sha256_lf") != _canonical_sha256(manifest_path):
        raise ValueError("Historical legacy manifest hash does not match")
    if reconciliation_snapshot.get("sha256_lf") != _canonical_sha256(
        reconciliation_path
    ):
        raise ValueError("Historical legacy reconciliation hash does not match")
    if contract.get("legacy_source_commit") != historical_manifest.get("source_commit"):
        raise ValueError(
            "Current contract legacy source commit does not match manifest"
        )
    formal_source = contract.get("formal_decisions_source")
    if not isinstance(formal_source, dict):
        raise ValueError("Current contract is missing formal_decisions_source")
    if formal_source.get("path") != (
        "docs/evidence/artifacts/legacy-26-formal-review-20260901/"
        "case_decisions.json"
    ):
        raise ValueError(
            "Current contract points to an invalid formal decisions source"
        )
    formal_path = project_root / Path(formal_source["path"])
    if not formal_path.is_file():
        raise ValueError("Formal decisions source is missing")
    if (
        formal_source.get("sha256")
        != hashlib.sha256(formal_path.read_bytes()).hexdigest()
    ):
        raise ValueError("Formal decisions source hash does not match")
    formal_decisions = json.loads(formal_path.read_text(encoding="utf-8"))
    if formal_decisions.get("schema") != "neoeng.legacy.phase5.formal-case-decisions":
        raise ValueError("Unsupported formal decisions source schema")
    if formal_decisions.get("legacy_source_commit") != historical_manifest.get(
        "source_commit"
    ):
        raise ValueError(
            "Formal decisions source legacy commit does not match manifest"
        )
    if formal_decisions.get("historical_manifest_sha256") != _canonical_sha256(
        manifest_path
    ):
        raise ValueError("Formal decisions source manifest hash does not match")
    if (
        formal_decisions.get("historical_reconciliation_sha256")
        != hashlib.sha256(reconciliation_path.read_bytes()).hexdigest()
    ):
        raise ValueError("Formal decisions source reconciliation hash does not match")
    formal_cases = formal_decisions.get("cases")
    if not isinstance(formal_cases, list):
        raise ValueError("Formal decisions source cases must be a list")
    formal_case_map: dict[str, dict[str, Any]] = {}
    for formal_case in formal_cases:
        identifier = formal_case.get("legacy_id")
        if not isinstance(identifier, str) or identifier in formal_case_map:
            raise ValueError(
                "Formal decisions source has invalid or duplicate case IDs"
            )
        formal_case_map[identifier] = formal_case
    if set(formal_case_map) != set(expectations):
        raise ValueError(
            "Formal decisions source does not cover exactly the historical cases"
        )
    formal_substitute_references = sorted(
        {
            reference
            for formal_case in formal_cases
            for reference in formal_case.get("substitute_tests", [])
        }
    )
    if not formal_substitute_references:
        raise ValueError("Formal decisions source has no substitute tests")
    native_files = {
        Path(reference.split("::", 1)[0]).as_posix()
        for reference in formal_substitute_references
    }
    if not native_files.issubset(set(NATIVE_CONTRACT_FILES)):
        raise ValueError("Formal substitute test points outside native contract suite")

    observations = contract.get("current_observations")
    if not isinstance(observations, list):
        raise ValueError("Current contract current_observations must be a list")
    observation_map: dict[str, dict[str, Any]] = {}
    for item in observations:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("Every current observation requires a string id")
        identifier = item["id"]
        if identifier in observation_map:
            raise ValueError(f"Duplicate current observation id: {identifier}")
        if identifier not in expectations:
            raise ValueError(
                f"Current observation is not a historical expectation: {identifier}"
            )
        classification = item.get("classification")
        if classification not in {"unexpected_signature", "missing_expected_failure"}:
            raise ValueError(
                f"Unsupported current observation classification: {identifier}"
            )
        formal_case = formal_case_map[identifier]
        formal_observation = formal_case.get("historical_observation", {})
        if not isinstance(formal_observation, dict):
            raise ValueError(f"Formal decision has invalid observation: {identifier}")
        expected_classification = formal_observation.get("reconciliation")
        if expected_classification not in {
            "unexpected_signature",
            "missing_expected_failure",
        }:
            raise ValueError(f"Formal decision classification is invalid: {identifier}")
        if item.get("classification") != expected_classification:
            raise ValueError(f"Formal decision classification diverges: {identifier}")
        if item.get("decision") != formal_case.get("decision"):
            raise ValueError(f"Formal decision outcome diverges: {identifier}")
        if item.get("replacement_tests") != formal_case.get("substitute_tests"):
            raise ValueError(f"Formal decision substitutes diverge: {identifier}")
        if not item.get("replacement_tests"):
            raise ValueError(
                f"Current observation has no replacement tests: {identifier}"
            )
        if not item.get("rationale"):
            raise ValueError(f"Current observation lacks rationale: {identifier}")
        signature = item.get("current_signature")
        if classification == "unexpected_signature":
            if not isinstance(signature, dict):
                raise ValueError(f"Current signature is missing: {identifier}")
            if signature.get("kind") not in {"failure", "error"}:
                raise ValueError(f"Current signature kind is invalid: {identifier}")
            if (
                not isinstance(signature.get("body_contains"), str)
                or not signature["body_contains"]
            ):
                raise ValueError(f"Current signature marker is invalid: {identifier}")
        elif signature is not None:
            raise ValueError(
                f"Missing-failure observation cannot have a signature: {identifier}"
            )
        observation_map[identifier] = item

    expected_ids = set(expectations)
    observed_ids = set(observation_map)
    if len(observed_ids) != 12:
        raise ValueError(f"Expected 12 current observations; found {len(observed_ids)}")
    exact_ids = expected_ids - observed_ids
    if len(exact_ids) != 15:
        raise ValueError(f"Expected 15 historical exact cases; found {len(exact_ids)}")

    historical_runner = contract.get("historical_runner")
    if not isinstance(historical_runner, dict):
        raise ValueError("Current contract is missing historical_runner")
    for key in (
        "selected_files",
        "tests",
        "failures",
        "errors",
        "skipped",
        "returncode",
        "exact_matches",
    ):
        if not isinstance(historical_runner.get(key), int):
            raise ValueError(f"Historical runner contract field is invalid: {key}")

    substitute_suite = contract.get("substitute_suite")
    if not isinstance(substitute_suite, dict):
        raise ValueError("Current contract is missing substitute_suite")
    for key in (
        "expected_tests",
        "expected_failures",
        "expected_errors",
        "expected_skipped",
    ):
        if not isinstance(substitute_suite.get(key), int):
            raise ValueError(f"Substitute suite contract field is invalid: {key}")
    if substitute_suite.get("test_files") != list(NATIVE_CONTRACT_FILES):
        raise ValueError(
            "Substitute suite files do not match the reviewed native suite"
        )

    return {
        "historical_manifest": manifest_path,
        "historical_reconciliation": reconciliation_path,
        "formal_decisions": formal_path,
        "expectations": expectations,
        "observations": observation_map,
        "exact_ids": exact_ids,
        "formal_substitute_references": formal_substitute_references,
        "substitute_references": list(NATIVE_CONTRACT_FILES),
    }


def _failure_details_by_id(summary: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    details: dict[str, list[dict[str, Any]]] = {}
    for result in summary.get("results", []):
        for detail in result.get("failure_details", []):
            identifier = detail.get("id")
            if not isinstance(identifier, str):
                identifier = "::".join(
                    (
                        Path(result["file"]).stem,
                        detail.get("classname", ""),
                        detail.get("name", ""),
                    )
                )
            details.setdefault(identifier, []).append(detail)
    return details


def _signature_matches(detail: dict[str, Any], signature: dict[str, Any]) -> bool:
    if detail.get("kind") != signature.get("kind"):
        return False
    observed = f"{detail.get('message', '')}\n{detail.get('body', '')}"
    return signature["body_contains"] in observed


def evaluate_historical_summary(
    summary: dict[str, Any],
    contract: dict[str, Any],
    validated: dict[str, Any],
    raw_returncode: int,
) -> dict[str, Any]:
    failures: list[str] = []
    expected_runner = contract["historical_runner"]
    totals = summary.get("totals", {})
    for key in ("tests", "failures", "errors", "skipped"):
        if totals.get(key) != expected_runner[key]:
            failures.append(
                f"historical totals.{key}={totals.get(key)!r}; "
                f"expected {expected_runner[key]!r}"
            )
    if summary.get("selected_files") != expected_runner["selected_files"]:
        failures.append("historical selected file count changed")
    if raw_returncode != expected_runner["returncode"]:
        failures.append(
            f"historical runner returncode={raw_returncode}; "
            f"expected {expected_runner['returncode']}"
        )
    if summary.get("working_tree_dirty") is not False:
        failures.append("historical runner did not execute from a clean tree")

    reconciliation = summary.get("reconciliation", {})
    observations = validated["observations"]
    expected_ids = set(validated["expectations"])
    observation_ids = set(observations)
    unexpected_ids = {
        item.get("id") for item in reconciliation.get("unexpected_failures", [])
    }
    missing_ids = set(reconciliation.get("missing_expected_failures", []))
    if unexpected_ids != {
        identifier
        for identifier, item in observations.items()
        if item["classification"] == "unexpected_signature"
    }:
        failures.append(
            "historical unexpected failure IDs do not match the reviewed contract"
        )
    if missing_ids != observation_ids:
        failures.append(
            "historical missing failure IDs do not match the reviewed contract"
        )
    if reconciliation.get("expected_failures") != len(expected_ids):
        failures.append("historical expected failure count changed")
    if reconciliation.get("matched_failures") != len(validated["exact_ids"]):
        failures.append("historical exact-match count changed")
    if set(unexpected_ids) - expected_ids:
        failures.append("historical runner reported an unknown failure ID")
    if set(missing_ids) - expected_ids:
        failures.append("historical runner reported an unknown missing ID")

    details = _failure_details_by_id(summary)
    if set(details) - expected_ids:
        failures.append("historical runner produced an unreviewed failure ID")

    for identifier in validated["exact_ids"]:
        matching = details.get(identifier, [])
        if len(matching) != 1:
            failures.append(
                f"historical exact case does not have one failure: {identifier}"
            )
            continue
        expectation = validated["expectations"][identifier]
        detail = matching[0]
        observed = f"{detail.get('message', '')}\n{detail.get('body', '')}"
        if detail.get("kind") != expectation.get("kind", "failure"):
            failures.append(f"historical exact case kind changed: {identifier}")
        if expectation.get("message_contains") not in observed:
            failures.append(f"historical exact case signature changed: {identifier}")

    for identifier, item in observations.items():
        matching = details.get(identifier, [])
        if item["classification"] == "missing_expected_failure":
            if matching:
                failures.append(
                    f"reviewed missing case produced a failure: {identifier}"
                )
            continue
        if len(matching) != 1:
            failures.append(
                f"reviewed signature case does not have one failure: {identifier}"
            )
            continue
        if not _signature_matches(matching[0], item["current_signature"]):
            failures.append(f"current failure signature changed: {identifier}")

    return {
        "accepted": not failures,
        "errors": failures,
        "observed_failure_ids": sorted(details),
        "historical_exact_ids": sorted(validated["exact_ids"]),
    }


def run_substitute_suite(
    project_root: Path,
    references: list[str],
    expected: dict[str, Any],
    output: Path,
    *,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    junit_path = output / "substitutes.xml"
    log_path = output / "substitutes.txt"
    environment = os.environ.copy()
    environment.setdefault("QT_QPA_PLATFORM", "offscreen")
    environment.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    existing_pythonpath = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = str(project_root) + (
        os.pathsep + existing_pythonpath if existing_pythonpath else ""
    )
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--tb=short",
        f"--junitxml={junit_path}",
        *references,
    ]
    timed_out = False
    try:
        process = subprocess.run(
            command,
            cwd=project_root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout_seconds,
        )
        output_text = process.stdout
        returncode = process.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        captured = exc.stdout or ""
        if isinstance(captured, bytes):
            captured = captured.decode("utf-8", errors="replace")
        output_text = captured + f"\nTIMEOUT after {timeout_seconds} seconds\n"
        returncode = 124
    log_path.write_text(output_text, encoding="utf-8", errors="replace")
    metrics = parse_junit(junit_path)
    return {
        "command": command,
        "returncode": returncode,
        "timed_out": timed_out,
        "junit": str(junit_path),
        "log": str(log_path),
        "tests": metrics["tests"],
        "failures": metrics["failures"],
        "errors": metrics["errors"],
        "skipped": metrics["skipped"],
        "accepted": (
            not timed_out
            and returncode == 0
            and metrics["tests"] == expected["expected_tests"]
            and metrics["failures"] == expected["expected_failures"]
            and metrics["errors"] == expected["expected_errors"]
            and metrics["skipped"] == expected["expected_skipped"]
        ),
    }


def _output_path(project_root: Path, requested: Path | None) -> Path:
    output = requested or (
        Path(tempfile.gettempdir()) / "neoeng-d-trace-formal-legacy-gate"
    )
    resolved = output.resolve()
    try:
        resolved.relative_to(project_root.resolve())
    except ValueError:
        return resolved
    raise ValueError("formal legacy gate output must be outside the project tree")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=("all",), default="all")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    args = parser.parse_args(argv)

    project_root = ROOT
    try:
        output = _output_path(project_root, args.output)
        output.mkdir(parents=True, exist_ok=True)
        contract_path, contract = load_current_contract(project_root)
        _, expectations = load_reconciliation(project_root / "quality/legacy_tests")
        validated = validate_current_contract(project_root, contract, expectations)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"formal legacy contract failed: {exc}", file=sys.stderr)
        return 2

    historical_output = output / "historical"
    historical_output.mkdir(parents=True, exist_ok=True)
    historical_command = [
        sys.executable,
        str(project_root / "tools/run_legacy_tests.py"),
        "--group",
        args.group,
        "--output",
        str(historical_output),
    ]
    try:
        historical_process = subprocess.run(
            historical_command,
            cwd=project_root,
            env=os.environ.copy(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=args.timeout_seconds,
        )
        historical_stdout = historical_process.stdout
        historical_returncode = historical_process.returncode
    except subprocess.TimeoutExpired as exc:
        captured = exc.stdout or ""
        if isinstance(captured, bytes):
            captured = captured.decode("utf-8", errors="replace")
        historical_stdout = (
            captured + f"\nTIMEOUT after {args.timeout_seconds} seconds\n"
        )
        historical_returncode = 124
    historical_log = output / "historical-runner.txt"
    historical_log.write_text(historical_stdout, encoding="utf-8", errors="replace")
    historical_summary_path = historical_output / "summary.json"
    if not historical_summary_path.is_file():
        report = {
            "schema": "neoeng.legacy.formal-runner-report",
            "schema_version": 1,
            "accepted": False,
            "errors": ["historical runner did not produce summary.json"],
            "historical_runner": {
                "returncode": historical_returncode,
                "log": str(historical_log),
            },
        }
        write_json_lf(output / "formal-gate.json", report)
        print("Formal legacy gate: FAILED (historical summary missing)")
        return 1

    historical_summary = json.loads(historical_summary_path.read_text(encoding="utf-8"))
    historical_evaluation = evaluate_historical_summary(
        historical_summary, contract, validated, historical_returncode
    )
    substitutes = run_substitute_suite(
        project_root,
        validated["substitute_references"],
        contract["substitute_suite"],
        output,
        timeout_seconds=args.timeout_seconds,
    )
    errors = list(historical_evaluation["errors"])
    if not substitutes["accepted"]:
        errors.append("current-contract replacement suite was not accepted")
    report = {
        "schema": "neoeng.legacy.formal-runner-report",
        "schema_version": 1,
        "accepted": not errors,
        "tested_commit": historical_summary.get("tested_commit"),
        "source_head_commit": historical_summary.get("source_head_commit"),
        "current_contract": {
            "path": str(contract_path),
            "sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        },
        "historical_runner": {
            "returncode": historical_returncode,
            "log": str(historical_log),
            "summary": str(historical_summary_path),
            "raw_test_status": historical_summary.get("raw_test_status"),
            "totals": historical_summary.get("totals"),
            "reconciliation": historical_summary.get("reconciliation"),
            "working_tree_dirty": historical_summary.get("working_tree_dirty"),
            "evaluation": historical_evaluation,
        },
        "case_resolution": {
            "historical_exact": len(validated["exact_ids"]),
            "unexpected_signatures": sum(
                item["classification"] == "unexpected_signature"
                for item in validated["observations"].values()
            ),
            "historical_missing_expected_failures": len(
                historical_summary.get("reconciliation", {}).get(
                    "missing_expected_failures", []
                )
            ),
            "current_missing_observations": sum(
                item["classification"] == "missing_expected_failure"
                for item in validated["observations"].values()
            ),
            "resolved_cases": len(validated["expectations"]),
        },
        "substitutes": substitutes,
        "errors": errors,
    }
    write_json_lf(output / "formal-gate.json", report)
    print(
        "Formal legacy gate: "
        f"{'ACCEPTED' if report['accepted'] else 'FAILED'}; "
        f"historical_returncode={historical_returncode}; "
        f"exact={report['case_resolution']['historical_exact']}; "
        f"changed={report['case_resolution']['unexpected_signatures']}; "
        f"missing={report['case_resolution']['historical_missing_expected_failures']}; "
        f"substitutes={substitutes['tests']} tests"
    )
    if errors:
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
    print(f"Report: {output / 'formal-gate.json'}")
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
