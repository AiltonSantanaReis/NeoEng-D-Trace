from __future__ import annotations

import pytest
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

from src.models.scene import Scene
from src.ui.icon_library import ICON_SPECS, TOOL_ICON_KEYS, configure_action, icon_for
from src.ui.main_window import MainWindow


class _ConfigStub:
    def get(self, key, default=None):
        return default


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def test_icon_catalog_is_embedded_and_complete(qt_app):
    expected = {
        "open",
        "open_image",
        "save",
        "save_as",
        "export",
        "undo",
        "redo",
        "collision",
        "clean",
        "fit",
        "zoom_100",
        "lit",
        "xray_1",
        "xray_2",
        "xray_3",
        "gizmo",
        "focus",
        "language",
        "settings",
        "grid",
        "snap",
        "scenario",
        "validation",
        "collider_edit",
        *TOOL_ICON_KEYS.values(),
    }
    assert expected <= set(ICON_SPECS)
    for key in expected:
        spec = ICON_SPECS[key]
        assert spec.svg_body
        assert "assets/" not in spec.svg_body
        assert not icon_for(key).isNull()
        assert icon_for(key).availableSizes()


def test_action_fallback_keeps_text_when_icon_rendering_fails(qt_app, monkeypatch):
    action = QAction("Visible textual fallback")

    def broken_icon(_key):
        raise RuntimeError("synthetic renderer failure")

    monkeypatch.setattr("src.ui.icon_library.icon_for", broken_icon)
    configure_action(action, "save")

    assert action.text() == "Visible textual fallback"
    assert action.icon().isNull()
    assert action.property("iconFallback") is True
    assert action.property("accessibleName") == "save"


def test_main_window_actions_and_tools_have_icons_and_accessible_text(qt_app):
    window = MainWindow(Scene(), _ConfigStub())

    actions = (
        window.open_project_action,
        window.open_image_action,
        window.save_project_action,
        window.save_project_as_action,
        window.act_export,
        window.act_export_collision_json,
        window.act_export_collision_txt,
        window.act_fit,
        window.act_100,
        window.act_lit,
        window.act_xray1,
        window.act_xray2,
        window.act_xray3,
        window.act_clean,
        window.undo_action,
        window.redo_action,
        window.act_snap,
        window.act_gizmo,
        window.settings_action,
        window.language_action,
    )
    for action in actions:
        assert not action.icon().isNull(), action.objectName()
        assert action.text()
        assert action.toolTip()
        assert action.property("accessibleName")
        assert action.property("iconFallback") is False

    for widget in (
        window.collision_panel.batch_test_btn,
        window.collision_panel.export_btn,
        window.collision_panel.auto_gen_btn,
    ):
        assert not widget.icon().isNull()
        assert widget.text()
        assert widget.toolTip()
        assert widget.accessibleName()
        assert widget.property("iconFallback") is False

    assert window.top_command_contract.physical_toolbar_required is False
    assert window.top_command_contract.group_names() == (
        "file",
        "edit",
        "view",
        "export",
        "context",
        "render",
    )
    assert window.reference_top_toolbar.iconSize() == QSize(24, 24)
    for button in window.tool_palette.tool_buttons.values():
        assert not button.icon().isNull()
        assert button.text()
        assert button.toolTip()
        assert button.accessibleName()
        assert button.property("iconFallback") is False
        assert button.minimumWidth() <= window.tool_palette.minimumWidth()

    for widget, key in (
        (window.collision_panel.batch_test_btn, "collision_test"),
        (window.collision_panel.export_btn, "export"),
        (window.collision_panel.auto_gen_btn, "collision_auto_generate"),
    ):
        assert widget.property("iconKey") == key
        assert widget.iconSize() == QSize(20, 20)
        assert all(ord(character) <= 0xFFFF for character in widget.text())

    assert window.reference_tool_palette.iconSize() == QSize(24, 24)
    window.set_language("pt")
    assert window.open_project_action.text()
    assert window.act_gizmo.text() == "Eixo"
    assert window.language_action.text() == "Idioma"
    assert window.act_portuguese.text() == "Português"
    assert all(
        not button.icon().isNull()
        for button in window.tool_palette.tool_buttons.values()
    )
    window.close()
