"""Behavioral tests for the professional scenario authoring surface."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl
from PySide6.QtGui import QDropEvent, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

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
    SceneTransformRecord,
)
from src.ui.scene_authoring_inspector import SceneAuthoringInspector
from src.ui.scene_authoring_viewport import SceneAuthoringViewport

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
        window.professional_session.set_selection(["scene_object"])
        qt_app.processEvents()
        assert window.professional_pages.currentWidget() is window.professional_viewport
        assert window.professional_viewport._gizmo is not None
        assert len(window.professional_session.document.objects) == 1
    finally:
        window.close()
        qt_app.processEvents()
