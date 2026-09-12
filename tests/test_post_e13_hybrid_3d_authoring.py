from __future__ import annotations

import json
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.core.hybrid_scene_model import (
    HybridSceneError,
    default_hybrid_scene,
    load_hybrid_scene,
    save_hybrid_scene,
    validate_hybrid_scene,
)
from src.core.scenario_authoring import ScenarioAuthoringState
from src.models.scene import Scene
from src.ui.hybrid_scene_viewport import HybridSceneViewport
from src.ui.scenario_editor_window import ScenarioEditorWindow


@pytest.fixture
def qt_app() -> QApplication:
    app = QApplication.instance() or QApplication([])
    yield app


def test_hybrid_model_is_additive_and_can_start_without_a_2d_asset(
    tmp_path: Path,
) -> None:
    project = tmp_path / "scenario.ndtproj"
    scene_2d = tmp_path / "scenario.ndtscene.json"
    scene_2d.write_text('{"format_id":"existing-2d"}\n', encoding="utf-8")
    sidecar = project.with_suffix(".hybrid3d.json")

    document = default_hybrid_scene()
    validate_hybrid_scene(document)
    save_hybrid_scene(document, sidecar)

    assert sidecar.is_file()
    assert json.loads(sidecar.read_text(encoding="utf-8"))["support_status"] == (
        "EDITOR_VERTICAL_SLICE"
    )
    assert scene_2d.read_text(encoding="utf-8") == '{"format_id":"existing-2d"}\n'
    assert load_hybrid_scene(sidecar)["selected_id"] == "mesh-cube"


def test_hybrid_viewport_covers_authoring_save_reload_and_localization(
    qt_app: QApplication, tmp_path: Path
) -> None:
    sidecar = tmp_path / "scenario.hybrid3d.json"
    viewport = HybridSceneViewport(sidecar, language="pt")
    viewport.resize(1100, 620)
    viewport.show()
    qt_app.processEvents()

    viewport.add_mesh("plane")
    viewport.add_light()
    viewport.add_camera()
    viewport.select_object("camera-1")
    viewport._target_fields["x"].setValue(2.5)
    viewport._target_fields["y"].setValue(1.25)
    viewport.mode_combo.setCurrentIndex(1)
    viewport.projection_combo.setCurrentIndex(1)
    assert viewport._buttons["cube"].text() == "Adicionar cubo"
    assert viewport.save_scene()

    reopened = HybridSceneViewport(sidecar, language="pt")
    assert reopened.document["camera"]["projection"] == "orthographic"
    assert reopened.mode_combo.currentData() == "3d"
    camera = next(
        item for item in reopened.document["objects"] if item["id"] == "camera-1"
    )
    assert camera["target"][:2] == [2.5, 1.25]
    assert any(item["kind"] == "light" for item in reopened.document["objects"])

    reopened.update_language("en")
    assert reopened._buttons["cube"].text() == "Add cube"
    assert reopened.hierarchy_label.text() == "3D hierarchy"


def test_hybrid_canvas_renders_objects_and_real_drag_accumulates(
    qt_app: QApplication, tmp_path: Path
) -> None:
    viewport = HybridSceneViewport(tmp_path / "scenario.hybrid3d.json", language="pt")
    viewport.resize(1000, 600)
    viewport.show()
    qt_app.processEvents()
    viewport.canvas.resize(700, 460)
    viewport.canvas.show()
    qt_app.processEvents()

    image = QImage(viewport.canvas.size(), QImage.Format.Format_ARGB32)
    image.fill(QColor("#101820"))
    viewport.canvas.render(image)
    non_background = sum(
        1
        for x in range(0, image.width(), 10)
        for y in range(0, image.height(), 10)
        if image.pixelColor(x, y) != QColor("#101820")
    )
    assert non_background > 20

    viewport.select_object("mesh-cube")
    cube_region = next(
        region
        for object_id, region in viewport.canvas._hit_regions
        if object_id == "mesh-cube"
    )
    start = cube_region.center().toPoint()
    end = QPoint(start.x() + 80, start.y())
    original_x = viewport.document["objects"][0]["position"][0]
    QTest.mousePress(viewport.canvas, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(viewport.canvas, end, 20)
    QTest.mouseRelease(viewport.canvas, Qt.MouseButton.LeftButton, pos=end)
    assert viewport.document["objects"][0]["position"][0] > original_x + 1.0
    assert viewport.dirty


def test_hybrid_model_rejects_unknown_or_unsafe_content() -> None:
    document = default_hybrid_scene()
    document["objects"][0]["primitive"] = "sphere"
    with pytest.raises(HybridSceneError, match="primitive is invalid"):
        validate_hybrid_scene(document)

    document = default_hybrid_scene()
    document["camera"]["far"] = 0.01
    with pytest.raises(HybridSceneError, match="clipping or FOV"):
        validate_hybrid_scene(document)


def test_scenario_editor_exposes_hybrid_view_without_replacing_2d_flow(
    qt_app: QApplication, tmp_path: Path
) -> None:
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    project = tmp_path / "scene.ndtproj"
    scene.save_project(str(project))
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project)
    window = ScenarioEditorWindow(authoring, scene, language="pt")
    window.show()
    qt_app.processEvents()

    assert window.hybrid_action.isEnabled()
    window.hybrid_action.trigger()
    qt_app.processEvents()
    assert window.hybrid_viewport is not None
    assert window.professional_pages.currentWidget() is window.hybrid_viewport
    window.hybrid_viewport.add_mesh("cube")
    assert window.hybrid_viewport.save_scene()
    assert project.with_suffix(".hybrid3d.json").is_file()

    window.hybrid_action.trigger()
    qt_app.processEvents()
    assert window.professional_pages.currentWidget() is window.professional_viewport
    window.close()
    qt_app.processEvents()


def test_hybrid_canvas_covers_modes_lighting_camera_gestures_and_failures(
    qt_app: QApplication, tmp_path: Path
) -> None:
    class MouseEvent:
        def __init__(
            self,
            x: float,
            y: float,
            button: Qt.MouseButton,
            modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
        ) -> None:
            self._position = QPointF(x, y)
            self._button = button
            self._modifiers = modifiers

        def position(self) -> QPointF:
            return self._position

        def button(self) -> Qt.MouseButton:
            return self._button

        def modifiers(self) -> Qt.KeyboardModifier:
            return self._modifiers

    class WheelEvent:
        def __init__(self, delta: int) -> None:
            self._delta = QPoint(0, delta)

        def angleDelta(self) -> QPoint:
            return self._delta

    sidecar = tmp_path / "hybrid-boundaries.json"
    viewport = HybridSceneViewport(sidecar, language="en")
    viewport.resize(1100, 640)
    viewport.show()
    qt_app.processEvents()
    canvas = viewport.canvas
    canvas.resize(720, 460)
    canvas.show()
    qt_app.processEvents()

    for mode in ("2d", "2.5d", "3d", "unsupported"):
        canvas.set_mode(mode)
        canvas._world_to_screen((1.0, 2.0, 3.0))
    assert canvas._mode == "3d"
    assert viewport.mode_caption() == "3D mode"

    viewport.projection_combo.setCurrentIndex(1)
    assert viewport.projection_caption() == "Orthographic projection"
    canvas._world_to_screen((1.0, 2.0, 3.0))
    viewport.projection_combo.setCurrentIndex(0)
    assert viewport.projection_caption() == "Perspective projection"
    canvas._vertices({"primitive": "plane", "scale": None})

    viewport.add_mesh("plane")
    viewport.add_mesh("cube")
    viewport.add_light()
    viewport.add_light()
    viewport.add_camera()
    viewport.add_camera()
    directional = next(
        item
        for item in viewport.document["objects"]
        if item["kind"] == "light" and item["id"] == "light-point-1"
    )
    directional["light_type"] = "directional"
    directional["color"] = "not-a-color"
    camera = next(
        item
        for item in viewport.document["objects"]
        if item["kind"] == "camera" and item["id"] == "camera-1"
    )
    camera["target"] = list(camera["position"])
    viewport.select_object("mesh-cube")

    image = QImage(canvas.size(), QImage.Format.Format_ARGB32)
    image.fill(QColor("#101820"))
    canvas.render(image)
    assert {object_id for object_id, _region in canvas._hit_regions} >= {
        "mesh-cube",
        "mesh-plane-1",
        "light-point-1",
        "camera-1",
    }

    canvas.set_mode("2d")
    canvas.render(image)
    canvas.set_mode("2.5d")
    canvas.render(image)
    canvas.set_mode("3d")
    canvas.render(image)
    viewport.select_object("camera-1")
    canvas.render(image)
    canvas._hit_regions.append(("ghost", QRectF(8, 8, 12, 12)))
    canvas.mousePressEvent(MouseEvent(14, 14, Qt.MouseButton.LeftButton))

    status_messages: list[str] = []
    canvas.status_message.connect(status_messages.append)
    canvas.mousePressEvent(MouseEvent(4, 4, Qt.MouseButton.RightButton))
    canvas.mousePressEvent(MouseEvent(4, 4, Qt.MouseButton.LeftButton))
    canvas.mousePressEvent(MouseEvent(100, 100, Qt.MouseButton.MiddleButton))
    canvas.mouseMoveEvent(MouseEvent(155, 380, Qt.MouseButton.MiddleButton))
    canvas.mouseReleaseEvent(MouseEvent(155, 380, Qt.MouseButton.MiddleButton))
    canvas._zoom = 160.0
    canvas.wheelEvent(WheelEvent(120))
    canvas._zoom = 12.0
    canvas.wheelEvent(WheelEvent(-120))
    assert "Clique em um objeto para selecioná-lo" in status_messages

    cube_region = next(
        region for object_id, region in canvas._hit_regions if object_id == "mesh-cube"
    )
    cube_start = cube_region.center()
    canvas.mousePressEvent(
        MouseEvent(cube_start.x(), cube_start.y(), Qt.MouseButton.LeftButton)
    )
    canvas.mouseMoveEvent(
        MouseEvent(
            cube_start.x() + 36,
            cube_start.y() + 22,
            Qt.MouseButton.LeftButton,
        )
    )
    canvas.mouseReleaseEvent(
        MouseEvent(
            cube_start.x() + 36,
            cube_start.y() + 22,
            Qt.MouseButton.LeftButton,
        )
    )

    light_region = next(
        region
        for object_id, region in canvas._hit_regions
        if object_id == "light-point-1"
    )
    light_start = light_region.center()
    canvas.mousePressEvent(
        MouseEvent(light_start.x(), light_start.y(), Qt.MouseButton.LeftButton)
    )
    canvas.mouseMoveEvent(
        MouseEvent(
            light_start.x(),
            light_start.y() + 30,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.ShiftModifier,
        )
    )
    canvas.mouseReleaseEvent(
        MouseEvent(
            light_start.x(),
            light_start.y() + 30,
            Qt.MouseButton.LeftButton,
        )
    )

    camera_region = next(
        region for object_id, region in canvas._hit_regions if object_id == "camera-1"
    )
    camera_start = camera_region.center()
    canvas.mousePressEvent(
        MouseEvent(camera_start.x(), camera_start.y(), Qt.MouseButton.LeftButton)
    )
    canvas.mouseMoveEvent(
        MouseEvent(
            camera_start.x() + 30,
            camera_start.y(),
            Qt.MouseButton.LeftButton,
        )
    )
    canvas.mouseReleaseEvent(
        MouseEvent(
            camera_start.x() + 30,
            camera_start.y(),
            Qt.MouseButton.LeftButton,
        )
    )
    assert viewport.document["camera"]["position"] == camera["position"]

    canvas._drag_id = "missing"
    canvas._drag_origin = [0.0, 0.0, 0.0]
    canvas.mouseMoveEvent(MouseEvent(20, 20, Qt.MouseButton.LeftButton))
    canvas._drag_id = "mesh-cube"
    canvas._drag_origin = None
    canvas.mouseMoveEvent(MouseEvent(20, 20, Qt.MouseButton.LeftButton))
    canvas._drag_id = None
    canvas.mouseReleaseEvent(MouseEvent(20, 20, Qt.MouseButton.LeftButton))

    viewport._hierarchy_changed(None, None)
    viewport.select_object("does-not-exist")
    viewport.selected_id = "does-not-exist"
    viewport._refresh_inspector()
    viewport._apply_inspector()
    viewport._apply_target()
    viewport.document["camera"]["projection"] = "unsupported"
    viewport._sync_projection_combo()
    viewport.document["camera"]["projection"] = "perspective"
    viewport.selected_id = "mesh-cube"
    viewport.select_object("light-point-1")
    viewport._fields["intensity"].setValue(4.0)
    viewport._apply_inspector()
    viewport.select_object("camera-1")
    viewport._fields["fov"].setValue(72.0)
    viewport._target_fields["x"].setValue(1.5)
    viewport._apply_inspector()
    viewport._apply_target()
    assert viewport.document["camera"]["fov_degrees"] == 72.0

    viewport.frame_all()
    assert viewport.save_scene()
    assert viewport.reload_scene()
    viewport.new_scene()
    assert viewport.dirty

    missing = HybridSceneViewport(tmp_path / "not-saved.json", language="en")
    assert not missing.reload_scene()
    missing.frame_all()
    invalid = tmp_path / "invalid-hybrid.json"
    invalid.write_text('{"invalid": true}\n', encoding="utf-8")
    HybridSceneViewport(invalid, language="en")
