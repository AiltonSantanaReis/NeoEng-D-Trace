"""Reproduce the two missing Unity stage-six failure scenarios.

The historical logs are not reconstructed.  This script copies the current
Unity package into a temporary project and injects the documented defects only
in that copy, then executes the installed Unity Editor in batch mode.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

try:
    from scripts.audit_unity_import_stage6 import (
        PACKAGE_ROOT,
        ROOT,
        assert_positive,
        create_fixture,
        digest,
        discover_unity,
        load_report,
        run_unity,
        write_project,
    )
except ModuleNotFoundError:
    from audit_unity_import_stage6 import (
        PACKAGE_ROOT,
        ROOT,
        assert_positive,
        create_fixture,
        digest,
        discover_unity,
        load_report,
        run_unity,
        write_project,
    )

OUT = (
    ROOT
    / "docs"
    / "evidence"
    / "artifacts"
    / ("unity-import-stage6-reproductions-2026-08-16")
)
IMPORT_METHOD = "NeoEng.DTrace.Editor.UnityImportGenerator.RunHeadlessImport"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_package(destination: Path) -> Path:
    package = destination / "com.neoeng.dtrace"
    shutil.copytree(PACKAGE_ROOT, package)
    return package


def inject_compile_failure(package: Path) -> dict[str, str]:
    source = package / "Editor" / "UnityImportGenerator.cs"
    original = source.read_text(encoding="utf-8")
    expected = "TrimStart('.', '/')"
    replacement = "TrimStart('./')"
    if original.count(expected) != 1:
        raise RuntimeError("expected TrimStart expression was not found exactly once")
    mutated = original.replace(expected, replacement)
    source.write_text(mutated, encoding="utf-8", newline="\n")
    return {
        "file": "Editor/UnityImportGenerator.cs",
        "original_sha256": hashlib.sha256(original.encode("utf-8")).hexdigest(),
        "mutated_sha256": hashlib.sha256(mutated.encode("utf-8")).hexdigest(),
        "transformation": "TrimStart('.', '/') -> TrimStart('./')",
    }


def corrupt_marker_binding(project: Path) -> dict[str, str]:
    prefab = project / "Assets" / "NeoEngGenerated" / "hero.prefab"
    if not prefab.is_file():
        raise RuntimeError("Unity did not create the prefab before corruption")
    prefab_text = prefab.read_text(encoding="utf-8")
    marker_meta = PACKAGE_ROOT / "Runtime" / "NeoEngGeneratedMarker.cs.meta"
    marker_guid_match = re.search(r"guid:\s*([0-9a-f]+)", marker_meta.read_text())
    if marker_guid_match is None:
        raise RuntimeError("marker script GUID was not found")
    marker_guid = marker_guid_match.group(1)
    pattern = re.compile(
        r"m_Script: \{fileID: 11500000, guid: "
        + re.escape(marker_guid)
        + r", type: 3\}"
    )
    mutated, replacements = pattern.subn("m_Script: {fileID: 0}", prefab_text)
    if replacements != 1:
        raise RuntimeError("generated prefab marker binding was not found exactly once")
    prefab.write_text(mutated, encoding="utf-8", newline="\n")
    return {
        "file": "Assets/NeoEngGenerated/hero.prefab",
        "marker_guid": marker_guid,
        "original_sha256": hashlib.sha256(prefab_text.encode("utf-8")).hexdigest(),
        "mutated_sha256": hashlib.sha256(mutated.encode("utf-8")).hexdigest(),
        "transformation": (
            "Unity-generated marker component binding changed to fileID 0"
        ),
    }


def assert_compile_failure(run: dict[str, Any]) -> None:
    output = run["output"]
    if run["returncode"] == 0 or "CS1012" not in output:
        raise RuntimeError("Unity did not reproduce the documented C# compile failure")


def assert_marker_binding_failure(run: dict[str, Any], project: Path) -> dict[str, Any]:
    output = run["output"]
    prefab = project / "Assets" / "NeoEngGenerated" / "hero.prefab"
    prefab_text = (
        prefab.read_text(encoding="utf-8", errors="replace") if prefab.is_file() else ""
    )
    binding_zero = "m_Script: {fileID: 0}" in prefab_text
    if run["returncode"] == 0 or not run["failure_marker"] or not binding_zero:
        raise RuntimeError("Unity did not reject the marker binding reproduction")
    if "no synchronization state" not in output.lower():
        raise RuntimeError("marker binding failure was not observable in Unity output")
    return {
        "prefab": "Assets/NeoEngGenerated/hero.prefab",
        "m_script_file_id_zero": binding_zero,
        "validator_observed_invalid_marker": "no synchronization state"
        in output.lower(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unity", type=Path)
    args = parser.parse_args()
    executable, unity_version = (
        (args.unity, args.unity.parents[1].name) if args.unity else discover_unity()
    )
    if not executable.is_file() or not PACKAGE_ROOT.is_dir():
        raise RuntimeError("Unity executable or package directory is missing")
    if OUT.exists():
        raise RuntimeError(f"output directory already exists: {OUT.name}")
    OUT.mkdir(parents=True)

    with tempfile.TemporaryDirectory(
        prefix="neoeng-dtrace-stage6-reproduction-", ignore_cleanup_errors=True
    ) as temporary:
        temporary_root = Path(temporary)
        compile_package = copy_package(temporary_root / "compile-package")
        marker_package = copy_package(temporary_root / "marker-package")
        compile_input = inject_compile_failure(compile_package)
        marker_input = None

        compile_project = temporary_root / "compile-project"
        marker_project = temporary_root / "marker-project"
        write_project(compile_project, compile_package, unity_version)
        write_project(marker_project, marker_package, unity_version)
        create_fixture(marker_project)

        compile_run = run_unity(
            executable,
            compile_project,
            IMPORT_METHOD,
            temporary_root,
        )
        assert_compile_failure(compile_run)

        marker_initial_report = temporary_root / "marker-initial-report.json"
        marker_initial_run = run_unity(
            executable,
            marker_project,
            IMPORT_METHOD,
            temporary_root,
            marker_initial_report,
        )
        marker_initial_data = load_report(marker_initial_report)
        assert_positive(marker_initial_run, marker_initial_data)
        marker_input = corrupt_marker_binding(marker_project)

        marker_report = temporary_root / "marker-report.json"
        marker_run = run_unity(
            executable,
            marker_project,
            IMPORT_METHOD,
            temporary_root,
            marker_report,
        )
        marker_observation = assert_marker_binding_failure(marker_run, marker_project)

        report = {
            "schema_version": 1,
            "status": "SUCCESS",
            "kind": "real_reproduction",
            "historical_logs_status": "originals_unavailable_reproduction_recorded",
            "engine": "unity",
            "unity_version": unity_version,
            "source_package": {
                "package": "integrations/unity/package/com.neoeng.dtrace",
                "editor_source_sha256": sha256(
                    PACKAGE_ROOT / "Editor" / "UnityImportGenerator.cs"
                ),
                "metadata_source_sha256": sha256(
                    PACKAGE_ROOT / "Runtime" / "NeoEngImportedSpriteMetadata.cs"
                ),
                "marker_source_sha256": sha256(
                    PACKAGE_ROOT / "Runtime" / "NeoEngGeneratedMarker.cs"
                ),
            },
            "cases": {
                "csharp_compile": {
                    "returncode": compile_run["returncode"],
                    "failure_observed": True,
                    "diagnostic": "CS1012",
                    "input_transformation": compile_input,
                    "log": "reproduction-csharp-compile.log",
                },
                "marker_script_binding": {
                    "returncode": marker_run["returncode"],
                    "failure_observed": True,
                    "input_transformation": marker_input,
                    "observation": marker_observation,
                    "log": "reproduction-marker-script-binding.log",
                },
            },
            "limitations": [
                "These are new executions against temporary fault-injected copies.",
                "They do not replace or rewrite the two unavailable historical logs.",
                (
                    "The package source and transformations are identified by hashes "
                    "above."
                ),
            ],
        }
        (OUT / "reproduction-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (OUT / "reproduction-csharp-compile.log").write_text(
            compile_run["output"], encoding="utf-8", newline="\n"
        )
        (OUT / "reproduction-marker-script-binding.log").write_text(
            marker_run["output"], encoding="utf-8", newline="\n"
        )

    files = {
        path.name: digest(path) for path in sorted(OUT.iterdir()) if path.is_file()
    }
    (OUT / "reproduction-index.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "SUCCESS",
                "kind": "real_reproduction",
                "engine": "unity",
                "unity_version": unity_version,
                "files": files,
                "historical_unavailable": [
                    "initial-failure-csharp-compile.log",
                    "initial-failure-marker-script-binding.log",
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("UNITY_STAGE6_REPRODUCTION=SUCCESS")
    print(f"UNITY_VERSION={unity_version}")
    print("CSHARP_COMPILE_FAILURE=REPRODUCED")
    print("MARKER_BINDING_FAILURE=REPRODUCED")
    print("HISTORICAL_LOGS=UNAVAILABLE_ORIGINALS_PRESERVED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
