"""Install, exercise, and uninstall a Windows MSI release candidate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from tools.package_windows_msi import sha256_file
from tools.validate_portable_release import validate_bundle


def run_msiexec(arguments: list[str], log_path: Path) -> int:
    executable = Path(os.environ["SystemRoot"]) / "System32" / "msiexec.exe"
    command = [
        str(executable),
        *arguments,
        "/qn",
        "/norestart",
        "/L*V",
        str(log_path),
    ]
    result = subprocess.run(command, check=False, timeout=300)
    return result.returncode


def validate_installer(
    installer: Path,
    output: Path,
    fixture: Path,
) -> dict[str, object]:
    if sys.platform != "win32":
        raise RuntimeError("MSI validation is supported only on Windows")
    if not installer.is_file():
        raise FileNotFoundError(f"installer does not exist: {installer}")
    output.mkdir(parents=True, exist_ok=True)
    install_directory = output / "installed" / "NeoEng-D-Trace"
    if install_directory.exists():
        raise FileExistsError(
            f"validation install directory already exists: {install_directory}"
        )

    user_state = Path(os.environ["LOCALAPPDATA"]) / "NeoEng-D-Trace"
    user_state_preexisted = user_state.exists()
    sentinel = user_state / "stage14-uninstall-preservation.txt"
    if sentinel.exists():
        raise FileExistsError(f"validation sentinel already exists: {sentinel}")

    install_log = output / "msi-install.log"
    uninstall_log = output / "msi-uninstall.log"
    installed = False
    sentinel_created = False
    try:
        install_exit = run_msiexec(
            [
                "/i",
                str(installer),
                f"INSTALLDIR={install_directory}",
            ],
            install_log,
        )
        if install_exit not in (0, 3010):
            raise RuntimeError(f"MSI installation failed with exit code {install_exit}")
        installed = True
        if not (install_directory / "NeoEng-D-Trace.exe").is_file():
            raise AssertionError("installed GUI executable is missing")
        if not (install_directory / "NeoEng-D-Trace-CLI.exe").is_file():
            raise AssertionError("installed CLI executable is missing")

        smoke_output = output / "installed-smoke"
        smoke = validate_bundle(install_directory, smoke_output, fixture)
        user_state.mkdir(parents=True, exist_ok=True)
        sentinel.write_text("preserve-on-uninstall\n", encoding="utf-8")
        sentinel_created = True

        uninstall_exit = run_msiexec(["/x", str(installer)], uninstall_log)
        if uninstall_exit not in (0, 3010):
            raise RuntimeError(
                f"MSI uninstallation failed with exit code {uninstall_exit}"
            )
        installed = False
        remaining = (
            [path for path in install_directory.rglob("*")]
            if install_directory.exists()
            else []
        )
        if remaining:
            raise AssertionError(
                f"MSI uninstall left {len(remaining)} paths in the install directory"
            )
        if not sentinel.is_file():
            raise AssertionError("MSI uninstall removed user state outside install dir")

        result = {
            "schema_version": 1,
            "status": "SUCCESS",
            "installer": installer.name,
            "installer_sha256": sha256_file(installer),
            "install_exit_code": install_exit,
            "uninstall_exit_code": uninstall_exit,
            "checks": [
                "per-user-install",
                "installed-cli-version",
                "installed-headless-project",
                "installed-headless-json",
                "installed-headless-glb",
                "installed-gui-open-close",
                "complete-uninstall",
                "user-state-preserved",
            ],
            "portable_smoke_status": smoke["status"],
        }
        report = output / "installer-validation-report.json"
        report.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(json.dumps(result, sort_keys=True))
        return result
    finally:
        if installed:
            run_msiexec(["/x", str(installer)], uninstall_log)
        if sentinel_created and sentinel.exists():
            sentinel.unlink()
        if not user_state_preexisted and user_state.exists():
            try:
                user_state.rmdir()
            except OSError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--installer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    args = parser.parse_args()
    validate_installer(
        args.installer.resolve(),
        args.output.resolve(),
        args.fixture.resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
