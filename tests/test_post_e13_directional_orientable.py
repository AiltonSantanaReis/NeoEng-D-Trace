"""Behavioral coverage for post-E13 directional lights and oriented sockets."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QApplication

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.core.scene_lighting import (
    SceneDirectionalLight,
    SceneLightingMaterial,
    SceneLightingSettings,
    shade_color,
)
from src.exporters.scene_authoring_export import build_scene_authoring_export
from src.persistence.scene_authoring_io import serialize_scene_authoring
from src.persistence.project_schema import Point3Record
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    SceneAuthoringDocumentV1,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneLightSocketRecord,
    SceneVfxSocketRecord,
    upgrade_scene_authoring_document,
)
from src.ui.scene_authoring_inspector import SceneAuthoringInspector
from src.ui.scene_authoring_viewport import (
    SceneAuthoringViewport,
    SceneSocketGraphicsItem,
)

SHA = "e" * 64


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _document() -> SceneAuthoringDocumentV2:
    base = SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="Directional authoring",
            generator="NeoEng-D-Trace",
            app_version="0.3.0",
        ),
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[],
        layers=[SceneLayerAuthoringRecord(id="layer", name="FX")],
        objects=[],
        groups=[],
    )
    return upgrade_scene_authoring_document(base)


def test_legacy_socket_payload_defaults_to_point_and_zero_rotation() -> None:
    legacy = SceneLightSocketRecord(
        id="lamp",
        layer_id="layer",
        position=Point3Record(x=10.0, y=20.0, z=0.0),
        color="#ffffff",
    ).model_dump()
    legacy.pop("kind")
    legacy.pop("rotation")

    restored = SceneLightSocketRecord.model_validate(legacy, strict=True)

    assert restored.kind == "point"
    assert restored.rotation == Point3Record(x=0.0, y=0.0, z=0.0)


def test_directional_light_changes_pixels_with_heading_and_preserves_shadow_rule() -> (
    None
):
    material = SceneLightingMaterial(albedo=(1.0, 1.0, 1.0))
    lit = SceneLightingSettings(
        ambient_intensity=0.0,
        lights=(SceneDirectionalLight("sun", direction_degrees=90.0),),
    )
    away = SceneLightingSettings(
        ambient_intensity=0.0,
        lights=(SceneDirectionalLight("sun", direction_degrees=270.0),),
    )

    lit_color, _, lit_sources = shade_color((0.0, 0.0), material, lit)
    away_color, _, away_sources = shade_color((0.0, 0.0), material, away)

    assert lit_color == (1.0, 1.0, 1.0)
    assert lit_sources == ("sun",)
    assert away_color == (0.0, 0.0, 0.0)
    assert away_sources == ()


def test_socket_rotation_is_undoable_and_viewport_resolves_directional_kind() -> None:
    socket = SceneLightSocketRecord(
        id="sun",
        layer_id="layer",
        position=Point3Record(x=20.0, y=30.0, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=90.0),
        kind="directional",
        color="#ffe082",
    )
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    assert session.add_socket(socket) is True
    assert (
        session.update_socket_rotation("sun", Point3Record(x=0.0, y=0.0, z=180.0))
        is True
    )
    assert session.document.sockets[0].rotation.z == 180.0
    assert session.undo() is True
    assert session.document.sockets[0].rotation.z == 90.0
    assert session.redo() is True


def test_scene_save_and_export_preserve_directional_socket_contract() -> None:
    document = _document().model_copy(
        update={
            "sockets": [
                SceneLightSocketRecord(
                    id="sun",
                    layer_id="layer",
                    position=Point3Record(x=1.0, y=2.0, z=0.0),
                    rotation=Point3Record(x=0.0, y=0.0, z=125.0),
                    kind="directional",
                    color="#ffe082",
                )
            ]
        }
    )
    persisted = json.loads(serialize_scene_authoring(document))
    exported = build_scene_authoring_export(document, target="generic")

    assert persisted["sockets"][0]["kind"] == "directional"
    assert persisted["sockets"][0]["rotation"]["z"] == 125.0
    assert exported["scene"]["sockets"][0]["kind"] == "directional"
    assert exported["scene"]["sockets"][0]["rotation"]["z"] == 125.0


def test_orientable_socket_handle_emits_real_rotation_gesture() -> None:
    class _Mouse:
        def __init__(self, point: QPointF) -> None:
            self._point = QPointF(point)

        def pos(self) -> QPointF:
            return QPointF(self._point)

        def scenePos(self) -> QPointF:
            return QPointF(self._point)

        def button(self) -> Qt.MouseButton:
            return Qt.MouseButton.LeftButton

        def buttons(self) -> Qt.MouseButton:
            return Qt.MouseButton.LeftButton

        def accept(self) -> None:
            pass

        def ignore(self) -> None:
            pass

    marker = SceneSocketGraphicsItem(
        "sun", "light", "#ffe082", rotation=0.0, orientable=True
    )
    rotations: list[float] = []
    finished: list[float] = []
    marker.rotated.connect(lambda _socket_id, value: rotations.append(value))
    marker.rotation_released.connect(lambda _socket_id, value: finished.append(value))

    marker.mousePressEvent(_Mouse(QPointF(31.0, 0.0)))
    marker.mouseMoveEvent(_Mouse(QPointF(0.0, 31.0)))
    marker.mouseReleaseEvent(_Mouse(QPointF(0.0, 31.0)))

    assert rotations
    assert rotations[-1] == pytest.approx(90.0)
    assert finished[-1] == pytest.approx(90.0)


def test_native_inspector_and_viewport_preserve_orientable_effects(
    qt_app: QApplication, tmp_path: Path
) -> None:
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    inspector = SceneAuthoringInspector(session)
    try:
        inspector.update_language("pt")
        inspector.socket_id.setText("sun")
        inspector.socket_type.setCurrentText("Luz")
        inspector.socket_light_kind.setCurrentText("Direcional")
        inspector.socket_x.setValue(20.0)
        inspector.socket_y.setValue(30.0)
        inspector.socket_rotation_z.setValue(90.0)
        inspector.add_socket_button.click()
        qt_app.processEvents()

        record = session.document.sockets[0]
        assert isinstance(record, SceneLightSocketRecord)
        assert record.kind == "directional"
        assert record.rotation.z == 90.0
        assert viewport._socket_items["sun"].boundingRect().width() > 18.0
        assert viewport._socket_items["sun"].rotation() == pytest.approx(90.0)

        lights = viewport._lighting_for_document().lights
        assert len(lights) == 1
        assert isinstance(lights[0], SceneDirectionalLight)
        assert lights[0].direction_degrees == 90.0
        assert inspector.socket_light_kind.itemText(1) == "Direcional"
        assert inspector.socket_rotation_z.toolTip()
    finally:
        inspector.close()
        viewport.close()
        qt_app.processEvents()


def test_vfx_preview_and_postprocess_follow_authored_rotation(
    qt_app: QApplication, tmp_path: Path
) -> None:
    document = _document().model_copy(
        update={
            "sockets": [
                SceneVfxSocketRecord(
                    id="wind",
                    layer_id="layer",
                    position=Point3Record(x=40.0, y=50.0, z=0.0),
                    rotation=Point3Record(x=0.0, y=0.0, z=35.0),
                    effect_id="wind-fx",
                )
            ]
        }
    )
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    viewport = SceneAuthoringViewport(session, project_root=tmp_path)
    viewport.resize(640, 480)
    viewport.show()
    qt_app.processEvents()
    try:
        assert viewport._socket_items["wind"].rotation() == pytest.approx(35.0)
        assert viewport._socket_items["wind"].boundingRect().width() > 18.0
        assert viewport._particle_items["wind"].rotation() == pytest.approx(35.0)
    finally:
        viewport.close()
        qt_app.processEvents()
