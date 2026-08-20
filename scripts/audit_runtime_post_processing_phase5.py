"""Run the fail-closed reproducibility audit for runtime post-processing."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from src.runtime.post_processing import (
    POST_PROCESSING_BACKEND,
    PostProcessingCapabilityError,
    PostProcessingDocumentV1,
    PostProcessingEffectRecord,
    PostProcessingFallbackRecord,
    PostProcessingPreviewError,
    PostProcessingRuntime,
    PostProcessingSourceBindingRecord,
    PostProcessingValidationError,
    load_post_processing_runtime_export,
    load_post_processing_runtime_export_bytes,
    save_post_processing_runtime_export,
    serialize_post_processing_runtime_export,
    verify_post_processing_source_binding,
)
from tools.evidence_integrity import digest_path, write_json_lf

ROOT = Path(__file__).resolve().parents[1]
MAX_REPORT_BYTES = 2_000_000
HOST_PATH_RE = re.compile(
    r"(?:[A-Za-z]:[\\/](?:Users|home)[\\/]|/(?:Users|home)/|\\\\[^\\/]+[\\/])"
)


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _source_state() -> dict[str, Any]:
    status = _git("status", "--porcelain")
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "worktree_clean": not bool(status),
    }


def _effect(
    effect_id: str,
    kind: str,
    order: int,
    parameters: dict[str, object],
    *,
    enabled: bool = True,
) -> PostProcessingEffectRecord:
    return PostProcessingEffectRecord(
        id=effect_id,
        kind=kind,
        order=order,
        enabled=enabled,
        parameters=parameters,
    )


def _document(*, fallback_mode: str = "cpu-preview") -> PostProcessingDocumentV1:
    return PostProcessingDocumentV1(
        source=PostProcessingSourceBindingRecord(sha256="a" * 64),
        fallback=PostProcessingFallbackRecord(
            mode=fallback_mode,
            reason="The requested backend has no native Stage 5 adapter.",
        ),
        effects=[
            _effect("vignette", "vignette", 20, {"amount": 0.5, "radius": 0.5}),
            _effect("exposure", "exposure", 10, {"stops": 1.0}),
            _effect(
                "disabled-gray",
                "grayscale",
                30,
                {"amount": 1.0},
                enabled=False,
            ),
        ],
    )


def _image() -> np.ndarray:
    return np.array(
        [
            [[0.2, 0.4, 0.6, 0.25], [0.8, 0.3, 0.1, 0.5]],
            [[0.1, 0.7, 0.2, 0.75], [0.4, 0.5, 0.9, 1.0]],
        ],
        dtype=np.float64,
    )


def _files_index(root: Path) -> dict[str, dict[str, Any]]:
    return {
        path.relative_to(root).as_posix(): digest_path(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "artifact-index.json"
    }


def _privacy_leaks(root: Path) -> list[str]:
    leaks: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".json", ".md", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if HOST_PATH_RE.search(text) or str(ROOT).replace("\\", "/") in text:
            leaks.append(path.relative_to(root).as_posix())
    return leaks


def run(output: Path) -> dict[str, Any]:
    output = output.resolve()
    if output.exists():
        raise FileExistsError(
            f"output must be a new directory; refusing to overwrite: {output.name}"
        )
    source = _source_state()
    checks: dict[str, bool] = {
        "source_tree_clean": source["worktree_clean"],
        "canonical_sidecar_roundtrip": False,
        "source_binding_is_hash_bound": False,
        "ordered_effects_are_deterministic": False,
        "disabled_effect_is_reported": False,
        "alpha_is_preserved": False,
        "limits_are_enforced": False,
        "fallback_is_explicit": False,
        "atomic_persistence_preserves_previous_bytes": False,
        "privacy": False,
    }

    with tempfile.TemporaryDirectory(prefix="neoeng-stage5-post-processing-") as temp:
        staging = Path(temp)
        document = _document()
        raw = serialize_post_processing_runtime_export(document)
        checks["canonical_sidecar_roundtrip"] = (
            load_post_processing_runtime_export_bytes(raw) == document
        )

        bound = document.model_copy(
            update={
                "source": PostProcessingSourceBindingRecord(
                    sha256=hashlib.sha256(b"source").hexdigest()
                )
            }
        )
        try:
            verify_post_processing_source_binding(bound, b"source")
            verify_post_processing_source_binding(bound, b"different-source")
        except PostProcessingValidationError:
            checks["source_binding_is_hash_bound"] = True

        runtime = PostProcessingRuntime()
        runtime.load_manifest(document)
        first = runtime.preview(_image())
        second = runtime.preview(_image())
        checks["ordered_effects_are_deterministic"] = (
            first.applied_effect_ids == ("exposure", "vignette")
            and first.output_sha256 == second.output_sha256
            and np.array_equal(first.image, second.image)
        )
        checks["disabled_effect_is_reported"] = first.skipped_effect_ids == (
            "disabled-gray",
        )
        checks["alpha_is_preserved"] = np.array_equal(
            first.image[:, :, 3], _image()[:, :, 3]
        )

        limits = _document()
        try:
            _effect("invalid", "box_blur", 0, {"radius": 9})
        except ValueError:
            checks["limits_are_enforced"] = True
        try:
            runtime.preview(np.zeros((0, 2, 4), dtype=np.float64))
        except PostProcessingPreviewError:
            checks["limits_are_enforced"] = checks["limits_are_enforced"]
        del limits

        degraded = runtime.preview(_image(), backend="godot")
        checks["fallback_is_explicit"] = (
            degraded.compatibility == "degraded"
            and degraded.backend == POST_PROCESSING_BACKEND
            and bool(degraded.fallback_reason)
        )
        rejected = PostProcessingRuntime()
        rejected.load_manifest(_document(fallback_mode="reject"))
        try:
            rejected.preview(_image(), backend="unity")
        except PostProcessingCapabilityError:
            checks["fallback_is_explicit"] = checks["fallback_is_explicit"]

        destination = staging / "post-processing.json"
        save_post_processing_runtime_export(document, destination)
        previous_bytes = destination.read_bytes()
        invalid_payload = document.model_dump(mode="json")
        invalid_payload["effects"][0]["parameters"]["unexpected"] = 1.0
        try:
            save_post_processing_runtime_export(
                invalid_payload, destination  # type: ignore[arg-type]
            )
        except PostProcessingValidationError:
            checks["atomic_persistence_preserves_previous_bytes"] = (
                load_post_processing_runtime_export(destination) == document
                and destination.read_bytes() == previous_bytes
            )

        write_json_lf(staging / "post-processing-sidecar.json", json.loads(raw))
        leaks = _privacy_leaks(staging)
        checks["privacy"] = not leaks
        report = {
            "schema_version": 1,
            "stage": "runtime-post-processing-phase5",
            "status": "PASS" if all(checks.values()) else "FAIL",
            "source": source,
            "environment": {"platform": platform.platform(), "python": sys.version},
            "backend": {"native": POST_PROCESSING_BACKEND, "engine_adapters": []},
            "commands": [
                (
                    "python scripts/audit_runtime_post_processing_phase5.py "
                    "--output <new-directory>"
                ),
                "python -m pytest -q tests/test_stage5_runtime_post_processing.py",
                "python -m pytest --cov=src --cov-branch --cov-fail-under=90",
            ],
            "checks": checks,
            "contract": {
                "format_id": document.format_id,
                "schema_version": document.schema_version,
                "algorithm_version": document.algorithm_version,
                "document_sha256": hashlib.sha256(raw).hexdigest(),
                "serialized_bytes": len(raw),
                "effect_count": len(document.effects),
                "effect_order": [
                    effect.order
                    for effect in sorted(document.effects, key=lambda item: item.order)
                ],
            },
            "privacy_leaks": leaks,
            "limitations": [
                (
                    "The implemented native backend is a deterministic CPU preview, "
                    "not GPU rasterization."
                ),
                (
                    "Godot and Unity post-processing adapters are not implemented "
                    "in this phase."
                ),
                (
                    "VRAM, driver-specific FPS and backend-specific rendering "
                    "remain untested."
                ),
                (
                    "The phase is not approved until full repository gates, "
                    "tracked-byte validation, CI and post-merge validation pass."
                ),
            ],
        }
        report_path = staging / "stage5-runtime-post-processing-report.json"
        write_json_lf(report_path, report)
        if report_path.stat().st_size > MAX_REPORT_BYTES:
            raise ValueError(
                "post-processing audit report exceeds the report size limit"
            )
        output.mkdir(parents=True)
        for path in staging.iterdir():
            (output / path.name).write_bytes(path.read_bytes())

    write_json_lf(
        output / "artifact-index.json",
        {
            "schema_version": 1,
            "stage": "runtime-post-processing-phase5",
            "files": _files_index(output),
        },
    )
    return report


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = run(args.output)
    except Exception as exc:
        print(f"RUNTIME_POST_PROCESSING_PHASE5=FAIL {type(exc).__name__}: {exc}")
        return 1
    print(
        json.dumps(
            {"status": report["status"], "checks": report["checks"]}, sort_keys=True
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
