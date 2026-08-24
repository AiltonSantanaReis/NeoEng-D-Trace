"""Local Stage 9 UI execution audit.

This audit exercises production UI actions, captures real Qt widgets and writes
machine-readable evidence outside the repository by default.  It deliberately
keeps functional checks separate from visual review: visual findings are
fail-closed, while human-only observations remain NOT_CONFIRMED until a human
reviews the generated PNGs.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from PySide6.QtCore import QPoint, QPointF, QRect, QSize  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QMenu, QScrollArea, QWidget  # noqa: E402

from scripts.audit_ui_defect_capture import AuditConfig, fixture_scene  # noqa: E402
from src.ui.main_window import MainWindow  # noqa: E402
from src.ui.theme_qss import QSS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
VIEWPORTS = {
    "compact_1280x720": (1280, 720),
    "compact_1366x768": (1366, 768),
    "desktop_1920x1080": (1920, 1080),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def source_state() -> dict[str, Any]:
    status = _git("status", "--porcelain")
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "worktree_clean": not bool(status),
    }


def settle(app: QApplication) -> None:
    app.processEvents()
    QTest.qWait(180)
    app.processEvents()


def rect_in(widget: QWidget, parent: QWidget) -> QRect:
    point = widget.mapTo(parent, QPoint(0, 0))
    return QRect(point.x(), point.y(), widget.width(), widget.height())


def _has_scroll_ancestor(child: QWidget, root: QWidget) -> bool:
    parent = child.parentWidget()
    while parent is not None and parent is not root:
        if isinstance(parent, QScrollArea):
            return True
        parent = parent.parentWidget()
    return False


def scoped_clipping(widget: QWidget) -> list[dict[str, Any]]:
    """Check only widgets owned by this top-level window.

    ``findChildren`` also sees child top-level windows.  Excluding them avoids
    reporting the dedicated scenario editor as a MainWindow child.
    """

    findings: list[dict[str, Any]] = []
    for child in widget.findChildren(QWidget):
        if child.window() is not widget:
            continue
        if _has_scroll_ancestor(child, widget):
            continue
        if not child.isVisible() or child.width() <= 0 or child.height() <= 0:
            continue
        hint = child.minimumSizeHint()
        if hint.width() > child.width() + 1 or hint.height() > child.height() + 1:
            findings.append(
                {
                    "object": child.objectName() or child.__class__.__name__,
                    "geometry": [child.width(), child.height()],
                    "minimum_size_hint": [hint.width(), hint.height()],
                }
            )
    return findings


def capture(widget: QWidget, path: Path) -> dict[str, Any]:
    pixmap = widget.grab()
    device_pixel_ratio = float(pixmap.devicePixelRatio())
    if not pixmap.save(str(path), "PNG"):
        raise RuntimeError(f"capture failed: {path.name}")
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        pixels = np.asarray(rgba)
        alpha = pixels[:, :, 3]
        border = np.concatenate(
            [pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]], axis=0
        )
        expected_size = (
            round(widget.width() * device_pixel_ratio),
            round(widget.height() * device_pixel_ratio),
        )
        if (image.width, image.height) != expected_size:
            raise RuntimeError(
                f"Qt/PNG dimensions disagree: {path.name}; "
                f"expected={expected_size}; actual={(image.width, image.height)}; "
                f"dpr={device_pixel_ratio}"
            )
        if int(alpha.min()) != 255 or int(alpha.max()) != 255:
            raise RuntimeError(f"alpha contract failed: {path.name}")
        if not np.any(border[:, :3] != 0):
            raise RuntimeError(f"empty PNG border: {path.name}")
        return {
            "file": path.name,
            "width": image.width,
            "height": image.height,
            "logical_size": [widget.width(), widget.height()],
            "device_pixel_ratio": device_pixel_ratio,
            "mode": image.mode,
            "alpha": [int(alpha.min()), int(alpha.max())],
            "bytes": path.stat().st_size,
            "sha256": digest(path),
        }


def annotate(path: Path, boxes: dict[str, QRect]) -> dict[str, Any]:
    with Image.open(path) as source:
        image = source.convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    colors = [(0, 255, 120, 255), (255, 210, 40, 255), (255, 80, 160, 255)]
    for index, (name, rect) in enumerate(boxes.items()):
        color = colors[index % len(colors)]
        draw.rectangle(
            [rect.left(), rect.top(), rect.right(), rect.bottom()],
            outline=color,
            width=3,
        )
        draw.text((rect.left() + 5, rect.top() + 5), name, fill=color)
    output = path.with_name(path.stem + "_annotated.png")
    image.save(output, "PNG")
    return {"file": output.name, "sha256": digest(output)}


def _record_action(
    results: dict[str, Any], name: str, passed: bool, detail: Any
) -> None:
    results[name] = {"status": "PASS" if passed else "FAIL", "detail": detail}


def run(output: Path | None = None) -> dict[str, Any]:
    if output is None:
        output = Path(tempfile.mkdtemp(prefix="neoeng-stage9-functional-ui-"))
    output.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app = cast(QApplication, app)
    app.setStyleSheet(QSS)
    project = output / "ui_fixture.ndtproj"
    project.write_bytes(b"stage9-functional-ui-fixture-v1\n")
    scene = fixture_scene()
    window: Any = MainWindow(scene, AuditConfig())
    window._project_path = project
    window.scenario_authoring.bind_project(project)
    window.scenario_authoring.reset()
    # Match the production refresh that follows an image/project load.
    window._refresh_document_views(project_loaded=True)
    window.show()
    settle(app)

    result: dict[str, Any] = {
        "schema_version": 1,
        "status": "FAIL",
        "source": source_state(),
        "environment": {
            "platform": sys.platform,
            "python": sys.version.split()[0],
            "qt_platform": os.environ.get("QT_QPA_PLATFORM"),
        },
        "command_scope": "local-only; no commit/push/PR/merge",
        "functional": {},
        "visual": {"viewports": {}, "findings": []},
        "human_review": {"status": "NOT_CONFIRMED"},
        "artifacts": [],
    }
    try:
        palette = window.tool_palette
        tool_results: dict[str, Any] = {}
        for name, button in palette.tool_buttons.items():
            button.click()
            settle(app)
            passed = (
                button.isChecked() and palette.button_group.checkedButton() is button
            )
            passed = passed and window.canvas._tool is not None
            tool_results[name] = {
                "status": "PASS" if passed else "FAIL",
                "button_text": button.text(),
                "checked": button.isChecked(),
                "tool_object_created": window.canvas._tool is not None,
            }
        result["functional"]["tool_palette"] = tool_results

        xray_results: dict[str, Any] = {}
        for action, mode in (
            (window.act_lit, window.canvas.VIEW_LIT),
            (window.act_xray1, window.canvas.VIEW_XRAY_1),
            (window.act_xray2, window.canvas.VIEW_XRAY_2),
            (window.act_xray3, window.canvas.VIEW_XRAY_3),
        ):
            action.trigger()
            settle(app)
            xray_results[action.text()] = {
                "status": "PASS" if window.canvas._view_mode == mode else "FAIL",
                "mode": window.canvas._view_mode,
                "expected": mode,
            }
        result["functional"]["main_xray_actions"] = xray_results

        window.canvas.gizmo_toggle.click()
        gizmo_on = (
            window.canvas._gizmo_enabled == window.canvas.gizmo_toggle.isChecked()
        )
        window.canvas.gizmo_toggle.click()
        gizmo_off = (
            window.canvas._gizmo_enabled == window.canvas.gizmo_toggle.isChecked()
        )

        from src.core.transform_gesture import capture_transform_state

        window.canvas.gizmo_toggle.click()
        window.canvas._update_gizmo_screen_position()
        before_gizmo = capture_transform_state(scene, ["audit_object"])
        if window.canvas.gizmo is None:
            raise RuntimeError("gizmo was not initialized for gesture audit")
        window.canvas._gizmo_operation = window.canvas.gizmo.AXIS_X
        gesture_started = window.canvas._begin_gizmo_object_gesture()
        if gesture_started:
            window.canvas._preview_gizmo_transform(translation=(20.0, 0.0))
            gesture_result = window.canvas._finish_gizmo_gesture()
        else:
            gesture_result = None
        committed = gesture_result is not None and gesture_result.status.name == "APPLIED"
        after_gizmo = capture_transform_state(scene, ["audit_object"])
        undo_result = scene.cmd.undo(scene)
        restored = capture_transform_state(scene, ["audit_object"]) == before_gizmo
        _record_action(
            result["functional"],
            "gizmo_gesture_transaction",
            gesture_started and committed and after_gizmo != before_gizmo and restored and undo_result.status.name == "APPLIED",
            {"started": gesture_started, "committed": committed, "restored_after_undo": restored},
        )
        _record_action(
            result["functional"],
            "gizmo_toggle",
            gizmo_on and gizmo_off,
            {
                "toolbar_parent": window.canvas.gizmo_toggle.parent().objectName(),
                "state_roundtrip": gizmo_on and gizmo_off,
            },
        )

        menu = window.reference_menu_button.menu()
        menu.popup(window.reference_menu_button.mapToGlobal(QPoint(0, window.reference_menu_button.height())))
        settle(app)
        menu_rect = menu.geometry()
        screen_geometry = app.primaryScreen().availableGeometry()
        menus_on_screen = menu.isVisible() and screen_geometry.contains(menu_rect.topLeft()) and screen_geometry.contains(menu_rect.bottomRight())
        menu.close()
        _record_action(result["functional"], "menus_on_screen", menus_on_screen, {"geometry": [menu_rect.x(), menu_rect.y(), menu_rect.width(), menu_rect.height()], "screen": [screen_geometry.x(), screen_geometry.y(), screen_geometry.width(), screen_geometry.height()]})

        scroll_checks = []
        for scroll_area in window.findChildren(QScrollArea):
            scroll_area.verticalScrollBar().setValue(scroll_area.verticalScrollBar().maximum())
            scroll_checks.append(scroll_area.verticalScrollBar().value() == scroll_area.verticalScrollBar().maximum())
        _record_action(result["functional"], "inspector_scroll", bool(scroll_checks) and all(scroll_checks), {"areas": len(scroll_checks), "passed": scroll_checks})

        window.open_scenario_editor()
        editor = window.scenario_editor_window
        if editor is None:
            raise RuntimeError("dedicated scenario editor was not created")
        editor.show()
        settle(app)
        panel = editor.scenario_panel
        before = panel.list.count()
        panel.btn_add.click()
        after_add = panel.list.count()
        panel.btn_remove.click()
        after_remove = panel.list.count()
        _record_action(
            result["functional"],
            "scenario_layer_actions",
            after_add == before + 1 and after_remove == before,
            {
                "before": before,
                "after_add": after_add,
                "after_remove": after_remove,
                "dedicated_window": editor.objectName() == "scenario_editor_window",
            },
        )

        for label, size in VIEWPORTS.items():
            window.resize(QSize(*size))
            editor.resize(QSize(*size))
            settle(app)
            main_path = output / f"{label}_main.png"
            editor_path = output / f"{label}_scenario_editor.png"
            main_capture = capture(window, main_path)
            editor_capture = capture(editor, editor_path)
            main_boxes = {"canvas": rect_in(window.canvas, window)}
            if window.nav_toolbar.isVisible():
                main_boxes["navigation_toolbar"] = rect_in(window.nav_toolbar, window)
            editor_boxes = {
                "scenario_canvas": rect_in(editor.canvas, editor),
                "scenario_inspector": rect_in(panel, editor),
            }
            main_overlap = "navigation_toolbar" in main_boxes and main_boxes[
                "canvas"
            ].intersects(main_boxes["navigation_toolbar"])
            editor_overlap = editor_boxes["scenario_canvas"].intersects(
                editor_boxes["scenario_inspector"]
            )
            main_clipping = scoped_clipping(window)
            editor_clipping = scoped_clipping(editor)
            result["visual"]["viewports"][label] = {
                "main": main_capture,
                "main_annotated": annotate(main_path, main_boxes),
                "scenario_editor": editor_capture,
                "scenario_annotated": annotate(editor_path, editor_boxes),
                "geometry": {
                    "main": {
                        name: [rect.x(), rect.y(), rect.width(), rect.height()]
                        for name, rect in main_boxes.items()
                    },
                    "scenario": {
                        name: [rect.x(), rect.y(), rect.width(), rect.height()]
                        for name, rect in editor_boxes.items()
                    },
                },
                "overlap": {"main": main_overlap, "scenario": editor_overlap},
                "clipping": {"main": main_clipping, "scenario": editor_clipping},
            }
            if main_overlap or editor_overlap:
                result["visual"]["findings"].append(
                    {"viewport": label, "check": "overlap", "status": "FAIL"}
                )
            if main_clipping or editor_clipping:
                result["visual"]["findings"].append(
                    {
                        "viewport": label,
                        "check": "minimum_size_hint",
                        "status": "FAIL",
                        "main_count": len(main_clipping),
                        "scenario_count": len(editor_clipping),
                    }
                )

        mask = window.open_mask_viewer()
        settle(app)
        if mask is None:
            mask = window._mask_viewer_dialog
        if mask is None:
            raise RuntimeError("Mask Viewer did not open")
        mask_path = output / "mask_viewer_xray_controls.png"
        result["functional"]["mask_viewer_capture"] = capture(mask, mask_path)
        modes: list[dict[str, Any]] = []
        for index, button in enumerate(mask.view_mode_buttons):
            button.click()
            settle(app)
            passed = mask.viewer.get_display_mode() == index and button.isChecked()
            modes.append(
                {
                    "index": index,
                    "text": button.text(),
                    "checked": button.isChecked(),
                    "mode": mask.viewer.get_display_mode(),
                    "status": "PASS" if passed else "FAIL",
                }
            )
        result["functional"]["mask_viewer_modes"] = modes
        mask.close()

        functional_values: list[str | None] = []
        for value in result["functional"].values():
            if isinstance(value, dict):
                functional_values.extend(
                    item.get("status")
                    for item in value.values()
                    if isinstance(item, dict) and "status" in item
                )
        functional_pass = all(status == "PASS" for status in functional_values)
        visual_pass = not result["visual"]["findings"]
        result["checks"] = {
            "functional_actions": functional_pass,
            "visual_geometry": visual_pass,
            "human_review": False,
            "source_tree_clean": result["source"]["worktree_clean"],
        }
        result["automated_status"] = "PASS" if result["checks"]["functional_actions"] and result["checks"]["visual_geometry"] else "FAIL"
        result["status"] = "PASS_AUTOMATED_HUMAN_PENDING" if result["automated_status"] == "PASS" else "FAIL"
    except Exception as exc:
        result["fatal_error"] = {"type": type(exc).__name__, "message": str(exc)}
        result["status"] = "FAIL"
    finally:
        if window.scenario_editor_window is not None:
            window.scenario_editor_window.close()
        window.close()
        settle(app)

    checklist = output / "HUMAN_REVIEW_REQUIRED.md"
    checklist.write_text(
        """# Revisão humana obrigatória — Etapa 9

Este arquivo não é uma aprovação. A automação não prova sozinha aparência,
legibilidade, consistência de cores ou sensação de uso. Um revisor deve
abrir os PNGs listados no relatório e marcar cada item somente após observar
o comportamento real.

- [ ] Texto sem clipping em 1280x720
- [ ] Texto sem clipping em 1366x768
- [ ] Texto sem clipping em 1920x1080
- [ ] Canvas e painéis sem sobreposição visual
- [ ] Estados Lit/X-Ray distinguíveis e legíveis
- [ ] Gizmo e feedback não ocultam texto ou controles
- [ ] Contraste e cores do tema escuro consistentes
- [ ] Toolbars, painéis e editor de cenário têm hierarquia visual clara

Status inicial: NOT_CONFIRMED
""",
        encoding="utf-8",
        newline="\n",
    )
    result["human_review"] = {
        "status": "NOT_CONFIRMED",
        "checklist": checklist.name,
        "reason": "aparência e usabilidade final exigem observação humana",
    }
    result["artifacts"] = [
        {
            "file": path.name,
            "bytes": path.stat().st_size,
            "sha256": digest(path),
        }
        for path in sorted(output.iterdir())
        if path.is_file() and path.name != "report.json"
    ]
    report = output / "report.json"
    report.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    result["report"] = {
        "file": report.name,
        "bytes": report.stat().st_size,
        "sha256": digest(report),
        "note": "hash calculado após a gravação; não é auto-incluído no JSON",
    }
    return result


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    audit = run(target)
    print(json.dumps(audit, indent=2, ensure_ascii=False))
    raise SystemExit(0 if audit["status"] == "PASS" else 1)
