"""Fail-closed integrity gates for the immutable product plan.

This validator is deliberately conservative. It validates the lock, the
per-stage reading receipt and an official delivery manifest. It never promotes
diagnostic, mocked, synthetic or incomplete evidence to PASS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "docs" / "IMMUTABLE_PLAN_LOCK_2026-09-15.json"
SEALED_LOCK_VALUES = {
    "lock_id": "LOCK-PLAN-REAL-20260915-R1",
    "seal_revision": 2,
    "plan_path": "docs/PLANO_IMUTAVEL_PRODUTO_REAL_2026-09-15.md",
    "plan_sha256": ("215fb4552fa34924a05357a1558f94d4ed55788cc3c08acd8114883f2adde4fa"),
    "governance_path": (
        "docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md"
    ),
    "governance_sha256": (
        "4630b27f12a0966cccc20d4413da514c6eb310da9a48cf37e1fc07559e1a02b1"
    ),
    "strict_addendum_path": (
        "docs/ADENDO_GOVERNANCA_REALIDADE_EVIDENCIAS_2026-09-15.md"
    ),
    "strict_addendum_sha256": (
        "bc796f1e8da2a5ce96c1c6b8918a7a3a6dbc49f42a36107c600c554b5a7874b2"
    ),
    "index_path": "docs/INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md",
    "index_sha256": (
        "957f18529243a733fd36a94b159cc5ca0144b7ad09ca579655074776091f09fd"
    ),
    "canonical_text_eol": "LF",
    "amendment_path": "docs/ADENDO_01_PORTABILIDADE_HASH_EOF_2026-09-15.md",
    "amendment_sha256": (
        "70f96e54243ad2a0cc11d163042fc9f6ebec50bc36e1098066d6e98958bf2636"
    ),
}


class StrictGateError(ValueError):
    """Raised when an official integrity gate must block."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StrictGateError(f"missing JSON: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StrictGateError(f"unreadable JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise StrictGateError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise StrictGateError(f"cannot hash {path}: {exc}") from exc
    return digest.hexdigest()


def _safe_path(root: Path, raw: Any, label: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise StrictGateError(f"{label} must be a non-empty relative path")
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise StrictGateError(f"{label} must stay inside repository: {raw}")
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise StrictGateError(f"{label} escapes repository: {raw}")
    return resolved


def _safe_input_path(root: Path, path: Path, label: str) -> Path:
    """Resolve an input path only after proving it stays inside ``root``."""

    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise StrictGateError(f"{label} is outside repository: {path}") from exc
    return _safe_path(root, relative.as_posix(), label)


def _require(data: dict[str, Any], key: str, label: str = "manifest") -> Any:
    if key not in data:
        raise StrictGateError(f"{label} missing required field: {key}")
    return data[key]


def validate_plan_lock(
    root: Path = ROOT,
    lock_path: Path | None = None,
    *,
    require_tracked: bool = False,
) -> dict[str, Any]:
    """Validate the immutable plan and governance bytes against the lock."""

    root = root.resolve()
    lock_file = _safe_input_path(
        root,
        lock_path or (root / DEFAULT_LOCK.relative_to(ROOT)),
        "lock_path",
    )
    if require_tracked and not _git_tracked(root, lock_file):
        raise StrictGateError("immutable lock is not tracked")
    lock = _load_json(lock_file)
    if _require(lock, "schema_version", "lock") != 1:
        raise StrictGateError("unsupported immutable lock schema_version")
    if _require(lock, "immutable", "lock") is not True:
        raise StrictGateError("immutable lock is not enabled")
    if _require(lock, "amendment_policy", "lock") != "ADDENDUM_ONLY":
        raise StrictGateError("plan amendment policy is not ADDENDUM_ONLY")
    if _require(lock, "release_gate_fail_closed", "lock") is not True:
        raise StrictGateError("release gate is not fail-closed")
    if _require(lock, "stage_ack_required", "lock") is not True:
        raise StrictGateError("stage acknowledgement is not required")
    if _require(lock, "canonical_text_eol", "lock") != "LF":
        raise StrictGateError("canonical text EOL is not LF")
    for key, expected in SEALED_LOCK_VALUES.items():
        if lock.get(key) != expected:
            raise StrictGateError(f"sealed lock value mismatch: {key}")

    plan = _safe_path(root, _require(lock, "plan_path", "lock"), "plan_path")
    governance = _safe_path(
        root, _require(lock, "governance_path", "lock"), "governance_path"
    )
    strict_addendum = _safe_path(
        root,
        _require(lock, "strict_addendum_path", "lock"),
        "strict_addendum_path",
    )
    index = _safe_path(root, _require(lock, "index_path", "lock"), "index_path")
    amendment = _safe_path(
        root, _require(lock, "amendment_path", "lock"), "amendment_path"
    )
    expected_plan = _require(lock, "plan_sha256", "lock")
    expected_governance = _require(lock, "governance_sha256", "lock")
    expected_addendum = _require(lock, "strict_addendum_sha256", "lock")
    expected_index = _require(lock, "index_sha256", "lock")
    expected_amendment = _require(lock, "amendment_sha256", "lock")
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected_plan)):
        raise StrictGateError("plan_sha256 is not sealed")
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected_governance)):
        raise StrictGateError("governance_sha256 is not sealed")
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected_addendum)):
        raise StrictGateError("strict_addendum_sha256 is not sealed")
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected_index)):
        raise StrictGateError("index_sha256 is not sealed")
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected_amendment)):
        raise StrictGateError("amendment_sha256 is not sealed")
    if _sha256(plan) != expected_plan:
        raise StrictGateError("immutable plan hash mismatch")
    if _sha256(governance) != expected_governance:
        raise StrictGateError("governance hash mismatch")
    if _sha256(strict_addendum) != expected_addendum:
        raise StrictGateError("strict addendum hash mismatch")
    if _sha256(index) != expected_index:
        raise StrictGateError("active index hash mismatch")
    if _sha256(amendment) != expected_amendment:
        raise StrictGateError("amendment hash mismatch")
    if not strict_addendum.is_file():
        raise StrictGateError("strict governance addendum is missing")
    if not amendment.is_file():
        raise StrictGateError("numbered governance amendment is missing")

    plan_text = plan.read_text(encoding="utf-8")
    required_plan_markers = (
        "PLAN-REAL-PRODUCT-20260915",
        "IMMUTABLE_BASELINE",
        "ADDENDUM_ONLY",
        "PRODUCT-SCENE-FULL-01",
    )
    missing = [marker for marker in required_plan_markers if marker not in plan_text]
    if missing:
        raise StrictGateError(f"immutable plan missing markers: {missing}")
    return lock


def validate_stage_ack(
    ack_path: Path,
    stage_id: str,
    *,
    root: Path = ROOT,
    lock_path: Path | None = None,
    require_tracked: bool = False,
) -> dict[str, Any]:
    """Require an integral, hash-bound reading/validation receipt."""

    lock = validate_plan_lock(root, lock_path, require_tracked=require_tracked)
    ack_file = _safe_input_path(root, ack_path, "stage acknowledgement")
    if require_tracked and not _git_tracked(root, ack_file):
        raise StrictGateError("stage acknowledgement is not tracked")
    ack = _load_json(ack_file)
    if _require(ack, "schema_version", "stage acknowledgement") != 1:
        raise StrictGateError("unsupported stage acknowledgement schema_version")
    if _require(ack, "stage_id", "stage acknowledgement") != stage_id:
        raise StrictGateError("stage acknowledgement stage_id mismatch")
    for field in ("read_integrally", "validated", "no_conflict_found"):
        if _require(ack, field, "stage acknowledgement") is not True:
            raise StrictGateError(f"stage acknowledgement is not valid: {field}")
    if _require(ack, "status", "stage acknowledgement") != "PASS":
        raise StrictGateError("stage acknowledgement status must be PASS")
    documents = _require(ack, "documents", "stage acknowledgement")
    if not isinstance(documents, list) or not documents:
        raise StrictGateError("stage acknowledgement must list all documents read")
    seen_documents: set[str] = set()
    for document in documents:
        if not isinstance(document, dict):
            raise StrictGateError("stage acknowledgement document entry is invalid")
        document_path = _safe_path(
            root, _require(document, "path", "ack document"), "ack path"
        )
        document_hash = _require(document, "sha256", "ack document")
        if not re.fullmatch(r"[0-9a-f]{64}", str(document_hash)):
            raise StrictGateError("ack document hash is invalid")
        if not document_path.is_file():
            raise StrictGateError(f"ack document is missing: {document['path']}")
        if _sha256(document_path) != document_hash:
            raise StrictGateError(f"ack document hash mismatch: {document['path']}")
        if require_tracked and not _git_tracked(root, document_path):
            raise StrictGateError(f"ack document is not tracked: {document['path']}")
        seen_documents.add(document_path.relative_to(root).as_posix())
    mandatory_documents = {
        lock["plan_path"]: lock["plan_sha256"],
        lock["governance_path"]: lock["governance_sha256"],
        lock["strict_addendum_path"]: lock["strict_addendum_sha256"],
        lock["index_path"]: lock["index_sha256"],
        lock["amendment_path"]: lock["amendment_sha256"],
    }
    for path, expected_hash in mandatory_documents.items():
        if path not in seen_documents:
            raise StrictGateError(f"stage acknowledgement omitted: {path}")
        matching = next(
            (
                item
                for item in documents
                if item.get("path") == path and item.get("sha256") == expected_hash
            ),
            None,
        )
        if matching is None:
            raise StrictGateError(f"stage acknowledgement hash is not locked: {path}")
    if _require(ack, "plan_sha256", "stage acknowledgement") != lock["plan_sha256"]:
        raise StrictGateError("stage acknowledgement plan hash mismatch")
    if (
        _require(ack, "governance_sha256", "stage acknowledgement")
        != lock["governance_sha256"]
    ):
        raise StrictGateError("stage acknowledgement governance hash mismatch")
    for field in ("reader", "read_at_utc", "audited_commit"):
        if (
            not isinstance(_require(ack, field, "stage acknowledgement"), str)
            or not ack[field].strip()
        ):
            raise StrictGateError(f"stage acknowledgement field is empty: {field}")
    return ack


_BYPASS_PATTERNS = (
    re.compile(r"(?i)(^|\s)--no-verify(?:\s|$)"),
    re.compile(r"(?i)(^|\s)--(?:ignore|deselect|continue-on-error)(?:=|\s|$)"),
    re.compile(r"(?i)(^|\s)--(?:skip|xfail)(?:=|\s|$)"),
    re.compile(r"(?i)\b(?:monkeypatch|mock|fake|stub)\b"),
)


def _zero(value: Any, label: str) -> None:
    if isinstance(value, bool):
        if value:
            raise StrictGateError(f"official test {label} is non-zero")
        return
    if isinstance(value, int):
        if value != 0:
            raise StrictGateError(f"official test {label} is non-zero: {value}")
        return
    if isinstance(value, list):
        if value:
            raise StrictGateError(f"official test {label} contains entries")
        return
    raise StrictGateError(f"official test {label} must be an integer or list")


def _git_tracked(root: Path, path: Path) -> bool:
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _validate_artifacts(
    root: Path, artifacts: Any, *, require_tracked: bool
) -> set[str]:
    if not isinstance(artifacts, list) or not artifacts:
        raise StrictGateError("official delivery must list at least one artifact")
    paths: set[str] = set()
    for item in artifacts:
        if not isinstance(item, dict):
            raise StrictGateError("artifact entry is invalid")
        raw_path = _require(item, "path", "artifact")
        path = _safe_path(root, raw_path, "artifact path")
        if not path.is_file():
            raise StrictGateError(f"artifact is missing: {raw_path}")
        digest = _require(item, "sha256", "artifact")
        if not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
            raise StrictGateError(f"artifact hash is invalid: {raw_path}")
        if _sha256(path) != digest:
            raise StrictGateError(f"artifact hash mismatch: {raw_path}")
        size = _require(item, "bytes", "artifact")
        if not isinstance(size, int) or size != path.stat().st_size:
            raise StrictGateError(f"artifact byte count mismatch: {raw_path}")
        if require_tracked and (
            item.get("tracked") is not True or not _git_tracked(root, path)
        ):
            raise StrictGateError(f"official artifact is not tracked: {raw_path}")
        paths.add(Path(raw_path).as_posix())
    return paths


def validate_delivery_manifest(
    manifest_path: Path,
    *,
    root: Path = ROOT,
    lock_path: Path | None = None,
    require_tracked: bool = True,
) -> dict[str, Any]:
    """Validate a real, hash-bound official delivery package."""

    validate_plan_lock(root, lock_path, require_tracked=require_tracked)
    manifest_file = _safe_input_path(root, manifest_path, "delivery manifest")
    manifest = _load_json(manifest_file)
    if _require(manifest, "schema_version", "delivery") != 1:
        raise StrictGateError("unsupported delivery manifest schema_version")
    if _require(manifest, "manifest_type", "delivery") != "OFFICIAL_DELIVERY":
        raise StrictGateError("manifest is not an official delivery")
    if _require(manifest, "official", "delivery") is not True:
        raise StrictGateError("delivery is not marked official")
    if _require(manifest, "status", "delivery") != "PASS":
        raise StrictGateError("delivery status must be PASS")
    if _require(manifest, "source_tree_clean", "delivery") is not True:
        raise StrictGateError("official delivery requires a clean source tree")
    for field in ("stage_id", "audited_commit", "observed_result"):
        value = _require(manifest, field, "delivery")
        if not isinstance(value, str) or not value.strip():
            raise StrictGateError(f"delivery field is empty: {field}")
    for field in ("requirement_ids", "feature_ids"):
        values = _require(manifest, field, "delivery")
        if (
            not isinstance(values, list)
            or not values
            or not all(isinstance(value, str) and value.strip() for value in values)
        ):
            raise StrictGateError(f"delivery field is incomplete: {field}")
    ack_raw = _require(manifest, "stage_ack_path", "delivery")
    ack_path = _safe_path(root, ack_raw, "stage_ack_path")
    validate_stage_ack(
        ack_path,
        manifest["stage_id"],
        root=root,
        lock_path=lock_path,
        require_tracked=require_tracked,
    )

    test = _require(manifest, "test", "delivery")
    if not isinstance(test, dict):
        raise StrictGateError("delivery test section is invalid")
    if test.get("full_official_suite") is not True:
        raise StrictGateError("delivery test is not the full official suite")
    if test.get("selection") != "FULL_OFFICIAL":
        raise StrictGateError("delivery test selection is not FULL_OFFICIAL")
    if test.get("exit_code") != 0:
        raise StrictGateError("official test exit code is not zero")
    for field in (
        "skipped",
        "xfails",
        "unexpected_failures",
        "warnings",
        "failures",
        "errors",
    ):
        _zero(_require(test, field, "test"), field)
    if test.get("mocks_used") is not False:
        raise StrictGateError("official test reports mocks_used")
    command = test.get("command")
    if not isinstance(command, str) or not command.strip():
        raise StrictGateError("official test command is missing")
    for pattern in _BYPASS_PATTERNS:
        if pattern.search(command):
            raise StrictGateError(
                "official test command contains a bypass/suspicious marker"
            )

    integrity = _require(manifest, "integrity", "delivery")
    if not isinstance(integrity, dict):
        raise StrictGateError("delivery integrity section is invalid")
    if integrity.get("evidence_class") not in {"PRODUCT_FUNCTIONAL", "ENGINE_RUNTIME"}:
        raise StrictGateError("evidence class cannot prove an official delivery")
    forbidden_flags = (
        "diagnostic_only",
        "synthetic_fixture",
        "source_only",
        "ui_only",
        "contract_only",
        "structural_only",
        "external_tool_only",
        "hidden_fallback",
    )
    for field in forbidden_flags:
        if integrity.get(field) is not False:
            raise StrictGateError(f"integrity flag is not clean: {field}")
    for field in (
        "hashes_verified",
        "real_input_used",
        "real_output_observed",
        "diagnostics_scanned",
        "source_files_scanned",
        "no_prohibited_markers",
    ):
        if integrity.get(field) is not True:
            raise StrictGateError(f"integrity proof is missing: {field}")
    if integrity.get("prohibited_markers") != []:
        raise StrictGateError("prohibited markers were detected")
    if integrity.get("unresolved_diagnostics") != []:
        raise StrictGateError("unresolved diagnostics remain")

    if manifest.get("functional_flow_real") is not True:
        raise StrictGateError("real user flow was not proven")
    limitations = _require(manifest, "limitations", "delivery")
    if not isinstance(limitations, list) or not all(
        isinstance(value, str) for value in limitations
    ):
        raise StrictGateError("delivery limitations must be a string list")
    claim_scope = _require(manifest, "claim_scope", "delivery")
    if claim_scope not in {"BOUNDED_FEATURE", "COMPLETE_PRODUCT"}:
        raise StrictGateError("unknown delivery claim_scope")
    if manifest.get("limitations_are_outside_claim_scope") is not True:
        raise StrictGateError("limitations are not bounded outside the claim")
    if claim_scope == "COMPLETE_PRODUCT":
        if manifest.get("all_required_ids_pass") is not True or limitations:
            raise StrictGateError("complete-product claim has incomplete requirements")

    runtime = _require(manifest, "runtime", "delivery")
    if not isinstance(runtime, dict):
        raise StrictGateError("delivery runtime section is invalid")
    if runtime.get("required") is True:
        required_runtime = (
            "real_engine",
            "clean_project",
            "process_started",
            "artifact_observed",
            "visual_capture_required",
        )
        for field in required_runtime:
            if runtime.get(field) is not True:
                raise StrictGateError(f"real runtime proof is missing: {field}")
        if runtime.get("process_exit_code") != 0:
            raise StrictGateError("real runtime did not exit successfully")
        if not isinstance(runtime.get("engine"), str) or not runtime["engine"].strip():
            raise StrictGateError("real runtime engine is missing")
        if (
            not isinstance(runtime.get("version"), str)
            or not runtime["version"].strip()
        ):
            raise StrictGateError("real runtime version is missing")
    else:
        if runtime.get("visual_capture_required") is True:
            raise StrictGateError("visual capture cannot be required without runtime")

    artifact_paths = _validate_artifacts(
        root,
        _require(manifest, "artifacts", "delivery"),
        require_tracked=require_tracked,
    )
    capture = runtime.get("visual_capture_path")
    if runtime.get("visual_capture_required") is True:
        if (
            not isinstance(capture, str)
            or Path(capture).as_posix() not in artifact_paths
        ):
            raise StrictGateError("required real visual capture is not in artifacts")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--root", type=Path, default=ROOT)
    stage_parser = subparsers.add_parser("stage")
    stage_parser.add_argument("stage_id")
    stage_parser.add_argument("ack", type=Path)
    stage_parser.add_argument("--root", type=Path, default=ROOT)
    delivery_parser = subparsers.add_parser("delivery")
    delivery_parser.add_argument("manifest", type=Path)
    delivery_parser.add_argument("--root", type=Path, default=ROOT)
    all_parser = subparsers.add_parser("all")
    all_parser.add_argument("stage_id")
    all_parser.add_argument("ack", type=Path)
    all_parser.add_argument("manifest", type=Path)
    all_parser.add_argument("--root", type=Path, default=ROOT)

    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            validate_plan_lock(args.root, require_tracked=True)
        elif args.command == "stage":
            validate_stage_ack(
                args.ack, args.stage_id, root=args.root, require_tracked=True
            )
        elif args.command == "delivery":
            validate_delivery_manifest(
                args.manifest,
                root=args.root,
                require_tracked=True,
            )
        else:
            validate_stage_ack(
                args.ack, args.stage_id, root=args.root, require_tracked=True
            )
            validate_delivery_manifest(args.manifest, root=args.root)
    except StrictGateError as exc:
        print(f"STRICT_GATE=BLOCKED reason={exc}", file=sys.stderr)
        return 2
    print(f"STRICT_GATE=PASS command={args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
