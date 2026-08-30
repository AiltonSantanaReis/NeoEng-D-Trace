from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
)
from src.ui.scene_authoring_inspector import SceneAuthoringInspector

SHA = "e" * 64


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app
    app.clipboard().clear()
    app.processEvents()


def _document() -> SceneAuthoringDocumentV1:
    transform = SceneTransformRecord(
        position=Point3Record(x=0.0, y=0.0, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )
    return SceneAuthoringDocumentV1(
        metadata={"name": "P2D-03B inspector", "generator": "test", "app_version": "0"},
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[AssetReferenceRecord(id="asset", path="assets/a.png", sha256=SHA)],
        layers=[SceneLayerAuthoringRecord(id="layer", name="Layer")],
        objects=[
            SceneObjectAuthoringRecord(
                id="a", asset_id="asset", layer_id="layer", transform=transform
            ),
            SceneObjectAuthoringRecord(
                id="b", asset_id="asset", layer_id="layer", transform=transform
            ),
        ],
        groups=[],
    )


def test_inspector_delete_delegates_to_complete_selection(qt_app):
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    session.set_selection(["a", "b"], primary="b")
    inspector = SceneAuthoringInspector(session)
    try:
        inspector._delete()
        assert session.document.objects == []
        assert session.selection.ids == ()
        assert session.undo_count == 1
    finally:
        inspector.close()
        inspector.deleteLater()
        qt_app.processEvents()


def test_inspector_text_fields_keep_native_clipboard_and_history_shortcuts(qt_app):
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    session.set_selection(["a"])
    session.nudge_selected(Point3Record(x=1.0, y=0.0, z=0.0))
    inspector = SceneAuthoringInspector(session)
    try:
        editor = inspector.position_x.lineEdit()
        editor.selectAll()
        editor.setFocus()
        qt_app.processEvents()
        copied = editor.text()
        QTest.keyClick(
            editor,
            Qt.Key.Key_C,
            Qt.KeyboardModifier.ControlModifier,
        )
        assert qt_app.clipboard().text() == copied
        editor.clear()
        QTest.keyClick(
            editor,
            Qt.Key.Key_V,
            Qt.KeyboardModifier.ControlModifier,
        )
        assert editor.text() == copied

        before = session.document.model_copy(deep=True)
        QTest.keyClick(
            editor,
            Qt.Key.Key_Z,
            Qt.KeyboardModifier.ControlModifier,
        )
        QTest.keyClick(
            editor,
            Qt.Key.Key_Y,
            Qt.KeyboardModifier.ControlModifier,
        )
        assert session.document == before
        assert session.undo_count == 1
    finally:
        inspector.close()
        inspector.deleteLater()
        qt_app.processEvents()
