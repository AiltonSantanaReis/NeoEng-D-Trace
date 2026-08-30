"""P2D-03A contracts for professional selection, focus and marquee input."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
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
from src.ui.scene_authoring_viewport import SceneAuthoringViewport


SHA = "b" * 64


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _transform(x: float, y: float) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _document() -> SceneAuthoringDocumentV1:
    return SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="P2D-03A test", generator="NeoEng-D-Trace", app_version="0.2.0"
        ),
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[AssetReferenceRecord(id="asset", path="assets/a.png", sha256=SHA)],
        layers=[SceneLayerAuthoringRecord(id="background", name="Background")],
        objects=[
            SceneObjectAuthoringRecord(
                id="a", asset_id="asset", layer_id="background", transform=_transform(0, 0)
            ),
            SceneObjectAuthoringRecord(
                id="b", asset_id="asset", layer_id="background", transform=_transform(100, 0)
            ),
            SceneObjectAuthoringRecord(
                id="c", asset_id="asset", layer_id="background", transform=_transform(200, 0)
            ),
        ],
        groups=[],
    )


def _viewport(qt_app) -> SceneAuthoringViewport:
    del qt_app
    view = SceneAuthoringViewport(SceneAuthoringSession(SceneAuthoringModel(_document())))
    view.resize(640, 480)
    view.set_geometry("a", [(-20, -20), (20, -20), (20, 20), (-20, 20)])
    view.set_geometry("b", [(-20, -20), (20, -20), (20, 20), (-20, 20)])
    view.set_geometry("c", [(-20, -20), (20, -20), (20, 20), (-20, 20)])
    view.show()
    QApplication.processEvents()
    return view


def _click(view: SceneAuthoringViewport, object_id: str, modifiers=Qt.KeyboardModifier.NoModifier):
    view._object_pressed(object_id, QPointF(0, 0), modifiers)
    view._object_released(object_id, QPointF(0, 0))


def test_professional_selection_modifiers_are_deterministic(qt_app):
    view = _viewport(qt_app)
    try:
        assert view.focusPolicy() == Qt.FocusPolicy.StrongFocus

        _click(view, "a")
        assert view.session.selection.ids == ("a",)
        assert view.session.selection.primary == "a"

        _click(view, "b", Qt.KeyboardModifier.ControlModifier)
        assert view.session.selection.ids == ("a", "b")
        assert view.session.selection.primary == "b"

        _click(view, "a", Qt.KeyboardModifier.ControlModifier)
        assert view.session.selection.ids == ("b",)
        assert view.session.selection.primary == "b"

        _click(view, "c", Qt.KeyboardModifier.ShiftModifier)
        assert view.session.selection.ids == ("b", "c")
        assert view.session.selection.primary == "c"
    finally:
        view.close()


def test_empty_click_clears_selection_and_escape_restores_marquee_anchor(qt_app):
    view = _viewport(qt_app)
    try:
        _click(view, "b")
        empty = QPoint(view.viewport().width() - 10, view.viewport().height() - 10)
        QTest.mousePress(
            view.viewport(),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            empty,
        )
        assert view.session.selection.ids == ()
        assert view._marquee_origin is not None

        escape = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Escape,
            Qt.KeyboardModifier.NoModifier,
        )
        view.keyPressEvent(escape)
        assert view.session.selection.ids == ("b",)
        assert view._marquee_origin is None
    finally:
        view.close()


def test_marquee_uses_containment_left_to_right_and_intersection_right_to_left(qt_app):
    view = _viewport(qt_app)
    try:
        selected = view._apply_marquee_selection(
            QPointF(-25, -25), QPointF(25, 25), Qt.KeyboardModifier.NoModifier
        )
        assert selected == ("a",)

        selected = view._apply_marquee_selection(
            QPointF(125, 25), QPointF(75, -25), Qt.KeyboardModifier.NoModifier
        )
        assert selected == ("b",)
    finally:
        view.close()


def test_marquee_modifier_selection_and_select_all(qt_app):
    view = _viewport(qt_app)
    try:
        _click(view, "a")
        assert view._apply_marquee_selection(
            QPointF(75, -25), QPointF(125, 25), Qt.KeyboardModifier.ShiftModifier
        ) == ("a", "b")

        assert view._apply_marquee_selection(
            QPointF(175, -25), QPointF(225, 25), Qt.KeyboardModifier.ControlModifier
        ) == ("a", "b", "c")

        select_all = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_A,
            Qt.KeyboardModifier.ControlModifier,
        )
        view.keyPressEvent(select_all)
        assert view.session.selection.ids == ("a", "b", "c")
        assert view.session.selection.primary == "c"
    finally:
        view.close()

def test_hidden_objects_are_not_reintroduced_by_marquee_or_select_all(qt_app):
    view = _viewport(qt_app)
    try:
        _click(view, "a")
        assert view.session.set_layer_visibility("background", False) is True
        assert view._items == {}

        view._marquee_selection_before = ("a",)
        view._marquee_primary_before = "a"
        assert view._apply_marquee_selection(
            QPointF(-25, -25), QPointF(25, 25), Qt.KeyboardModifier.ShiftModifier
        ) == ()
        assert view._select_all_visible() == ()
        assert view.session.selection.ids == ()
    finally:
        view.close()