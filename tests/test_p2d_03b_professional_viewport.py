from __future__ import annotations

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QKeyEvent
import pytest

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
from src.ui.scene_authoring_viewport import SceneAuthoringViewport


SHA = "d" * 64

@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app
    app.clipboard().clear()
    app.processEvents()


def _transform(x: float, y: float) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _view() -> SceneAuthoringViewport:
    document = SceneAuthoringDocumentV1(
        metadata={"name": "P2D-03B viewport", "generator": "test", "app_version": "0"},
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[AssetReferenceRecord(id="asset", path="assets/a.png", sha256=SHA)],
        layers=[SceneLayerAuthoringRecord(id="layer", name="Layer")],
        objects=[
            SceneObjectAuthoringRecord(
                id="a", asset_id="asset", layer_id="layer", transform=_transform(0, 0)
            ),
            SceneObjectAuthoringRecord(
                id="b", asset_id="asset", layer_id="layer", transform=_transform(100, 20)
            ),
        ],
        groups=[],
    )
    view = SceneAuthoringViewport(SceneAuthoringSession(SceneAuthoringModel(document)))
    view.resize(640, 480)
    view.set_geometry("a", [(-20, -20), (20, -20), (20, 20), (-20, 20)])
    view.set_geometry("b", [(-20, -20), (20, -20), (20, 20), (-20, 20)])
    view.show()
    QApplication.processEvents()
    return view


def _key(view: SceneAuthoringViewport, key: Qt.Key, modifiers=Qt.KeyboardModifier.NoModifier):
    event = QKeyEvent(QEvent.Type.KeyPress, key, modifiers)
    view.keyPressEvent(event)
    assert event.isAccepted()


def test_professional_keyboard_commands_are_transactional(qt_app):
    view = _view()
    try:
        view.session.set_selection(["a"])
        _key(view, Qt.Key.Key_Right)
        assert view.session.document.objects[0].transform.position.x == 1.0
        assert view.session.undo_count == 1

        _key(view, Qt.Key.Key_D, Qt.KeyboardModifier.ControlModifier)
        assert [item.id for item in view.session.document.objects] == [
            "a",
            "b",
            "a__copy",
        ]
        assert view.session.selection.ids == ("a__copy",)

        before_copy = view.session.document.model_copy(deep=True)
        _key(view, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        assert view.session.document == before_copy
        _key(view, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        assert len(view.session.document.objects) == 4
        pasted_id = view.session.selection.primary
        assert pasted_id not in {"a", "b", "a__copy"}

        _key(view, Qt.Key.Key_Delete)
        assert pasted_id not in {item.id for item in view.session.document.objects}
        assert view.session.selection.ids == ()

        _key(view, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        assert pasted_id in {item.id for item in view.session.document.objects}
        _key(view, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
        assert pasted_id not in {item.id for item in view.session.document.objects}
    finally:
        view.close()
        view.deleteLater()
        qt_app.processEvents()


def test_shift_nudge_uses_ten_world_units_and_preview_is_read_only(qt_app):
    view = _view()
    try:
        view.session.set_selection(["a"])
        _key(view, Qt.Key.Key_Down, Qt.KeyboardModifier.ShiftModifier)
        assert view.session.document.objects[0].transform.position.y == 10.0

        before = view.session.document.model_copy(deep=True)
        view.set_preview_enabled(True)
        view.set_authoring_enabled(False)
        _key(view, Qt.Key.Key_Right)
        _key(view, Qt.Key.Key_D, Qt.KeyboardModifier.ControlModifier)
        _key(view, Qt.Key.Key_Delete)
        _key(view, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        assert view.session.document == before
    finally:
        view.close()
        view.deleteLater()
        qt_app.processEvents()
