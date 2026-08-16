from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "integrations" / "unity" / "package" / "com.neoeng.dtrace"
OUT = ROOT / "docs" / "evidence" / "artifacts" / "unity-package-stage5-2026-08-16"
METHOD = "NeoEng.DTrace.Editor.PackageDiagnostics.RunHeadless"


def _discover_unity() -> tuple[Path, str]:
    roots = []
    for variable in ("ProgramFiles", "ProgramW6464", "ProgramFiles(x86)"):
        value = os.environ.get(variable)
        if value:
            roots.append(Path(value) / "Unity" / "Hub" / "Editor")
    roots.extend(
        [
            Path("C:/Program Files/Unity/Hub/Editor"),
            Path("C:/Program Files (x86)/Unity/Hub/Editor"),
        ]
    )
    candidates: list[tuple[Path, str]] = []
    for root in roots:
        if not root.is_dir():
            continue
        for version_dir in root.iterdir():
            executable = version_dir / "Editor" / "Unity.exe"
            if executable.is_file():
                candidates.append((executable, version_dir.name))
    if not candidates:
        raise RuntimeError("Unity Editor executable was not found")
    preferred = [item for item in candidates if item[1] == "6000.5.7f1"]
    return sorted(preferred or candidates, key=lambda item: item[1], reverse=True)[0]


def _sanitize(text: str, temporary_root: Path) -> str:
    value = text.replace(str(temporary_root), "<local-path>")
    value = value.replace(str(ROOT), "<repo>")
    value = value.replace(str(PACKAGE_ROOT), "<package>")
    value = re.sub(r"[A-Za-z]:[\\/][^\r\n\"]+", "<local-path>", value)
    value = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "<network-address>", value)
    value = re.sub(
        r"(?im)^(\s*(?:Machine Id|Session Id|Correlation Id|External correlation Id):).*$",
        r"\1 <redacted>",
        value,
    )
    return value


def _write_project(project: Path, package_path: Path, unity_version: str) -> None:
    (project / "ProjectSettings").mkdir(parents=True)
    (project / "Packages").mkdir(parents=True)
    (project / "Assets").mkdir(parents=True)
    (project / "ProjectSettings" / "ProjectVersion.txt").write_text(
        f"m_EditorVersion: {unity_version}\n", encoding="utf-8", newline="\n"
    )
    relative_package = os.path.relpath(package_path, project / "Packages").replace(
        "\\", "/"
    )
    manifest = {"dependencies": {"com.neoeng.dtrace": f"file:{relative_package}"}}
    (project / "Packages" / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def _run_unity(
    executable: Path,
    project: Path,
    report: Path,
    log: Path,
    temporary_root: Path,
) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["NEOENG_STAGE5_REPORT"] = str(report)
    command = [
        str(executable),
        "-batchmode",
        "-nographics",
        "-quit",
        "-projectPath",
        str(project),
        "-executeMethod",
        METHOD,
        "-logFile",
        str(log),
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    output = completed.stdout + completed.stderr
    if log.is_file():
        output += "\n" + log.read_text(encoding="utf-8", errors="replace")
    return {
        "returncode": completed.returncode,
        "marker_success": "UNITY_NATIVE_PACKAGE_STAGE5=SUCCESS" in output,
        "marker_failure": "UNITY_NATIVE_PACKAGE_STAGE5=FAILURE" in output,
        "output": _sanitize(output, temporary_root),
    }


def _digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _load_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"Unity did not produce the expected report: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_success(run: dict[str, Any], report: dict[str, Any]) -> None:
    if run["returncode"] != 0 or not run["marker_success"] or not report["Success"]:
        raise RuntimeError("Unity positive package validation failed")
    if not all(check["Success"] for check in report["Checks"]):
        raise RuntimeError("Unity positive package validation contains a failed check")


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unity", type=Path)
    args = parser.parse_args()
    executable, unity_version = (
        (args.unity, args.unity.parents[1].name) if args.unity else _discover_unity()
    )
    if not executable.is_file():
        raise RuntimeError("the requested Unity executable is not a regular file")
    if not PACKAGE_ROOT.is_dir():
        raise RuntimeError("Unity UPM package directory is missing")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    with tempfile.TemporaryDirectory(
        prefix="neoeng-dtrace-stage5-", ignore_cleanup_errors=True
    ) as temporary:
        temporary_root = Path(temporary)
        first_project = temporary_root / "positive-one"
        repeat_project = temporary_root / "positive-two"
        negative_package = temporary_root / "negative-package"
        negative_project = temporary_root / "negative-project"
        shutil.copytree(PACKAGE_ROOT, negative_package)
        (negative_package / "forbidden.exe").write_text(
            "negative fixture\n", encoding="utf-8", newline="\n"
        )

        _write_project(first_project, PACKAGE_ROOT, unity_version)
        _write_project(repeat_project, PACKAGE_ROOT, unity_version)
        _write_project(negative_project, negative_package, unity_version)

        first_report_path = temporary_root / "first-report.json"
        repeat_report_path = temporary_root / "repeat-report.json"
        negative_report_path = temporary_root / "negative-report.json"
        first_log = temporary_root / "first.log"
        repeat_log = temporary_root / "repeat.log"
        negative_log = temporary_root / "negative.log"

        first_run = _run_unity(
            executable, first_project, first_report_path, first_log, temporary_root
        )
        first_report = _load_report(first_report_path)
        _assert_success(first_run, first_report)

        repeat_run = _run_unity(
            executable, repeat_project, repeat_report_path, repeat_log, temporary_root
        )
        repeat_report = _load_report(repeat_report_path)
        _assert_success(repeat_run, repeat_report)
        if first_report_path.read_bytes() != repeat_report_path.read_bytes():
            raise RuntimeError(
                "repeated Unity package validation was not deterministic"
            )

        negative_run = _run_unity(
            executable,
            negative_project,
            negative_report_path,
            negative_log,
            temporary_root,
        )
        negative_report = _load_report(negative_report_path)
        if (
            negative_run["returncode"] == 0
            or not negative_run["marker_failure"]
            or negative_report["Success"]
        ):
            raise RuntimeError(
                "Unity negative source-only validation did not fail closed"
            )

        (OUT / "stage5-report.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "stage": 5,
                    "status": "SUCCESS",
                    "engine": "unity",
                    "unity_version": unity_version,
                    "package_name": first_report["PackageName"],
                    "package_version": first_report["PackageVersion"],
                    "installation": "local-file-upm",
                    "editor_assembly": "LOADED",
                    "positive": {
                        "returncode": first_run["returncode"],
                        "marker": "UNITY_NATIVE_PACKAGE_STAGE5=SUCCESS",
                        "report": first_report,
                    },
                    "repeat": {
                        "returncode": repeat_run["returncode"],
                        "marker": "UNITY_NATIVE_PACKAGE_STAGE5=SUCCESS",
                        "report_identical": True,
                    },
                    "negative": {
                        "returncode": negative_run["returncode"],
                        "marker": "UNITY_NATIVE_PACKAGE_STAGE5=FAILURE",
                        "source_only_violation_rejected": True,
                        "report": negative_report,
                    },
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        newline="\n",
        )
        (OUT / "stage5-report-repeat.json").write_bytes(first_report_path.read_bytes())
        (OUT / "stage5-report-negative.json").write_bytes(
            negative_report_path.read_bytes()
        )
        (OUT / "package.json").write_bytes((PACKAGE_ROOT / "package.json").read_bytes())
        for source, target in (
            (first_log, OUT / "unity-validation.log"),
            (repeat_log, OUT / "unity-validation-repeat.log"),
            (negative_log, OUT / "unity-validation-negative.log"),
        ):
            target.write_text(
                _sanitize(
                    source.read_text(encoding="utf-8", errors="replace"), temporary
                ),
                encoding="utf-8",
            newline="\n",
            )

    time.sleep(1.0)

    files = {
        str(path.relative_to(OUT)).replace("\\", "/"): _digest(path)
        for path in sorted(OUT.rglob("*"))
        if path.is_file()
    }
    (OUT / "stage5-index.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "stage": 5,
                "status": "SUCCESS",
                "engine": "unity",
                "unity_version": unity_version,
                "package_name": "com.neoeng.dtrace",
                "files": files,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("NATIVE_PACKAGE_STAGE5=SUCCESS")
    print(f"UNITY_VERSION={unity_version}")
    print("UPM_INSTALLATION=LOCAL_FILE")
    print("EDITOR_ASSEMBLY=LOADED")
    print("SOURCE_ONLY_NEGATIVE=REJECTED")
    print("REPEAT_VALIDATION=DETERMINISTIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
