"""Behavioral tests for the professional scenario authoring surface."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QScrollArea

from src.core.scenario_authoring import ScenarioAuthoringState
from src.core.scene_authoring_factory import document_from_scene
from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.models.scene import Scene
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneSnapRecord,
    SceneTransformRecord,
)
from src.ui.scene_authoring_inspector import SceneAuthoringInspector
from src.ui.scene_authoring_viewport import SceneAuthoringViewport, SceneTransformGizmo

SHA = "a" * 64


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _transform(x: float = 0.0, y: float = 0.0) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=2.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _document(*, locked: bool = False) -> SceneAuthoringDocumentV1:
    return SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="Stage 3 test", generator="NeoEng-D-Trace", app_version="0.2.0"
        ),
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[AssetReferenceRecord(id="asset", path="assets/a.png", sha256=SHA)],
        layers=[SceneLayerAuthoringRecord(id="layer", name="Layer", locked=locked)],
        objects=[
            SceneObjectAuthoringRecord(
                id="object_a",
                asset_id="asset",
                layer_id="layer",
                transform=_transform(10.0, 20.0),
            ),
            SceneObjectAuthoringRecord(
                id="object_b",
                asset_id="asset",
                layer_id="layer",
                transform=_transform(30.0, 20.0),
            ),
        ],
        groups=[],
    )


def test_session_commits_one_gesture_and_supports_undo_redo() -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    session.set_selection(["object_a", "object_b"], "object_a")
    session.begin_gesture()
    session.preview_transform_selected(
        translation=Point3Record(x=5.0, y=-3.0, z=1.0),
        rotation_z=90.0,
        scale_factor=2.0,
    )
    assert session.finish_gesture("Move and transform selection") is True
    assert session.undo_count == 1
    assert session.document.objects[0].transform.position.z == 3.0
    assert session.undo() is True
    assert session.document.objects[0].transform.position == Point3Record(
        x=10.0, y=20.0, z=2.0
    )
    assert session.redo() is True
    assert session.document.objects[0].transform.scale.x == 2.0


def test_session_failed_operation_restores_exact_snapshot_and_locked_edit_rejects() -> (
    None
):
    session = SceneAuthoringSession(SceneAuthoringModel(_document(locked=True)))
    session.set_selection(["object_a"])
    before = session.snapshot()
    with pytest.raises(PermissionError, match="layer"):
        session.translate_selected(Point3Record(x=1.0, y=0.0, z=0.0))
    assert session.snapshot() == before
    assert session.undo_count == 0


def test_factory_only_emits_hashable_relative_asset(tmp_path: Path) -> None:
    project = tmp_path / "scene.ndtproj"
    project.write_bytes(b"project bytes")
    asset = tmp_path / "assets" / "tree.png"
    asset.parent.mkdir()
    image = QImage(12, 8, QImage.Format.Format_RGBA8888)
    image.fill(0xFF204060)
    assert image.save(str(asset))

    scene = Scene()
    scene.image_path = str(asset)
    scene.add_object("tree", [(0, 0), (12, 0), (12, 8), (0, 8)])
    document = document_from_scene(scene, project)
    assert document.assets[0].path == "assets/tree.png"
    assert len(document.assets[0].sha256) == 64
    assert document.objects[0].asset_id == "project_image"

    outside = tmp_path.parent / "outside-stage3.png"
    outside.write_bytes(asset.read_bytes())
    scene.image_path = str(outside)
    rejected = document_from_scene(scene, project)
    assert rejected.assets == []
    assert rejected.objects == []
    scene.image_path = None
    no_image = document_from_scene(scene, project)
    assert no_image.assets == []
    assert no_image.objects == []
    scene.image_path = "assets/tree.png"
    relative = document_from_scene(scene, project)
    assert relative.assets[0].path == "assets/tree.png"
    scene.image_path = str(tmp_path / "missing.png")
    missing = document_from_scene(scene, project)
    assert missing.assets == []
    scene.image_path = str(asset)
    scene.layers = []
    fallback_layers = document_from_scene(scene, project)
    assert fallback_layers.layers[0].id == "layer_default"


def test_viewport_inspector_and_drop_import_are_interactive(
    tmp_path: Path, qt_app
) -> None:
    project = tmp_path / "scene.ndtproj"
    project.write_bytes(b"project bytes")
    asset = tmp_path / "assets" / "drop.png"
    asset.parent.mkdir()
    image = QImage(20, 14, QImage.Format.Format_RGBA8888)
    image.fill(0xFF55AACC)
    assert image.save(str(asset))

    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    inspector = SceneAuthoringInspector(session)
    try:
        viewport.resize(640, 480)
        inspector.show()
        viewport.show()
        qt_app.processEvents()
        session.set_selection(["object_a"])
        qt_app.processEvents()
        assert "object_a" in viewport._items
        assert viewport._gizmo is not None
        assert inspector.position_x.isEnabled()

        start = viewport.mapFromScene(QPointF(10.0, 20.0))
        end = viewport.mapFromScene(QPointF(25.0, 20.0))
        QTest.mousePress(viewport.viewport(), Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(viewport.viewport(), end)
        QTest.mouseRelease(viewport.viewport(), Qt.MouseButton.LeftButton, pos=end)
        assert session.document.objects[0].transform.position.x == 25.0

        inspector.position_x.setValue(77.0)
        inspector.apply_transform()
        qt_app.processEvents()
        assert session.document.objects[0].transform.position.x == 77.0
        assert viewport._items["object_a"].pos().x() == 77.0

        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(asset))])
        event = QDropEvent(
            QPointF(140.0, 120.0),
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        viewport.dropEvent(event)
        qt_app.processEvents()
        assert any(item.path == "assets/drop.png" for item in session.document.assets)
        assert session.undo() is True
        assert not any(
            item.path == "assets/drop.png" for item in session.document.assets
        )
        assert session.redo() is True
    finally:
        inspector.close()
        viewport.close()
        qt_app.processEvents()


def test_viewport_rejects_outside_and_unsupported_drop(tmp_path: Path, qt_app) -> None:
    project = tmp_path / "scene.ndtproj"
    project.write_bytes(b"project bytes")
    outside = tmp_path.parent / "outside-stage3.txt"
    outside.write_text("not an image", encoding="utf-8")
    outside_image = tmp_path.parent / "outside-stage3.png"
    external_image = QImage(8, 8, QImage.Format.Format_RGBA8888)
    external_image.fill(0xFF112233)
    assert external_image.save(str(outside_image))
    invalid = tmp_path / "invalid.png"
    invalid.write_bytes(b"not a PNG")
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    try:
        for path in (outside_image, outside, invalid):
            mime = QMimeData()
            mime.setUrls([QUrl.fromLocalFile(str(path))])
            event = QDropEvent(
                QPointF(10.0, 10.0),
                Qt.DropAction.CopyAction,
                mime,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            viewport.dropEvent(event)
        assert len(session.document.assets) == 1
        assert len(session.document.objects) == 2
    finally:
        viewport.close()
        qt_app.processEvents()


def test_window_binds_professional_editor_only_after_saved_project(
    tmp_path: Path, qt_app
) -> None:
    from src.core.commands import CommandManager
    from src.ui.scenario_editor_window import ScenarioEditorWindow

    project = tmp_path / "scene.ndtproj"
    project.write_bytes(b"project bytes")
    image = tmp_path / "scene.png"
    rendered = QImage(24, 16, QImage.Format.Format_RGBA8888)
    rendered.fill(0xFF336699)
    assert rendered.save(str(image))
    scene = Scene()
    scene.cmd = CommandManager(max_history=10)
    scene.image_path = str(image)
    scene.add_object("scene_object", [(0, 0), (24, 0), (24, 16), (0, 16)])
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project)
    window = ScenarioEditorWindow(authoring, scene)
    try:
        window.show()
        qt_app.processEvents()
        assert window.professional_viewport is not None
        assert window.professional_inspector is not None
        assert isinstance(window.right_pages.currentWidget(), QScrollArea)
        assert (
            window.right_pages.currentWidget().widget() is window.professional_inspector
        )
        window.professional_session.set_selection(["scene_object"])
        qt_app.processEvents()
        assert window.professional_pages.currentWidget() is window.professional_viewport
        assert window.professional_viewport._gizmo is not None
        assert len(window.professional_session.document.objects) == 1
    finally:
        window.close()
        qt_app.processEvents()


def test_session_transaction_guards_and_history_capacity() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        SceneAuthoringSession(SceneAuthoringModel(_document()), max_history=0)
    session = SceneAuthoringSession(SceneAuthoringModel(_document()), max_history=1)
    notifications = []

    def callback() -> None:
        notifications.append(True)

    session.subscribe(callback)
    session.subscribe(callback)
    session.set_selection(["object_a"])
    assert len(notifications) == 1
    assert session.apply(lambda: None, "no-op") is False
    session.begin_gesture()
    with pytest.raises(RuntimeError, match="already active"):
        session.begin_gesture()
    session.cancel_gesture()
    with pytest.raises(RuntimeError, match="no authoring gesture"):
        session.restore_gesture_base()
    with pytest.raises(RuntimeError, match="no authoring gesture"):
        session.finish_gesture("missing")
    with pytest.raises(RuntimeError, match="no authoring gesture"):
        session.preview_transform_selected()
    before = session.snapshot()
    with pytest.raises(RuntimeError, match="boom"):
        session.apply(lambda: (_ for _ in ()).throw(RuntimeError("boom")), "fail")
    assert session.snapshot() == before
    session.update_transform("object_a", _transform(11.0))
    session.update_transform("object_a", _transform(12.0))
    assert session.undo_count == 1
    session.clear_history()
    assert session.undo() is False
    assert session.redo() is False


def test_gizmo_modes_and_invalid_image_are_explicit(qt_app, tmp_path: Path) -> None:
    gizmo = SceneTransformGizmo()
    assert gizmo._mode_for(QPointF(40.0, 0.0)) == "rotate"
    assert gizmo._mode_for(QPointF(30.0, 0.0)) == "translate_x"
    assert gizmo._mode_for(QPointF(0.0, -30.0)) == "translate_y"
    assert gizmo._mode_for(QPointF(30.0, 30.0)) == "scale"
    assert gizmo._mode_for(QPointF(0.0, 0.0)) == "translate"
    invalid = tmp_path / "invalid.png"
    invalid.write_bytes(b"not an image")
    with pytest.raises(ValueError, match="decoded"):
        SceneAuthoringViewport._image_size(invalid)
    del qt_app


def test_inspector_reports_empty_and_locked_edit_paths(qt_app) -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    inspector = SceneAuthoringInspector(session)
    try:
        inspector.apply_transform()
        inspector._undo()
        inspector._redo()
        inspector._delete()
        session.set_selection(["object_a"])
        inspector.snap_enabled.setChecked(True)
        inspector._apply_snap()
        assert session.document.snap == SceneSnapRecord(enabled=True)
    finally:
        inspector.close()
    locked_session = SceneAuthoringSession(SceneAuthoringModel(_document(locked=True)))
    locked_inspector = SceneAuthoringInspector(locked_session)
    messages = []
    locked_inspector.status_message.connect(messages.append)
    try:
        locked_session.set_selection(["object_a"])
        locked_inspector.apply_transform()
        assert messages and "locked" in messages[-1]
    finally:
        locked_inspector.close()


def test_viewport_gizmo_modes_commit_and_noop_paths(qt_app) -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    viewport = SceneAuthoringViewport(session)
    try:
        viewport._object_moved("missing", QPointF(1.0, 1.0))
        viewport._object_released("missing", QPointF(1.0, 1.0))
        assert viewport.undo() is False
        assert viewport.redo() is False
        session.set_selection(["object_a"])
        for mode, point in (
            ("translate_x", QPointF(20.0, 30.0)),
            ("translate_y", QPointF(30.0, 30.0)),
            ("scale", QPointF(35.0, 35.0)),
            ("rotate", QPointF(10.0, 60.0)),
        ):
            current = session.document.objects[0].transform.position
            start = QPointF(current.x, current.y)
            viewport._gizmo_started(mode, start)
            viewport._gizmo_changed(mode, point)
            viewport._gizmo_finished(mode, point)
        viewport._gizmo_start = None
        viewport._gizmo_changed("translate", QPointF(1.0, 1.0))
        viewport._gizmo_start = QPointF(0.0, 0.0)
        viewport._gizmo_changed("unknown", QPointF(1.0, 1.0))
        viewport._gizmo_start = QPointF(0.0, 0.0)
        session.clear_selection()
        viewport._gizmo_changed("rotate", QPointF(1.0, 1.0))
        assert viewport._gizmo_start is not None
    finally:
        viewport.close()
        qt_app.processEvents()


def test_viewport_drop_rejections_text_path_and_visibility(
    qt_app, tmp_path: Path
) -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    viewport = SceneAuthoringViewport(session)
    messages = []
    viewport.status_message.connect(messages.append)
    try:
        empty = QMimeData()
        drag_empty = QDragEnterEvent(
            QPoint(1, 1),
            Qt.DropAction.CopyAction,
            empty,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        viewport.dragEnterEvent(drag_empty)
        assert not drag_empty.isAccepted()
        no_drop = QDropEvent(
            QPointF(1.0, 1.0),
            Qt.DropAction.CopyAction,
            empty,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        viewport.dropEvent(no_drop)
        assert "Drop an image" in messages[-1]
    finally:
        viewport.close()

    project = tmp_path / "scene.ndtproj"
    project.write_bytes(b"project bytes")
    asset = tmp_path / "text-drop.png"
    image = QImage(6, 5, QImage.Format.Format_RGBA8888)
    image.fill(0xFF445566)
    assert image.save(str(asset))
    no_project = SceneAuthoringViewport(
        SceneAuthoringSession(SceneAuthoringModel(_document()))
    )
    no_project.status_message.connect(messages.append)
    try:
        text_mime = QMimeData()
        text_mime.setText(str(asset))
        drag_text = QDragEnterEvent(
            QPoint(1, 1),
            Qt.DropAction.CopyAction,
            text_mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        no_project.dragEnterEvent(drag_text)
        assert drag_text.isAccepted()
        no_project.dropEvent(
            QDropEvent(
                QPointF(2.0, 2.0),
                Qt.DropAction.CopyAction,
                text_mime,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
        )
        assert "Save the project" in messages[-1]
    finally:
        no_project.close()

    imported_session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    imported = SceneAuthoringViewport(imported_session, project_root=tmp_path)
    try:
        text_mime = QMimeData()
        text_mime.setText(str(asset))
        imported.dropEvent(
            QDropEvent(
                QPointF(2.0, 2.0),
                Qt.DropAction.CopyAction,
                text_mime,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
        )
        assert any(
            item.path == "text-drop.png" for item in imported_session.document.assets
        )
    finally:
        imported.close()

    hidden = _document().model_copy(
        update={
            "objects": [
                item.model_copy(update={"visible": False})
                for item in _document().objects
            ]
        }
    )
    hidden_viewport = SceneAuthoringViewport(
        SceneAuthoringSession(SceneAuthoringModel(hidden))
    )
    try:
        assert hidden_viewport._items == {}
    finally:
        hidden_viewport.close()
        qt_app.processEvents()


def test_session_empty_state_observables() -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    assert session.can_undo is False
    assert session.can_redo is False
    assert session.undo_count == 0
    assert session.redo_count == 0
    session.cancel_gesture()
    session.clear_selection()
    assert session.selection.ids == ()
