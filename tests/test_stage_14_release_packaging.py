"""Stage 14 contracts for release packaging and writable runtime state."""

from __future__ import annotations

import json
import struct
from pathlib import Path

import src.core.app_paths as app_paths
import src.launcher as launcher


def test_default_config_path_uses_writable_user_state(
    tmp_path: Path, monkeypatch
) -> None:
    state = tmp_path / "user-state"
    monkeypatch.setattr(app_paths, "default_state_directory", lambda: state)
    assert app_paths.default_config_path() == state / "config.json"


def test_runtime_config_migrates_legacy_without_mutating_it(tmp_path: Path) -> None:
    legacy = tmp_path / "checkout" / "config.json"
    destination = tmp_path / "state" / "config.json"
    legacy.parent.mkdir()
    payload = {
        "config_version": 1,
        "last_folder": None,
        "zoom": 2.0,
        "tool": "polygonal_lasso",
        "window_geometry": None,
        "recent_files": [],
        "default_export_profile": "default",
        "profiles": [],
        "log_level": "INFO",
        "log_to_file": False,
        "log_file_path": None,
        "autosave_enabled": True,
        "autosave_interval_seconds": 60,
    }
    raw = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    legacy.write_bytes(raw)
    manager = launcher.load_runtime_config(config_path=destination, legacy_path=legacy)
    assert manager.path == str(destination)
    assert manager.get("zoom") == 2.0
    assert destination.read_bytes() == raw
    assert legacy.read_bytes() == raw
    assert not list(destination.parent.glob("*.migrating"))


def test_existing_user_config_is_never_overwritten_by_legacy(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.json"
    destination = tmp_path / "state" / "config.json"
    destination.parent.mkdir()
    legacy.write_text('{"zoom": 2.0}', encoding="utf-8")
    destination.write_text('{"zoom": 3.0}', encoding="utf-8")
    manager = launcher.load_runtime_config(config_path=destination, legacy_path=legacy)
    assert manager.get("zoom") == 3.0
    assert destination.read_text(encoding="utf-8") == '{"zoom": 3.0}'


def test_failed_legacy_migration_preserves_source_and_uses_defaults(
    tmp_path: Path, monkeypatch
) -> None:
    legacy = tmp_path / "legacy.json"
    destination = tmp_path / "state" / "config.json"
    legacy.write_text('{"zoom": 2.0}', encoding="utf-8")
    monkeypatch.setattr(
        launcher.os,
        "replace",
        lambda *_: (_ for _ in ()).throw(OSError("replace blocked")),
    )
    manager = launcher.load_runtime_config(config_path=destination, legacy_path=legacy)
    assert manager.get("zoom") == 1.0
    assert legacy.read_text(encoding="utf-8") == '{"zoom": 2.0}'
    assert not destination.exists()
    assert not list(destination.parent.glob("*.migrating"))


def test_packaging_contract_is_versioned() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = (root / "packaging" / "NeoEng-D-Trace.spec").read_text(encoding="utf-8")
    build = (root / "scripts" / "build_windows.ps1").read_text(encoding="utf-8")
    assert 'name="NeoEng-D-Trace"' in spec
    assert 'name="NeoEng-D-Trace-CLI"' in spec
    assert "console=False" in spec
    assert "console=True" in spec
    assert "git status --porcelain --untracked-files=all" in build
    assert build.index("git status --porcelain --untracked-files=all") < build.index(
        "Remove-Item -LiteralPath $releaseRoot -Recurse -Force"
    )
    assert "$releaseRoot.Equals($repositoryRoot" in build
    assert "$releaseRoot.StartsWith($repositoryPrefix" in build
    assert "SkipClean" not in build
    assert '$env:PYTHONHASHSEED = "0"' in build
    assert build.index('$env:PYTHONHASHSEED = "0"') < build.index(
        "pyinstaller --noconfirm"
    )
    assert "package_portable_release.py" in build
    assert "validate_portable_release.py" in build
    assert build.index("validate_portable_release.py") < build.index(
        "package_portable_release.py"
    )
    fixture = root / "tests" / "fixtures" / "release_smoke.ndtproj"
    assert fixture.is_file()
    assert "C:\\\\Users\\\\" not in fixture.read_text(encoding="utf-8")


def test_portable_package_is_deterministic_and_manifested(tmp_path: Path) -> None:
    from tools.package_portable_release import package_portable

    bundle = tmp_path / "NeoEng-D-Trace"
    bundle.mkdir()
    (bundle / "NeoEng-D-Trace.exe").write_bytes(b"gui")
    (bundle / "NeoEng-D-Trace-CLI.exe").write_bytes(b"cli")
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    first_result = package_portable(bundle, first, "a" * 40)
    second_result = package_portable(bundle, second, "a" * 40)

    assert first.read_bytes() == second.read_bytes()
    assert first_result["sha256"] == second_result["sha256"]
    manifest = json.loads(
        (bundle / "release-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["source_commit"] == "a" * 40
    assert manifest["build_environment"]["python"]
    assert manifest["build_environment"]["pyinstaller"] == "6.22.0"
    assert len(manifest["build_inputs"]["poetry_lock_canonical_sha256"]) == 64
    assert len(manifest["build_inputs"]["spec_canonical_sha256"]) == 64
    assert {item["path"] for item in manifest["files"]} == {
        "NeoEng-D-Trace-CLI.exe",
        "NeoEng-D-Trace.exe",
    }


def test_gui_smoke_requires_structured_validation_log(monkeypatch) -> None:
    import pytest

    monkeypatch.setattr("sys.argv", ["neoeng", "--smoke-test-gui"])
    with pytest.raises(SystemExit) as captured:
        launcher.main()
    assert captured.value.code == 2


def test_msi_identifiers_are_stable_and_path_safe() -> None:
    from tools.package_windows_msi import (
        short_directory_name,
        stable_guid,
        stable_identifier,
    )

    assert stable_guid("same") == stable_guid("same")
    assert stable_guid("same") != stable_guid("different")
    assert stable_identifier("cmp", "_internal/PySide6") == stable_identifier(
        "cmp", "_internal/PySide6"
    )
    default = short_directory_name("NeoEng-D-Trace")
    assert default.endswith("|NeoEng-D-Trace")
    assert len(default.split("|", 1)[0]) <= 8


def test_windows_installer_contract_is_fail_closed() -> None:
    root = Path(__file__).resolve().parents[1]
    build = (root / "scripts" / "build_installer.ps1").read_text(encoding="utf-8")
    package = (root / "tools" / "package_windows_msi.py").read_text(encoding="utf-8")
    validate = (root / "tools" / "validate_windows_installer.py").read_text(
        encoding="utf-8"
    )
    portable_validate = (root / "tools" / "validate_portable_release.py").read_text(
        encoding="utf-8"
    )
    engine_validate = (root / "tools" / "validate_engine_exports.py").read_text(
        encoding="utf-8"
    )
    assert "git status --porcelain --untracked-files=all" in build
    assert "source_commit -ne $sourceCommit" in build
    assert "build_windows.ps1" in build
    assert build.index("build_windows.ps1") < build.index("package_windows_msi.py")
    assert "package_windows_msi.py" in build
    assert "validate_windows_installer.py" in build
    assert '"--export-profile"' in portable_validate
    assert '"--fixture-dir"' in engine_validate
    assert '"MSIINSTALLPERUSER", "1"' in package
    assert '"LIMITUI", "1"' in package
    assert '"VersionNT64"' in package
    assert "stable_guid" in package
    assert "complete-uninstall" in validate
    assert "user-state-preserved" in validate
    assert "C:\\Users\\" not in build + package + validate


def test_msi_rejects_portable_manifest_tampering(tmp_path: Path) -> None:
    import pytest

    from tools.package_windows_msi import sha256_file, verify_portable_manifest

    bundle = tmp_path / "bundle"
    bundle.mkdir()
    executable = bundle / "NeoEng-D-Trace.exe"
    executable.write_bytes(b"valid")
    manifest = {
        "files": [
            {
                "path": executable.name,
                "size": executable.stat().st_size,
                "sha256": sha256_file(executable),
            }
        ]
    }
    verify_portable_manifest(bundle, manifest)
    executable.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="size mismatch"):
        verify_portable_manifest(bundle, manifest)


def test_msi_storage_timestamp_normalization_is_structurally_guarded(
    tmp_path: Path,
) -> None:
    import pytest

    from tools.package_windows_msi import normalize_msi_storage_timestamps

    invalid = tmp_path / "invalid.msi"
    invalid.write_bytes(b"not-an-msi")
    with pytest.raises(ValueError, match="Compound File Binary"):
        normalize_msi_storage_timestamps(invalid)

    path = tmp_path / "valid.msi"
    data = bytearray(1152)
    data[:8] = bytes.fromhex("D0CF11E0A1B11AE1")
    struct.pack_into("<H", data, 30, 9)
    struct.pack_into("<I", data, 48, 1)
    root_offset = 1024
    name = "Root Entry".encode("utf-16le") + b"\x00\x00"
    data[root_offset : root_offset + len(name)] = name
    struct.pack_into("<H", data, root_offset + 64, len(name))
    data[root_offset + 66] = 5
    data[root_offset + 100 : root_offset + 116] = bytes(range(16))
    path.write_bytes(data)

    normalize_msi_storage_timestamps(path)

    normalized = path.read_bytes()
    assert normalized[root_offset + 100 : root_offset + 116] == bytes(16)
    assert normalized[:root_offset] == data[:root_offset]
