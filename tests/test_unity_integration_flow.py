from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QProcess
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QDialog

from scripts.audit_ui_capture import AuditConfig
from src.core.config import ConfigManager
from src.core.operational_limits import MAX_CONFIG_PATH_LENGTH
from src.core.unity_integration import (
    build_unity_integration_snapshot,
    discover_unity_editor_executables,
    discover_unity_hub_executables,
    inspect_executable,
    normalize_external_path,
)
from src.models.scene import Scene
from src.ui.main_window import MainWindow
from src.ui.unity_integration_settings import (
    UnityIntegrationDialog,
    open_unity_integration_settings,
)


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


class _MemoryConfig:
    def __init__(self):
        self.values: dict[str, object] = {}
        self.save_calls = 0

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value

    def save(self):
        self.save_calls += 1


def _fake_unity_installation(root: Path) -> tuple[Path, Path, dict[str, str]]:
    program_files = root / "Program Files"
    hub = program_files / "Unity Hub" / "Unity Hub.exe"
    editor = (
        program_files
        / "Unity"
        / "Hub"
        / "Editor"
        / "6000.5.7f1"
        / "Editor"
        / "Unity.exe"
    )
    hub.parent.mkdir(parents=True)
    editor.parent.mkdir(parents=True)
    hub.write_bytes(b"hub-placeholder")
    editor.write_bytes(b"editor-placeholder")
    environment = {
        "PROGRAMFILES": str(program_files),
        "ProgramW6432": "",
        "PROGRAMFILES(X86)": "",
        "LOCALAPPDATA": str(root / "LocalAppData"),
    }
    return hub, editor, environment


def test_external_path_normalization_is_bounded_and_does_not_read_content(
    tmp_path: Path,
):
    executable = tmp_path / "Unity Hub.exe"
    executable.write_bytes(b"not-read-by-the-preflight")

    normalized = normalize_external_path(str(executable))
    assert normalized == executable.resolve()
    assert inspect_executable(normalized, "hub") == "available"

    assert normalize_external_path("   ") is None
    with pytest.raises(ValueError, match="NUL"):
        normalize_external_path("bad\x00path")
    with pytest.raises(ValueError, match="length limit"):
        normalize_external_path("x" * (MAX_CONFIG_PATH_LENGTH + 1))
    assert inspect_executable(None, "hub") == "not_configured"

    invalid = tmp_path / "not-unity.exe"
    invalid.write_bytes(b"not-a-unity-executable")
    assert inspect_executable(invalid, "hub") == "invalid"


def test_unity_discovery_finds_hub_and_latest_editor_without_launching(
    tmp_path: Path,
):
    hub, editor, environment = _fake_unity_installation(tmp_path)

    hubs = discover_unity_hub_executables(environment)
    editors = discover_unity_editor_executables(environment)

    assert hub in hubs
    assert editor in editors
    snapshot = build_unity_integration_snapshot(environment=environment)
    assert snapshot.hub_path == hub.resolve()
    assert snapshot.editor_path == editor.resolve()
    assert snapshot.hub_state == "available"
    assert snapshot.editor_state == "available"


def test_unity_hub_discovery_deduplicates_environment_and_path_candidates(
    tmp_path: Path,
    monkeypatch,
):
    program_files = tmp_path / "Program Files"
    hub = program_files / "Unity Hub" / "Unity Hub.exe"
    hub.parent.mkdir(parents=True)
    hub.write_bytes(b"hub-placeholder")
    environment = {
        "PROGRAMFILES": str(program_files),
        "ProgramW6432": str(program_files),
        "PROGRAMFILES(X86)": "",
        "LOCALAPPDATA": "",
    }

    monkeypatch.setattr(
        "src.core.unity_integration.shutil.which",
        lambda name: str(hub) if name == "Unity Hub.exe" else None,
    )

    assert discover_unity_hub_executables(environment) == (hub,)


def test_dialog_selection_covers_cancel_invalid_and_valid_paths(
    qt_app,
    tmp_path: Path,
    monkeypatch,
):
    window = MainWindow(Scene(), AuditConfig())
    dialog = UnityIntegrationDialog(window)
    valid_hub = tmp_path / "Unity Hub.exe"
    invalid = tmp_path / "not-unity.exe"
    valid_hub.write_bytes(b"hub-placeholder")
    invalid.write_bytes(b"not-a-unity-executable")
    selected = iter(
        (
            ("", ""),
            ("x" * (MAX_CONFIG_PATH_LENGTH + 1), ""),
            (str(invalid), ""),
            (str(valid_hub), ""),
        )
    )
    warnings: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        "src.ui.unity_integration_settings.QFileDialog.getOpenFileName",
        lambda *_args: next(selected),
    )
    monkeypatch.setattr(
        "src.ui.unity_integration_settings.QMessageBox.warning",
        lambda *args: warnings.append(args),
    )

    try:
        dialog._select_executable("hub")
        dialog._select_executable("hub")
        dialog._select_executable("editor")
        dialog._select_executable("hub")

        assert len(warnings) == 2
        assert dialog.hub_path.text() == str(valid_hub.resolve())
        assert str(invalid) in dialog._format_state("missing", invalid)
        assert str(invalid) in dialog._format_state("invalid", invalid)
    finally:
        dialog.deleteLater()
        window.close()
        qt_app.processEvents()


def test_explicit_missing_path_is_visible_as_missing_not_silently_replaced(
    tmp_path: Path,
):
    missing = tmp_path / "Unity Hub.exe"
    snapshot = build_unity_integration_snapshot(configured_hub=str(missing))
    assert snapshot.hub_path == missing.resolve()
    assert snapshot.hub_state == "missing"


def test_config_round_trip_adds_only_optional_unity_paths(tmp_path: Path):
    config_path = tmp_path / "config.json"
    manager = ConfigManager(str(config_path))
    manager.set("unity_hub_path", str(tmp_path / "Unity Hub.exe"))
    manager.set("unity_editor_path", str(tmp_path / "Unity.exe"))
    manager.save()

    reloaded = ConfigManager(str(config_path))
    assert reloaded.get("unity_hub_path") == str(tmp_path / "Unity Hub.exe")
    assert reloaded.get("unity_editor_path") == str(tmp_path / "Unity.exe")
    assert reloaded.get("language") == "auto"


def test_main_window_exposes_unity_preflight_without_replacing_canonical_actions(
    qt_app,
):
    window = MainWindow(Scene(), AuditConfig())
    try:
        action = window.unity_integration_action
        assert action in window.view_menu.actions()
        assert window.command_registry.action("integration.unity") is action
        assert action.objectName() == "unity_integration_action"
        assert action.property("iconKey") == "unity"
        assert not action.icon().isNull()
        assert action.toolTip()
        assert action.property("accessibleName")
        assert window.settings_action in window.edit_menu.actions()
    finally:
        window.close()
        qt_app.processEvents()


def test_dialog_accepts_real_user_selected_paths_and_persists_locally(
    qt_app,
    tmp_path: Path,
    monkeypatch,
):
    hub, editor, _environment = _fake_unity_installation(tmp_path)
    config = _MemoryConfig()
    window = MainWindow(Scene(), config)

    def accepted(dialog):
        assert isinstance(dialog, UnityIntegrationDialog)
        dialog.hub_path.setText(str(hub))
        dialog.editor_path.setText(str(editor))
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(QDialog, "exec", accepted)
    try:
        open_unity_integration_settings(window)
        assert config.values == {
            "unity_hub_path": str(hub.resolve()),
            "unity_editor_path": str(editor.resolve()),
        }
        assert config.save_calls == 1
        dialog = window.unity_integration_dialog
        assert dialog.hub_status.text().startswith("Found:")
        assert dialog.editor_status.text().startswith("Found:")
        assert "not verified" in dialog.license_status.text()
    finally:
        window.close()
        qt_app.processEvents()


def test_dialog_personal_copy_and_accessible_controls_are_localized(qt_app):
    window = MainWindow(Scene(), AuditConfig())
    try:
        dialog = UnityIntegrationDialog(window)
        dialog.update_language("pt")
        assert dialog.windowTitle() == "Integração do Unity e fluxo de licença"
        assert "Personal" in dialog.personal_flow_label.text()
        assert dialog.hub_browse.accessibleName() or dialog.hub_browse.text()
        assert dialog.hub_path.objectName() == "unity_hub_path"
        assert dialog.editor_path.objectName() == "unity_editor_path"
        assert dialog.buttons.objectName() == "unity_integration_buttons"
        dialog.deleteLater()
    finally:
        window.close()
        qt_app.processEvents()


def test_open_hub_uses_selected_executable_without_shell_or_arguments(
    qt_app,
    tmp_path: Path,
    monkeypatch,
):
    hub, _editor, _environment = _fake_unity_installation(tmp_path)
    window = MainWindow(Scene(), AuditConfig())
    dialog = UnityIntegrationDialog(window)
    dialog.hub_path.setText(str(hub))
    calls: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(
        QProcess,
        "startDetached",
        lambda program, arguments: calls.append((program, list(arguments))) or True,
    )
    try:
        dialog._open_hub()
        assert calls == [(str(hub.resolve()), [])]
        assert "Unity Hub opened" in dialog.status_label.text()
    finally:
        dialog.deleteLater()
        window.close()
        qt_app.processEvents()


def test_dialog_reports_unavailable_hub_failed_launch_and_url(
    qt_app,
    tmp_path: Path,
    monkeypatch,
):
    hub, _editor, _environment = _fake_unity_installation(tmp_path)
    window = MainWindow(Scene(), AuditConfig())
    dialog = UnityIntegrationDialog(window)
    warnings: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        "src.ui.unity_integration_settings.QMessageBox.warning",
        lambda *args: warnings.append(args),
    )
    monkeypatch.setattr(QProcess, "startDetached", lambda *_args: False)
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda _url: False)
    try:
        dialog._open_hub()
        dialog.hub_path.setText(str(hub))
        dialog._open_hub()
        dialog._open_url("https://id.unity.com/")

        assert len(warnings) == 3
        assert "not found" in warnings[0][2].lower()
        assert "failed" in warnings[1][1].lower()
        assert "failed" in warnings[2][1].lower()
    finally:
        dialog.deleteLater()
        window.close()
        qt_app.processEvents()


def test_links_are_delegated_to_desktop_services_without_credentials(
    qt_app, monkeypatch
):
    window = MainWindow(Scene(), AuditConfig())
    dialog = UnityIntegrationDialog(window)
    opened: list[str] = []
    monkeypatch.setattr(
        QDesktopServices,
        "openUrl",
        lambda url: opened.append(url.toString()) or True,
    )
    try:
        dialog._open_url("https://id.unity.com/")
        assert opened == ["https://id.unity.com/"]
    finally:
        dialog.deleteLater()
        window.close()
        qt_app.processEvents()


def test_integration_module_has_no_license_file_or_environment_activation_path():
    source = Path("src/core/unity_integration.py").read_text(encoding="utf-8")
    assert ".ulf" not in source
    assert "UNITY_LICENSE_FILE" not in source
    assert "read_bytes" not in source
    assert "read_text" not in source
    assert "open(" not in source
    assert "QProcess" not in source
