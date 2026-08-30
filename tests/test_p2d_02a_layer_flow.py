from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QApplication

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_preview import build_scene_authoring_preview
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_io import (
    load_scene_authoring_v2,
    save_scene_authoring,
)
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
    upgrade_scene_authoring_document,
)
from src.ui.scene_authoring_layer_stack import SceneAuthoringLayerStack
from src.ui.scene_authoring_viewport import SceneAuthoringViewport

SHA = "c" * 64


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _transform(x: float, y: float, z: float = 0.0) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=z),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _document() -> SceneAuthoringDocumentV2:
    source = SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="P2D-02A flow", generator="NeoEng-D-Trace", app_version="0.2.0"
        ),
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[AssetReferenceRecord(id="asset", path="assets/a.png", sha256=SHA)],
        layers=[
            SceneLayerAuthoringRecord(id="back", name="Back"),
            SceneLayerAuthoringRecord(id="front", name="Front"),
        ],
        # Deliberately interleave layers to prove that layer order, not object
        # list coincidence, defines the preview and viewport order.
        objects=[
            SceneObjectAuthoringRecord(
                id="foreground_object",
                asset_id="asset",
                layer_id="front",
                transform=_transform(0.0, 0.0, 7.0),
            ),
            SceneObjectAuthoringRecord(
                id="background_a",
                asset_id="asset",
                layer_id="back",
                transform=_transform(0.0, 0.0, 3.0),
            ),
            SceneObjectAuthoringRecord(
                id="background_b",
                asset_id="asset",
                layer_id="back",
                transform=_transform(0.0, 0.0, 5.0),
            ),
        ],
        groups=[],
    )
    return upgrade_scene_authoring_document(source)


def _geometry() -> dict[str, list[tuple[float, float]]]:
    return {
        object_id: [(-30.0, -30.0), (30.0, -30.0), (30.0, 30.0), (-30.0, 30.0)]
        for object_id in ("foreground_object", "background_a", "background_b")
    }


def test_layer_order_is_observable_in_preview_and_viewport(
    qt_app: QApplication, tmp_path: Path
) -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    try:
        viewport.resize(640, 480)
        viewport.set_geometry("foreground_object", _geometry()["foreground_object"])
        viewport.set_geometry("background_a", _geometry()["background_a"])
        viewport.set_geometry("background_b", _geometry()["background_b"])
        qt_app.processEvents()

        assert list(viewport._items) == [
            "background_a",
            "background_b",
            "foreground_object",
        ]
        initial_z = {
            object_id: visual.zValue() for object_id, visual in viewport._items.items()
        }
        assert initial_z["background_a"] < initial_z["background_b"]
        assert initial_z["background_b"] < initial_z["foreground_object"]

        frame = build_scene_authoring_preview(session.document, (640, 480), _geometry())
        assert [item.object_id for item in frame.objects] == [
            "background_a",
            "background_b",
            "foreground_object",
        ]

        object_ids_before = [item.id for item in session.document.objects]
        positions_z_before = [
            item.transform.position.z for item in session.document.objects
        ]
        assert session.reorder_layer("front", 0) is True
        qt_app.processEvents()

        assert [layer.id for layer in session.document.layers] == ["front", "back"]
        assert list(viewport._items) == [
            "foreground_object",
            "background_a",
            "background_b",
        ]
        reordered_z = {
            object_id: visual.zValue() for object_id, visual in viewport._items.items()
        }
        assert reordered_z["foreground_object"] < reordered_z["background_a"]
        assert reordered_z["background_a"] < reordered_z["background_b"]
        reordered_frame = build_scene_authoring_preview(
            session.document, (640, 480), _geometry()
        )
        assert [item.object_id for item in reordered_frame.objects] == [
            "foreground_object",
            "background_a",
            "background_b",
        ]
        assert [item.id for item in session.document.objects] == object_ids_before
        assert [
            item.transform.position.z for item in session.document.objects
        ] == positions_z_before

        scene_path = tmp_path / "p2d-02a-roundtrip.ndtscene.json"
        save_scene_authoring(session.document, scene_path)
        loaded = load_scene_authoring_v2(scene_path, verify_assets=False)
        assert [layer.id for layer in loaded.layers] == ["front", "back"]
        assert [item.id for item in loaded.objects] == object_ids_before
        assert [
            item.transform.position.z for item in loaded.objects
        ] == positions_z_before
    finally:
        viewport.close()
        qt_app.processEvents()


def test_layer_stack_user_flow_visibility_lock_and_history(
    qt_app: QApplication, tmp_path: Path
) -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    stack = SceneAuthoringLayerStack(session)
    messages: list[str] = []
    viewport.status_message.connect(messages.append)
    try:
        viewport.resize(640, 480)
        for object_id, points in _geometry().items():
            viewport.set_geometry(object_id, points)
        stack.layer_list.setCurrentRow(1)
        qt_app.processEvents()
        assert stack.layer_list.currentItem().data(Qt.ItemDataRole.UserRole) == "front"

        stack.up_button.click()
        qt_app.processEvents()
        assert [layer.id for layer in session.document.layers] == ["front", "back"]
        assert stack.layer_list.currentRow() == 0
        assert stack.order_hint.text() == "Render order: Back → Front"

        stack.visible_box.click()
        qt_app.processEvents()
        assert not session.document.layers[0].visible
        assert "foreground_object" not in viewport._items
        stack.visible_box.click()
        qt_app.processEvents()
        assert session.document.layers[0].visible
        assert "foreground_object" in viewport._items

        stack.locked_box.click()
        qt_app.processEvents()
        assert session.document.layers[0].locked
        locked_document = session.document
        history_before_attempt = session.undo_count
        messages.clear()

        # This is the user action: select the visible object, then attempt to
        # drag it. Selection remains possible, but authoring is rejected safely.
        viewport._object_pressed(
            "foreground_object", QPointF(0.0, 0.0), Qt.KeyboardModifier.NoModifier
        )
        viewport._object_moved("foreground_object", QPointF(20.0, 20.0))
        qt_app.processEvents()
        assert session.document == locked_document
        assert session.undo_count == history_before_attempt
        assert viewport._gesture_start is None
        assert any("layer is locked" in message for message in messages)

        messages.clear()
        viewport._gizmo_started("translate", QPointF(0.0, 0.0))
        assert session.document == locked_document
        assert session._gesture_before is None
        assert any("layer is locked" in message for message in messages)

        assert viewport.undo() is True
        assert session.document.layers[0].locked is False
        assert viewport.redo() is True
        assert session.document.layers[0].locked is True
    finally:
        stack.close()
        viewport.close()
        qt_app.processEvents()
