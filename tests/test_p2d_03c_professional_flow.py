from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.core.scenario_authoring import ScenarioAuthoringState
from src.models.scene import Scene
from src.ui.scenario_editor_window import ScenarioEditorWindow


def _window(tmp_path: Path, qt_app: QApplication) -> ScenarioEditorWindow:
    project = tmp_path / "scene.ndtproj"
    project.write_bytes(b"p2d-03c project")
    image = tmp_path / "scene.png"
    rendered = QImage(40, 24, QImage.Format.Format_RGBA8888)
    rendered.fill(0xFF336699)
    assert rendered.save(str(image))
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image_path = str(image)
    scene.add_object("scene_object", [(0, 0), (40, 0), (40, 24), (0, 24)])
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project)
    window = ScenarioEditorWindow(authoring, scene)
    window.show()
    qt_app.processEvents()
    return window


def test_professional_fit_controls_are_connected_and_preview_disables_edits(
    tmp_path: Path,
) -> None:
    qt_app = QApplication.instance() or QApplication([])
    window = _window(tmp_path, qt_app)
    try:
        viewport = window.professional_viewport
        inspector = window.professional_inspector
        session = window.professional_session
        assert viewport is not None and inspector is not None and session is not None
        session.set_selection(["scene_object"], "scene_object")
        before_document = session.document.model_dump(mode="json")
        before_history = len(session._undo)

        inspector.fit_button.click()
        qt_app.processEvents()
        selection_zoom = viewport.navigation_zoom
        inspector.fit_all_button.click()
        qt_app.processEvents()

        assert selection_zoom > 0.0
        assert viewport.navigation_zoom > 0.0
        assert session.document.model_dump(mode="json") == before_document
        assert len(session._undo) == before_history
        assert inspector.fit_button.nextInFocusChain() is inspector.fit_all_button

        window.preview_action.trigger()
        qt_app.processEvents()
        assert not inspector.isEnabled()
        assert not inspector.fit_all_button.isEnabled()
    finally:
        window.close()
        qt_app.processEvents()
