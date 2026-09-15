from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.validate_strict_delivery_gate import (
    ROOT,
    SEALED_LOCK_VALUES,
    StrictGateError,
    validate_delivery_manifest,
    validate_plan_lock,
    validate_stage_ack,
)


def _write(path: Path, content: str | bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8", newline="\n")
    return path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _base(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    plan = _write(
        tmp_path / SEALED_LOCK_VALUES["plan_path"],
        (ROOT / SEALED_LOCK_VALUES["plan_path"]).read_bytes(),
    )
    governance = _write(
        tmp_path / SEALED_LOCK_VALUES["governance_path"],
        (ROOT / SEALED_LOCK_VALUES["governance_path"]).read_bytes(),
    )
    addendum = _write(
        tmp_path / SEALED_LOCK_VALUES["strict_addendum_path"],
        (ROOT / SEALED_LOCK_VALUES["strict_addendum_path"]).read_bytes(),
    )
    _index = _write(
        tmp_path / SEALED_LOCK_VALUES["index_path"],
        (ROOT / SEALED_LOCK_VALUES["index_path"]).read_bytes(),
    )
    amendment = _write(
        tmp_path / SEALED_LOCK_VALUES["amendment_path"],
        (ROOT / SEALED_LOCK_VALUES["amendment_path"]).read_bytes(),
    )
    assert _index.is_file()
    assert amendment.is_file()
    lock = {
        "schema_version": 1,
        **SEALED_LOCK_VALUES,
        "immutable": True,
        "amendment_policy": "ADDENDUM_ONLY",
        "release_gate_fail_closed": True,
        "stage_ack_required": True,
    }
    lock_path = _write(
        tmp_path / "docs" / "lock.json",
        json.dumps(lock, indent=2) + "\n",
    )
    return plan, governance, addendum, lock_path


def _ack(tmp_path: Path, lock_path: Path) -> Path:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    return _write(
        tmp_path / "evidence" / "stage-ack.json",
        json.dumps(
            {
                "schema_version": 1,
                "stage_id": "G0",
                "read_integrally": True,
                "validated": True,
                "no_conflict_found": True,
                "status": "PASS",
                "documents": [
                    {
                        "path": SEALED_LOCK_VALUES["plan_path"],
                        "sha256": lock["plan_sha256"],
                    },
                    {
                        "path": SEALED_LOCK_VALUES["governance_path"],
                        "sha256": lock["governance_sha256"],
                    },
                    {
                        "path": SEALED_LOCK_VALUES["strict_addendum_path"],
                        "sha256": lock["strict_addendum_sha256"],
                    },
                    {
                        "path": SEALED_LOCK_VALUES["amendment_path"],
                        "sha256": lock["amendment_sha256"],
                    },
                    {
                        "path": SEALED_LOCK_VALUES["index_path"],
                        "sha256": lock["index_sha256"],
                    },
                ],
                "plan_sha256": lock["plan_sha256"],
                "governance_sha256": lock["governance_sha256"],
                "reader": "test",
                "read_at_utc": "2026-09-15T12:00:00Z",
                "audited_commit": "abc123",
            },
            indent=2,
        )
        + "\n",
    )


def test_plan_lock_requires_exact_bytes(tmp_path: Path) -> None:
    plan, _, _, lock = _base(tmp_path)
    validate_plan_lock(tmp_path, lock)
    plan.write_text(plan.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
    with pytest.raises(StrictGateError, match="plan hash mismatch"):
        validate_plan_lock(tmp_path, lock)


def test_plan_lock_cannot_be_redirected_by_editing_only_the_lock(
    tmp_path: Path,
) -> None:
    _, _, _, lock = _base(tmp_path)
    data = json.loads(lock.read_text(encoding="utf-8"))
    data["plan_sha256"] = "0" * 64
    lock.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(StrictGateError, match="sealed lock value mismatch"):
        validate_plan_lock(tmp_path, lock)


def test_official_lock_requires_git_tracking(tmp_path: Path) -> None:
    _, _, _, lock = _base(tmp_path)
    with pytest.raises(StrictGateError, match="lock is not tracked"):
        validate_plan_lock(tmp_path, lock, require_tracked=True)


def test_stage_ack_requires_integral_hash_bound_read(tmp_path: Path) -> None:
    _, _, _, lock = _base(tmp_path)
    ack = _ack(tmp_path, lock)
    validate_stage_ack(ack, "G0", root=tmp_path, lock_path=lock)
    data = json.loads(ack.read_text(encoding="utf-8"))
    data["read_integrally"] = False
    ack.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(StrictGateError, match="read_integrally"):
        validate_stage_ack(ack, "G0", root=tmp_path, lock_path=lock)


def _delivery(tmp_path: Path, lock: Path) -> Path:
    artifact = _write(tmp_path / "artifacts" / "result.txt", b"real result\n")
    data = {
        "schema_version": 1,
        "manifest_type": "OFFICIAL_DELIVERY",
        "official": True,
        "status": "PASS",
        "source_tree_clean": True,
        "stage_id": "G0",
        "audited_commit": "abc123",
        "requirement_ids": ["REQ-REAL-01"],
        "feature_ids": ["FEAT-REAL-01"],
        "stage_ack_path": "evidence/stage-ack.json",
        "claim_scope": "BOUNDED_FEATURE",
        "all_required_ids_pass": False,
        "functional_flow_real": True,
        "limitations": [],
        "limitations_are_outside_claim_scope": True,
        "test": {
            "command": "python -m pytest -q",
            "full_official_suite": True,
            "selection": "FULL_OFFICIAL",
            "exit_code": 0,
            "skipped": 0,
            "xfails": 0,
            "unexpected_failures": 0,
            "warnings": 0,
            "failures": 0,
            "errors": 0,
            "mocks_used": False,
        },
        "integrity": {
            "evidence_class": "PRODUCT_FUNCTIONAL",
            "diagnostic_only": False,
            "synthetic_fixture": False,
            "source_only": False,
            "ui_only": False,
            "contract_only": False,
            "structural_only": False,
            "external_tool_only": False,
            "hidden_fallback": False,
            "hashes_verified": True,
            "real_input_used": True,
            "real_output_observed": True,
            "diagnostics_scanned": True,
            "source_files_scanned": True,
            "no_prohibited_markers": True,
            "prohibited_markers": [],
            "unresolved_diagnostics": [],
        },
        "runtime": {"required": False, "visual_capture_required": False},
        "artifacts": [
            {
                "path": "artifacts/result.txt",
                "sha256": _sha(artifact),
                "bytes": artifact.stat().st_size,
                "tracked": False,
            }
        ],
        "observed_result": "The real bounded flow produced the result.",
    }
    return _write(
        tmp_path / "evidence" / "delivery.json",
        json.dumps(data, indent=2) + "\n",
    )


def test_delivery_passes_only_with_real_clean_bounded_evidence(tmp_path: Path) -> None:
    _, _, _, lock = _base(tmp_path)
    ack = _ack(tmp_path, lock)
    manifest = _delivery(tmp_path, lock)
    validate_delivery_manifest(
        manifest, root=tmp_path, lock_path=lock, require_tracked=False
    )
    assert ack.is_file()


def test_delivery_blocks_skipped_tests(tmp_path: Path) -> None:
    _, _, _, lock = _base(tmp_path)
    _ack(tmp_path, lock)
    manifest = _delivery(tmp_path, lock)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["test"]["skipped"] = 1
    manifest.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(StrictGateError, match="skipped"):
        validate_delivery_manifest(
            manifest, root=tmp_path, lock_path=lock, require_tracked=False
        )


def test_delivery_blocks_suspicious_marker(tmp_path: Path) -> None:
    _, _, _, lock = _base(tmp_path)
    _ack(tmp_path, lock)
    manifest = _delivery(tmp_path, lock)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["test"]["command"] = "python -m pytest --ignore tests/fake"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(StrictGateError, match="bypass/suspicious"):
        validate_delivery_manifest(
            manifest, root=tmp_path, lock_path=lock, require_tracked=False
        )
