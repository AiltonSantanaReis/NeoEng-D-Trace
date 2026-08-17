"""Functional contracts for the approved application icon integration."""

from __future__ import annotations

import hashlib
import sys
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication

import src.core.app_icon as core_app_icon
import src.ui.app_icon as ui_app_icon
from src.core.app_icon import application_icon_path
from src.models.scene import Scene
from src.ui.app_icon import application_icon
from src.ui.main_window import MainWindow
from tools.package_windows_msi import _write_wix_source

ROOT = Path(__file__).resolve().parents[1]
ICON_SOURCE = ROOT / "assets" / "branding" / "neoeng-d-trace-icon-source.png"
ICON_PATH = ROOT / "assets" / "branding" / "neoeng-d-trace-icon.ico"
EXPECTED_ICON_SIZES = {(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)}


class _ConfigStub:
    def get(self, key, default=None):
        return default


def test_approved_source_and_derived_icon_are_versioned_and_valid() -> None:
    assert ICON_SOURCE.is_file()
    assert ICON_PATH.is_file()
    assert (
        hashlib.sha256(ICON_SOURCE.read_bytes()).hexdigest()
        == "17dde3dc0d616cef8927403cb3b2b15aa818960776605eb2a7d2b99b8e5adedc"
    )

    with Image.open(ICON_SOURCE) as source:
        assert source.size == (878, 810)
        assert source.convert("RGBA").getchannel("A").getbbox() is not None
    with Image.open(ICON_PATH) as icon:
        assert icon.format == "ICO"
        assert icon.info["sizes"] == EXPECTED_ICON_SIZES


def test_runtime_loads_icon_and_main_window_exposes_it() -> None:
    QApplication.instance() or QApplication([])
    assert application_icon_path() == ICON_PATH
    assert not application_icon().isNull()

    window = MainWindow(Scene(), _ConfigStub())
    assert not window.windowIcon().isNull()
    window.close()


def test_frozen_bundle_path_is_preferred(monkeypatch, tmp_path: Path) -> None:
    frozen_icon = tmp_path / "assets" / "branding" / ICON_PATH.name
    frozen_icon.parent.mkdir(parents=True)
    shutil.copyfile(ICON_PATH, frozen_icon)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert application_icon_path() == frozen_icon


def test_missing_icon_fails_closed(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    monkeypatch.setattr(
        core_app_icon,
        "ICON_RELATIVE_PATH",
        Path("assets") / "branding" / "missing.ico",
    )

    with pytest.raises(FileNotFoundError, match="application icon is missing"):
        application_icon_path()


def test_invalid_qt_icon_fails_closed(monkeypatch, tmp_path: Path) -> None:
    invalid_icon = tmp_path / "invalid.ico"
    invalid_icon.write_bytes(b"not-an-icon")
    monkeypatch.setattr(ui_app_icon, "application_icon_path", lambda: invalid_icon)

    QApplication.instance() or QApplication([])
    with pytest.raises(ValueError, match="Unable to load application icon"):
        application_icon()

def test_wix_shortcut_references_installed_icon(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "NeoEng-D-Trace.exe").write_bytes(b"gui")
    icon_destination = bundle / "assets" / "branding" / ICON_PATH.name
    icon_destination.parent.mkdir(parents=True)
    shutil.copyfile(ICON_PATH, icon_destination)

    source = tmp_path / "main.wxs"
    count = _write_wix_source(bundle, source, "a" * 36)
    assert count == 2

    namespace = {"wix": "http://wixtoolset.org/schemas/v4/wxs"}
    root = ET.parse(source).getroot()
    shortcut = root.find(".//wix:Shortcut", namespace)
    assert shortcut is not None
    assert shortcut.attrib["Icon"] == "NeoEngDTraceIcon.ico"
    icon = shortcut.find("wix:Icon", namespace)
    assert icon is not None
    assert icon.attrib == {
        "Id": "NeoEngDTraceIcon.ico",
        "SourceFile": "assets/branding/neoeng-d-trace-icon.ico",
    }


def test_pyinstaller_spec_bundles_icon_and_sets_gui_executable_icon() -> None:
    spec = (ROOT / "packaging" / "NeoEng-D-Trace.spec").read_text(encoding="utf-8")
    assert 'icon_path = repository_root / "assets" / "branding"' in spec
    assert 'datas=[(str(icon_path), "assets/branding")]' in spec
