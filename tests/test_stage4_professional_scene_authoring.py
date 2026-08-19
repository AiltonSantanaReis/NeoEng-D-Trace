"""Real contract, preview and UI tests for professional scenario stage 4."""

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
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneCameraAuthoringRecord,
    SceneGroupAuthoringRecord,
    SceneLayerAuthoringRecord,
    SceneLightSocketRecord,
    SceneObjectAuthoringRecord,
    SceneParallaxLayerRecord,
    SceneTransformRecord,
    SceneTriggerSocketRecord,
    SceneVfxSocketRecord,
    upgrade_scene_authoring_document,
    validate_scene_authoring_document,
)
from src.ui.scene_authoring_inspector import SceneAuthoringInspector
from src.ui.scene_authoring_viewport import SceneAuthoringViewport, SceneTransformGizmo

SHA = "b" * 64


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _transform(x: float = 10.0, y: float = 20.0) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _v1() -> SceneAuthoringDocumentV1:
    return SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="Stage 4 test", generator="NeoEng-D-Trace", app_version="0.2.0"
        ),
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[AssetReferenceRecord(id="asset", path="assets/a.png", sha256=SHA)],
        layers=[SceneLayerAuthoringRecord(id="background", name="Background")],
        objects=[
            SceneObjectAuthoringRecord(
                id="tree",
                asset_id="asset",
                layer_id="background",
                transform=_transform(),
            )
        ],
        groups=[],
    )


def _v2() -> SceneAuthoringDocumentV2:
    return upgrade_scene_authoring_document(_v1())


def test_v1_is_preserved_and_upgrade_is_explicit() -> None:
    v1 = _v1()
    v2 = upgrade_scene_authoring_document(v1)
    assert v1.schema_version == 1
    assert v2.schema_version == 2
    assert v2.parallax_layers == []
    assert v2.sockets == []
    assert v1.model_dump() == _v1().model_dump()


def test_v2_accepts_typed_sockets_and_rejects_invalid_references() -> None:
    light = SceneLightSocketRecord(
        id="lamp",
        layer_id="background",
        position=Point3Record(x=1, y=2, z=0),
        color="#FFE082",
        intensity=1.5,
        radius=80,
    )
    vfx = SceneVfxSocketRecord(
        id="smoke",
        layer_id="background",
        position=Point3Record(x=3, y=4, z=0),
        effect_id="smoke",
        scale=0.75,
    )
    trigger = SceneTriggerSocketRecord(
        id="enter",
        layer_id="background",
        position=Point3Record(x=5, y=6, z=0),
        event_id="enter_area",
        size=Point3Record(x=32, y=16, z=1),
    )
    document = _v2().model_copy(
        update={
            "parallax_layers": [
                SceneParallaxLayerRecord(
                    layer_id="background",
                    depth=0.8,
                    translation_strength=1.0,
                    zoom_strength=0.5,
                )
            ],
            "sockets": [light, vfx, trigger],
        }
    )
    assert document.sockets[0].color == "#ffe082"
    assert {socket.type for socket in document.sockets} == {"light", "vfx", "trigger"}
    with pytest.raises(ValueError, match="unknown layer"):
        SceneAuthoringDocumentV2.model_validate(
            document.model_copy(
                update={
                    "parallax_layers": [SceneParallaxLayerRecord(layer_id="missing")]
                }
            ),
            strict=True,
        )
    with pytest.raises(ValueError, match="between 0 and 1"):
        SceneParallaxLayerRecord(layer_id="background", depth=1.1)
    with pytest.raises(ValueError, match="String should match pattern"):
        SceneLightSocketRecord(
            id="bad",
            layer_id="background",
            position=Point3Record(x=0, y=0, z=0),
            color="red",
        )


def test_preview_projection_is_deterministic_and_depth_aware() -> None:
    foreground = SceneParallaxLayerRecord(
        layer_id="background", depth=0.0, translation_strength=1.0, zoom_strength=1.0
    )
    far = SceneParallaxLayerRecord(
        layer_id="background", depth=1.0, translation_strength=1.0, zoom_strength=1.0
    )
    first = _v2().model_copy(
        update={
            "camera": SceneCameraAuthoringRecord(
                position=PointRecord(x=100, y=0), zoom=2.0
            ),
            "parallax_layers": [foreground],
        }
    )
    second = build_scene_authoring_preview(
        first, (800, 600), {"tree": [(-5, -5), (5, 5)]}
    )
    third = build_scene_authoring_preview(
        first, (800, 600), {"tree": [(-5, -5), (5, 5)]}
    )
    assert second == third
    far_document = first.model_copy(update={"parallax_layers": [far]})
    far_frame = build_scene_authoring_preview(
        far_document, (800, 600), {"tree": [(-5, -5), (5, 5)]}
    )
    assert second.objects[0].origin != far_frame.objects[0].origin
    assert far_frame.objects[0].origin == (410.0, 320.0)


def test_session_stage4_operations_are_undoable() -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_v2()))
    session.set_parallax_layer(
        SceneParallaxLayerRecord(layer_id="background", depth=0.5)
    )
    assert session.document.parallax_layers[0].depth == 0.5
    socket = SceneLightSocketRecord(
        id="lamp",
        layer_id="background",
        position=Point3Record(x=1, y=2, z=0),
        color="#ffffff",
    )
    assert session.add_socket(socket) is True
    assert session.update_socket_position("lamp", Point3Record(x=8, y=9, z=0)) is True
    assert session.document.sockets[0].position.x == 8
    assert session.undo() is True
    assert session.document.sockets[0].position.x == 1
    assert session.redo() is True
    assert session.remove_socket("lamp") is True
    assert session.undo() is True
    assert session.document.sockets[0].id == "lamp"


def test_professional_inspector_and_viewport_edit_stage4_state(
    qt_app: QApplication, tmp_path: Path
) -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_v2()))
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    inspector = SceneAuthoringInspector(session)
    try:
        viewport.resize(640, 480)
        viewport.set_geometry("tree", [(-20, -20), (20, -20), (20, 20), (-20, 20)])
        viewport.set_preview_enabled(True)
        inspector.show()
        viewport.show()
        qt_app.processEvents()
        assert viewport.is_preview_enabled() is True
        assert inspector.stage4_group.isEnabled()
        inspector.camera_x.setValue(42.0)
        inspector.camera_apply_button.click()
        assert session.document.camera.position.x == 42.0
        inspector.parallax_depth.setValue(0.75)
        inspector.parallax_apply_button.click()
        assert session.document.parallax_layers[0].depth == 0.75
        inspector.socket_id.setText("lamp")
        inspector.socket_type.setCurrentText("light")
        inspector.socket_x.setValue(12.0)
        inspector.socket_y.setValue(18.0)
        inspector.add_socket_button.click()
        assert session.document.sockets[0].id == "lamp"
        assert viewport._socket_items["lamp"].pos().x() != 0.0
        inspector.socket_x.setValue(24.0)
        inspector.update_socket_button.click()
        assert session.document.sockets[0].position.x == 24.0
        inspector.remove_socket_button.click()
        assert session.document.sockets == []
    finally:
        inspector.close()
        viewport.close()
        qt_app.processEvents()


def test_viewport_gizmo_modes_and_preview_fallbacks(
    qt_app: QApplication, tmp_path: Path
) -> None:
    v1_session = SceneAuthoringSession(SceneAuthoringModel(_v1()))
    v1_viewport = SceneAuthoringViewport(v1_session, project_root=tmp_path)
    gizmo = SceneTransformGizmo()
    try:
        v1_viewport.resize(320, 240)
        v1_viewport.set_geometry("tree", [(-8, -8), (8, -8), (8, 8), (-8, 8)])
        assert v1_viewport._camera().zoom == 1.0
        assert v1_viewport._layer_parallax("background").depth == 0.0
        assert v1_viewport._project_position(
            Point3Record(x=3, y=4, z=0), "background"
        ) == QPointF(3, 4)
        v1_viewport.set_preview_enabled(True)
        assert v1_viewport._layer_parallax("missing").depth == 0.0
        assert v1_viewport._world_position(
            v1_viewport._project_position(Point3Record(x=3, y=4, z=0), "background"),
            "background",
        ).x() == pytest.approx(3.0)
        v1_viewport.set_preview_enabled(False)
        assert [
            gizmo._mode_for(point)
            for point in (
                QPointF(35, 35),
                QPointF(45, 0),
                QPointF(30, 0),
                QPointF(0, -30),
                QPointF(0, 0),
            )
        ] == ["scale", "rotate", "translate_x", "translate_y", "translate"]
    finally:
        v1_viewport.close()
        qt_app.processEvents()


def test_viewport_gizmo_gestures_and_model_error_paths(
    qt_app: QApplication, tmp_path: Path
) -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_v2()))
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    try:
        viewport.resize(640, 480)
        viewport.set_geometry("tree", [(-20, -20), (20, -20), (20, 20), (-20, 20)])
        viewport._object_pressed(
            "tree", QPointF(10, 10), Qt.KeyboardModifier.NoModifier
        )
        viewport._object_moved("missing", QPointF(12, 12))
        viewport._object_moved("tree", QPointF(18, 14))
        viewport._object_released("tree", QPointF(18, 14))
        for mode, start, current in (
            ("translate_x", QPointF(10, 10), QPointF(30, 20)),
            ("translate_y", QPointF(10, 10), QPointF(30, 20)),
            ("scale", QPointF(10, 10), QPointF(30, 30)),
            ("rotate", QPointF(10, 10), QPointF(20, 20)),
        ):
            viewport._gizmo_started(mode, start)
            viewport._gizmo_changed(mode, current)
            viewport._gizmo_finished(mode, current)
        assert session.document.objects[0].transform.scale.x > 0
        assert viewport.undo() is True
        assert viewport.redo() is True
    finally:
        viewport.close()
        qt_app.processEvents()

    model = SceneAuthoringModel(_v1())
    model.clear_selection()
    model.transform_selected()
    with pytest.raises(ValueError, match="scale_factor"):
        model.transform_selected(scale_factor=0.0)
    with pytest.raises(ValueError, match="schema v2"):
        model.set_camera(SceneCameraAuthoringRecord())
    with pytest.raises(ValueError, match="schema v2"):
        model.add_socket(
            SceneLightSocketRecord(
                id="lamp",
                layer_id="background",
                position=Point3Record(x=0, y=0, z=0),
                color="#ffffff",
            )
        )


def test_v2_reference_validation_and_version_dispatch() -> None:
    def validate(update: dict[str, object]) -> None:
        SceneAuthoringDocumentV2.model_validate(
            _v2().model_copy(update=update), strict=True
        )

    duplicate_layer = SceneLayerAuthoringRecord(id="background", name="Duplicate")
    with pytest.raises(ValueError, match="layer IDs must be unique"):
        validate({"layers": [_v2().layers[0], duplicate_layer]})
    with pytest.raises(ValueError, match="unknown asset"):
        validate(
            {
                "objects": [
                    SceneObjectAuthoringRecord(
                        id="tree",
                        asset_id="missing",
                        layer_id="background",
                        transform=_transform(),
                    )
                ]
            }
        )
    with pytest.raises(ValueError, match="unknown layer"):
        validate(
            {
                "objects": [
                    SceneObjectAuthoringRecord(
                        id="tree",
                        asset_id="asset",
                        layer_id="missing",
                        transform=_transform(),
                    )
                ]
            }
        )
    with pytest.raises(ValueError, match="unknown object"):
        validate(
            {
                "groups": [
                    SceneGroupAuthoringRecord(
                        id="group", name="Group", members=["missing"]
                    )
                ]
            }
        )
    with pytest.raises(ValueError, match="parallax layer IDs"):
        validate(
            {
                "parallax_layers": [
                    SceneParallaxLayerRecord(layer_id="background"),
                    SceneParallaxLayerRecord(layer_id="background"),
                ]
            }
        )
    with pytest.raises(ValueError, match="parallax references unknown"):
        validate({"parallax_layers": [SceneParallaxLayerRecord(layer_id="missing")]})
    light = SceneLightSocketRecord(
        id="lamp",
        layer_id="background",
        position=Point3Record(x=0, y=0, z=0),
        color="#ffffff",
    )
    with pytest.raises(ValueError, match="socket IDs"):
        validate({"sockets": [light, light]})
    with pytest.raises(ValueError, match="socket references unknown layer"):
        validate(
            {
                "sockets": [
                    light.model_copy(update={"id": "lamp2", "layer_id": "missing"})
                ]
            }
        )
    with pytest.raises(ValueError, match="socket references unknown object"):
        validate(
            {
                "sockets": [
                    light.model_copy(update={"id": "lamp2", "object_id": "missing"})
                ]
            }
        )
    assert isinstance(
        validate_scene_authoring_document(_v1().model_dump()), SceneAuthoringDocumentV1
    )
    assert isinstance(
        validate_scene_authoring_document(_v2().model_dump()), SceneAuthoringDocumentV2
    )
    with pytest.raises(TypeError, match="mapping"):
        validate_scene_authoring_document("not a document")
    with pytest.raises(ValueError, match="unsupported"):
        validate_scene_authoring_document({"schema_version": 99})


def test_preview_filters_hidden_records_and_projects_all_socket_types() -> None:
    sockets = [
        SceneLightSocketRecord(
            id="lamp",
            layer_id="background",
            position=Point3Record(x=1, y=2, z=0),
            color="#ffffff",
        ),
        SceneVfxSocketRecord(
            id="smoke",
            layer_id="background",
            position=Point3Record(x=3, y=4, z=0),
            effect_id="smoke",
        ),
        SceneTriggerSocketRecord(
            id="trigger",
            layer_id="background",
            position=Point3Record(x=5, y=6, z=0),
            event_id="enter",
            size=Point3Record(x=8, y=8, z=1),
        ),
    ]
    document = _v2().model_copy(update={"sockets": sockets})
    frame = build_scene_authoring_preview(
        document, (800, 600), {"tree": [(-2, -2), (2, 2)]}
    )
    assert {socket.socket_type for socket in frame.sockets} == {
        "light",
        "vfx",
        "trigger",
    }
    assert {socket.color for socket in frame.sockets} == {
        "#ffffff",
        "#c78cff",
        "#ffcf65",
    }
    hidden = document.model_copy(
        update={"layers": [document.layers[0].model_copy(update={"visible": False})]}
    )
    assert build_scene_authoring_preview(hidden, (800, 600), {}).objects == ()
    assert build_scene_authoring_preview(hidden, (800, 600), {}).sockets == ()
    with pytest.raises(ValueError, match="schema v2"):
        build_scene_authoring_preview(_v1(), (800, 600), {})
    with pytest.raises(ValueError, match="exactly two"):
        build_scene_authoring_preview(document, (800,), {})
    with pytest.raises(ValueError, match="positive"):
        build_scene_authoring_preview(document, (0, 600), {})
    with pytest.raises(ValueError, match="object geometry"):
        build_scene_authoring_preview(document, (800, 600), {"tree": [(1,)]})


def test_inspector_v1_and_empty_socket_states_are_safe(qt_app: QApplication) -> None:
    v1_inspector = SceneAuthoringInspector(
        SceneAuthoringSession(SceneAuthoringModel(_v1()))
    )
    v2_session = SceneAuthoringSession(SceneAuthoringModel(_v2()))
    v2_inspector = SceneAuthoringInspector(v2_session)
    try:
        assert not v1_inspector.stage4_group.isEnabled()
        v1_inspector._refresh_stage4_controls()
        v2_inspector.socket_combo.clear()
        v2_inspector._refresh_socket_fields()
        v2_inspector._update_socket()
        v2_inspector._remove_socket()
        v2_inspector.layer_combo.clear()
        v2_inspector._apply_parallax()
        v2_inspector._apply_camera()
        v2_inspector._apply_camera()
        v2_inspector.socket_id.setText("vfx")
        v2_inspector.socket_type.setCurrentText("vfx")
        v2_inspector._add_socket()
        assert v2_session.document.sockets[0].type == "vfx"
        v2_inspector.socket_id.setText("trigger")
        v2_inspector.socket_type.setCurrentText("trigger")
        v2_inspector._add_socket()
        assert {socket.type for socket in v2_session.document.sockets} == {
            "vfx",
            "trigger",
        }
    finally:
        v1_inspector.close()
        v2_inspector.close()
        qt_app.processEvents()


def test_model_stage4_missing_references_fail_closed() -> None:
    model = SceneAuthoringModel(_v2())
    with pytest.raises(KeyError, match="missing"):
        model.set_parallax_layer(SceneParallaxLayerRecord(layer_id="missing"))
    with pytest.raises(KeyError, match="missing"):
        model.add_socket(
            SceneLightSocketRecord(
                id="lamp",
                layer_id="missing",
                position=Point3Record(x=0, y=0, z=0),
                color="#ffffff",
            )
        )
    with pytest.raises(KeyError, match="missing"):
        model.update_socket_position("missing", Point3Record(x=0, y=0, z=0))
    with pytest.raises(KeyError, match="missing"):
        model.remove_socket("missing")
