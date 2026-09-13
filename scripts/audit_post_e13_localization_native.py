"""Native PT-BR localization and context-menu evidence for the canonical editor.

This audit deliberately keeps the default Qt platform.  It opens the same
canonical scenario editor used by the application, displays native menus and
hover feedback, captures the visible screen, and records the action metadata
that was actually attached to the widgets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QToolTip, QWidget

from scripts.audit_post_e13_native_flow import AuditConfig, _write_fixture_image
from src.core.commands import CommandManager
from src.core.scenario_authoring import ScenarioAuthoringState
from src.models.scene import Scene
from src.ui.main_window import MainWindow
from src.ui.theme_qss import QSS


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _settle(app: QApplication, milliseconds: int = 180) -> None:
    app.processEvents()
    QTest.qWait(milliseconds)
    app.processEvents()


def _save_screen(app: QApplication, path: Path) -> None:
    screen = app.primaryScreen()
    if screen is None or not screen.grabWindow(0).save(str(path), "PNG"):
        raise RuntimeError(f"could not save native screen capture: {path}")


def _action_record(action) -> dict[str, object]:
    return {
        "text": action.text(),
        "tooltip": action.toolTip(),
        "status_tip": action.statusTip(),
        "enabled": action.isEnabled(),
        "visible": action.isVisible(),
    }


def _visible_widget_metadata(root: QWidget) -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    for widget in (root, *root.findChildren(QWidget)):
        if widget is not root and not widget.isVisibleTo(root):
            continue
        tooltip = widget.toolTip()
        description = widget.accessibleDescription()
        if tooltip or description:
            values.append(
                {
                    "object_name": widget.objectName(),
                    "class": widget.__class__.__name__,
                    "tooltip": tooltip,
                    "accessible_description": description,
                }
            )
    return values


def run(output: Path) -> dict[str, object]:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    fixture = output / "fixture"
    fixture.mkdir(parents=True, exist_ok=True)
    project = fixture / "localization.ndtproj"
    image = fixture / "scene.png"
    project.write_bytes(b"post-e13-localization-fixture-v1\n")
    _write_fixture_image(image)

    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image_path = str(image)
    scene.add_object(
        "localization_object",
        [(0, 0), (640, 0), (640, 360), (0, 360)],
        layer_id="layer_default",
    )
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    main = MainWindow(scene, AuditConfig("pt"))
    main._project_path = project
    main.scenario_authoring.bind_project(project)
    main.scenario_authoring.reset()
    main.show()
    main.open_scenario_editor()
    editor = main.scenario_editor_window
    if editor is None:
        raise RuntimeError("canonical scenario editor did not open")
    editor.resize(QSize(1500, 980))
    editor.show()
    editor.raise_()
    editor.activateWindow()
    _settle(app, 500)

    captures = output / "captures"
    captures.mkdir(parents=True, exist_ok=True)
    records: dict[str, object] = {
        "language": editor.current_lang,
        "qt_platform": os.environ.get("QT_QPA_PLATFORM", "native-default"),
        "native_window": True,
        "events": [],
    }

    def capture_screen(name: str, action: str) -> None:
        path = captures / name
        _save_screen(app, path)
        records["events"].append(
            {
                "action": action,
                "capture": name,
                "sha256": _digest(path),
            }
        )

    capture_screen("01-pt-editor.png", "canonical editor opened in PT-BR")

    view_button = editor._toolbar_menu_buttons["view"]
    view_menu = view_button.menu()
    if view_menu is None:
        raise RuntimeError("canonical view menu is missing")
    view_menu.popup(view_button.mapToGlobal(QPoint(0, view_button.height())))
    _settle(app)
    if not view_menu.isVisible():
        raise RuntimeError("canonical PT-BR view menu did not become visible")
    records["view_menu_pt"] = [_action_record(action) for action in view_menu.actions()]
    capture_screen("02-pt-view-menu.png", "open canonical Visualizar menu")
    view_menu.close()

    viewport = editor.professional_viewport
    if viewport is None:
        raise RuntimeError("canonical professional viewport is missing")
    context_menu = viewport._build_context_menu(None)
    context_menu.popup(viewport.mapToGlobal(QPoint(210, 180)))
    _settle(app)
    if not context_menu.isVisible():
        raise RuntimeError("canonical PT-BR context menu did not become visible")
    records["context_menu_pt"] = [
        _action_record(action) for action in context_menu.actions()
    ]
    capture_screen("03-pt-viewport-context-menu.png", "open canonical viewport context menu")
    context_menu.close()

    inspector = editor.professional_inspector
    if inspector is None:
        raise RuntimeError("canonical professional inspector is missing")
    inspector_scroll = editor.professional_inspector_scroll
    if inspector_scroll is None:
        raise RuntimeError("canonical professional inspector scroll area is missing")
    inspector_scroll.ensureWidgetVisible(inspector.fit_all_button)
    _settle(app)
    if not inspector.fit_all_button.isVisibleTo(editor):
        raise RuntimeError("canonical PT-BR fit-all control is not visible")
    hover_pos = inspector.fit_all_button.mapToGlobal(inspector.fit_all_button.rect().center())
    QCursor.setPos(hover_pos)
    for _ in range(10):
        _settle(app, 180)
        if QToolTip.isVisible():
            break
    tooltip = inspector.fit_all_button.toolTip()
    automatic_hover_visible = QToolTip.isVisible()
    display_mode = "cursor-hover"
    if not automatic_hover_visible:
        # The native cursor hover is not deterministic when this source harness
        # runs behind a host desktop.  Keep that fact in the manifest, then
        # render the same native Qt tooltip explicitly so the localized pixels
        # are still captured without pretending the hover trigger was proven.
        QToolTip.showText(hover_pos, tooltip, inspector.fit_all_button)
        _settle(app, 180)
        display_mode = "native-tooltip-explicit"
    records["hover_pt"] = {
        "object_name": inspector.fit_all_button.objectName(),
        "tooltip": tooltip,
        "automatic_hover_visible": automatic_hover_visible,
        "display_mode": display_mode,
        "tooltip_visible": QToolTip.isVisible(),
    }
    if not tooltip or "enquadrar" not in tooltip.casefold():
        raise RuntimeError(f"unexpected PT-BR fit tooltip: {tooltip!r}")
    capture_screen("04-pt-fit-tooltip.png", "hover canonical Enquadrar Tudo control")
    QToolTip.hideText()

    records["visible_hover_metadata_pt"] = _visible_widget_metadata(editor)
    editor.update_language("en")
    _settle(app)
    records["language_switch_en"] = {
        "language": editor.current_lang,
        "view_menu": [
            _action_record(action) for action in view_menu.actions()
        ],
    }
    editor.update_language("pt")
    _settle(app)
    records["language_switch_back_pt"] = {
        "language": editor.current_lang,
        "view_menu": [
            _action_record(action) for action in view_menu.actions()
        ],
    }
    capture_screen("05-pt-editor-after-language-roundtrip.png", "restore PT-BR after language round-trip")

    records.update(
        {
            "status": "PASS",
            "scope": "canonical scenario editor PT-BR menus, context menu, hover and language round-trip",
            "source_commit": __import__("subprocess").check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
            ).strip(),
        }
    )
    (output / "manifest.json").write_text(
        json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    editor.close()
    main.close()
    app.processEvents()
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
