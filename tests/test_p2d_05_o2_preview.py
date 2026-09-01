"""Focused O-2 tests for safe asset reuse, incremental refresh and frame parity."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import pytest
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from src.core.parallax_camera import OrthographicCamera
from src.core.scene_asset_library import sha256_file
from src.core.scene_authoring_groups import object_is_effectively_visible
from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_order import ordered_scene_objects
from src.core.scene_authoring_preview import (
    ProjectedSceneObject,
    ProjectedSceneSocket,
    _parallax,
    _socket_color,
    _world_points,
    build_scene_authoring_preview,
)
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneCameraAuthoringRecord,
    SceneGroupAuthoringRecordV2,
    SceneLayerAuthoringRecord,
    SceneLightSocketRecord,
    SceneObjectAuthoringRecord,
    SceneParallaxLayerRecord,
    SceneSocketRecord,
    SceneTransformRecord,
)
from src.ui import scene_authoring_viewport as viewport_module
from src.ui.scene_authoring_viewport import SceneAuthoringViewport


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    application = QApplication.instance()
    return application if isinstance(application, QApplication) else QApplication([])


def _write_png(path: Path, color: str) -> None:
    image = QImage(8, 8, QImage.Format.Format_RGBA8888)
    image.fill(QColor(color))
    path.parent.mkdir(parents=True, exist_ok=True)
    assert image.save(str(path))


def _transform(x: float = 0.0, y: float = 0.0) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _document(
    asset: AssetReferenceRecord,
    *,
    objects: list[SceneObjectAuthoringRecord] | None = None,
    groups: list[SceneGroupAuthoringRecordV2] | None = None,
    sockets: list[SceneSocketRecord] | None = None,
) -> SceneAuthoringDocumentV2:
    return SceneAuthoringDocumentV2(
        metadata=SceneAuthoringMetadataRecord(
            name="o2", generator="tests", app_version="0"
        ),
        project=ProjectReferenceRecord(sha256="a" * 64),
        assets=[asset],
        layers=[
            SceneLayerAuthoringRecord(id="back", name="Back"),
            SceneLayerAuthoringRecord(id="front", name="Front"),
        ],
        objects=objects
        or [
            SceneObjectAuthoringRecord(
                id="a", asset_id=asset.id, layer_id="back", transform=_transform()
            ),
            SceneObjectAuthoringRecord(
                id="b",
                asset_id=asset.id,
                layer_id="front",
                transform=_transform(20, 10),
            ),
        ],
        groups=groups or [],
        camera=SceneCameraAuthoringRecord(
            position=PointRecord(x=3.0, y=4.0), zoom=1.25
        ),
        parallax_layers=[
            SceneParallaxLayerRecord(
                layer_id="back", depth=0.2, translation_strength=0.7, zoom_strength=0.8
            ),
            SceneParallaxLayerRecord(
                layer_id="front", depth=0.8, translation_strength=0.9, zoom_strength=0.9
            ),
        ],
        sockets=sockets or [],
    )


def test_viewport_reuses_only_validated_pixmap_and_reloads_after_revision(
    qt_app: QApplication, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    asset_path = tmp_path / "project" / "assets" / "a.png"
    _write_png(asset_path, "#2aa7ff")
    original_bytes = asset_path.read_bytes()
    asset = AssetReferenceRecord(
        id="asset", path="assets/a.png", sha256=sha256_file(asset_path)
    )
    session = SceneAuthoringSession(SceneAuthoringModel(_document(asset)))
    calls: list[Path] = []
    original_loader = SceneAuthoringViewport._load_asset_pixmap

    def counted_loader(path: Path):
        calls.append(path)
        return original_loader(path)

    monkeypatch.setattr(
        SceneAuthoringViewport, "_load_asset_pixmap", staticmethod(counted_loader)
    )
    view = SceneAuthoringViewport(session, project_root=tmp_path / "project")
    try:
        assert len(calls) == 1
        view.sync()
        assert len(calls) == 1
        assert len(view._asset_pixmap_cache) == 1

        # Disable the asynchronous watcher for this deterministic direct probe.
        view._asset_watcher.removePaths(view._asset_watcher.files())
        _write_png(asset_path, "#ff5d63")
        view.sync()
        assert len(calls) == 1
        assert not view._asset_pixmap_cache
        assert any("hash mismatch" in message for message in view._asset_diagnostics)

        asset_path.write_bytes(original_bytes)
        view.sync()
        assert len(calls) == 2
        assert not view._asset_diagnostics
        assert len(view._asset_pixmap_cache) == 1
    finally:
        view.close()
        qt_app.processEvents()


def test_viewport_transform_refresh_touches_only_changed_object(
    qt_app: QApplication, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    asset_path = tmp_path / "project" / "assets" / "a.png"
    _write_png(asset_path, "#2aa7ff")
    asset = AssetReferenceRecord(
        id="asset", path="assets/a.png", sha256=sha256_file(asset_path)
    )
    session = SceneAuthoringSession(SceneAuthoringModel(_document(asset)))
    view = SceneAuthoringViewport(session, project_root=tmp_path / "project")
    positions: list[str] = []
    original_set_pos = viewport_module.SceneObjectGraphicsItem.setPos

    def counted_set_pos(item, *args):
        positions.append(item.object_id)
        return original_set_pos(item, *args)

    monkeypatch.setattr(
        viewport_module.SceneObjectGraphicsItem, "setPos", counted_set_pos
    )
    try:
        session.update_transform("a", _transform(44.0, 12.0))
        assert positions == ["a"]
        assert view._items["a"].pos().x() == pytest.approx(44.0)
        assert view._items["b"].pos().x() == pytest.approx(20.0)
    finally:
        view.close()
        qt_app.processEvents()


def _legacy_frame(
    document: SceneAuthoringDocumentV2,
    viewport_size: tuple[float, float],
    geometries: Mapping[str, tuple[tuple[float, float], ...]],
    isolated_group_id: str | None,
):
    camera = OrthographicCamera(
        viewport_size=viewport_size,
        position=(float(document.camera.position.x), float(document.camera.position.y)),
        zoom=float(document.camera.zoom),
    )
    layers = {item.id: item for item in document.layers}
    objects: list[ProjectedSceneObject] = []
    for item in ordered_scene_objects(document):
        layers[item.layer_id]
        if not object_is_effectively_visible(
            document, item.id, isolated_group_id=isolated_group_id
        ):
            continue
        world = _world_points(item, geometries.get(item.id, ()))
        if not world:
            continue
        parallax = _parallax(document, item.layer_id)
        objects.append(
            ProjectedSceneObject(
                object_id=item.id,
                layer_id=item.layer_id,
                points=tuple(camera.project(point, parallax) for point in world),
                origin=camera.project(
                    (
                        float(item.transform.position.x),
                        float(item.transform.position.y),
                    ),
                    parallax,
                ),
                zoom=camera.effective_zoom(parallax),
            )
        )
    sockets: list[ProjectedSceneSocket] = []
    for socket in document.sockets:
        if not layers[socket.layer_id].visible:
            continue
        sockets.append(
            ProjectedSceneSocket(
                socket_id=socket.id,
                socket_type=socket.type,
                position=camera.project(
                    (float(socket.position.x), float(socket.position.y)),
                    _parallax(document, socket.layer_id),
                ),
                color=_socket_color(socket),
            )
        )
    return tuple(objects), tuple(sockets)


def test_preview_frame_is_equivalent_to_pre_optimization_oracle() -> None:
    asset = AssetReferenceRecord(id="asset", path="assets/a.png", sha256="a" * 64)
    document = _document(
        asset,
        groups=[
            SceneGroupAuthoringRecordV2(id="root", name="Root", members=["a"]),
            SceneGroupAuthoringRecordV2(
                id="child", name="Child", members=["b"], parent_group_id="root"
            ),
        ],
        sockets=[
            SceneLightSocketRecord(
                id="light",
                layer_id="front",
                position=Point3Record(x=15.0, y=5.0, z=0.0),
                color="#abcdef",
            )
        ],
    )
    geometries = {
        "a": ((-4.0, -2.0), (4.0, -2.0), (4.0, 2.0), (-4.0, 2.0)),
        "b": ((-3.0, -3.0), (3.0, -3.0), (3.0, 3.0), (-3.0, 3.0)),
    }
    for isolated_group_id in (None, "root"):
        optimized = build_scene_authoring_preview(
            document,
            (640.0, 480.0),
            geometries,
            isolated_group_id=isolated_group_id,
        )
        expected_objects, expected_sockets = _legacy_frame(
            document, (640.0, 480.0), geometries, isolated_group_id
        )
        assert optimized.objects == expected_objects
        assert optimized.sockets == expected_sockets


def test_viewport_prunes_removed_asset_and_reloads_after_restore(
    qt_app: QApplication, tmp_path: Path
) -> None:
    asset_path = tmp_path / "project" / "assets" / "a.png"
    _write_png(asset_path, "#2aa7ff")
    asset = AssetReferenceRecord(
        id="asset", path="assets/a.png", sha256=sha256_file(asset_path)
    )
    session = SceneAuthoringSession(SceneAuthoringModel(_document(asset)))
    view = SceneAuthoringViewport(session, project_root=tmp_path / "project")
    try:
        assert len(view._asset_pixmap_cache) == 1
        view._asset_watcher.removePaths(view._asset_watcher.files())
        asset_path.unlink()
        view.sync()
        assert not view._asset_pixmap_cache
        assert any(
            "asset file is missing" in message
            for message in view._asset_diagnostics
        )

        _write_png(asset_path, "#2aa7ff")
        view.sync()
        assert len(view._asset_pixmap_cache) == 1
        assert not view._asset_diagnostics
    finally:
        view.close()
        qt_app.processEvents()


def test_viewport_selection_refresh_does_not_rebuild_scene(
    qt_app: QApplication, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    asset_path = tmp_path / "project" / "assets" / "a.png"
    _write_png(asset_path, "#2aa7ff")
    asset = AssetReferenceRecord(
        id="asset", path="assets/a.png", sha256=sha256_file(asset_path)
    )
    session = SceneAuthoringSession(SceneAuthoringModel(_document(asset)))
    view = SceneAuthoringViewport(session, project_root=tmp_path / "project")
    sync_calls: list[bool] = []
    original_sync = view.sync

    def counted_sync() -> None:
        sync_calls.append(True)
        original_sync()

    monkeypatch.setattr(view, "sync", counted_sync)
    try:
        session.set_selection(["a"], "a")
        assert sync_calls == []
        assert view._items["a"]._selected is True
        assert view._items["b"]._selected is False
    finally:
        view.close()
        qt_app.processEvents()


def test_viewport_group_membership_uses_structural_fallback(
    qt_app: QApplication, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    asset_path = tmp_path / "project" / "assets" / "a.png"
    _write_png(asset_path, "#2aa7ff")
    asset = AssetReferenceRecord(
        id="asset", path="assets/a.png", sha256=sha256_file(asset_path)
    )
    document = _document(
        asset,
        groups=[SceneGroupAuthoringRecordV2(id="group", name="Group", members=["a"])],
    )
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    view = SceneAuthoringViewport(session, project_root=tmp_path / "project")
    sync_calls: list[bool] = []
    original_sync = view.sync

    def counted_sync() -> None:
        sync_calls.append(True)
        original_sync()

    monkeypatch.setattr(view, "sync", counted_sync)
    try:
        assert session.add_objects_to_group("group", ["b"]) is True
        assert sync_calls == [True]
    finally:
        view.close()
        qt_app.processEvents()


def test_viewport_camera_and_parallax_refresh_without_rebuild(
    qt_app: QApplication, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    asset_path = tmp_path / "project" / "assets" / "a.png"
    _write_png(asset_path, "#2aa7ff")
    asset = AssetReferenceRecord(
        id="asset", path="assets/a.png", sha256=sha256_file(asset_path)
    )
    session = SceneAuthoringSession(SceneAuthoringModel(_document(asset)))
    view = SceneAuthoringViewport(session, project_root=tmp_path / "project")
    sync_calls: list[bool] = []
    original_sync = view.sync
    before_items = dict(view._items)

    def counted_sync() -> None:
        sync_calls.append(True)
        original_sync()

    monkeypatch.setattr(view, "sync", counted_sync)
    try:
        assert session.set_camera(
            SceneCameraAuthoringRecord(position=PointRecord(x=10.0, y=-6.0), zoom=1.5)
        ) is True
        assert sync_calls == []
        assert all(
            view._items[object_id] is item
            for object_id, item in before_items.items()
        )

        assert session.set_parallax_layer(
            SceneParallaxLayerRecord(
                layer_id="back", depth=0.6, translation_strength=0.8, zoom_strength=0.9
            )
        ) is True
        assert sync_calls == []
        assert all(
            view._items[object_id] is item
            for object_id, item in before_items.items()
        )
    finally:
        view.close()
        qt_app.processEvents()


def test_viewport_sync_preserves_navigation_center(
    qt_app: QApplication, tmp_path: Path
) -> None:
    asset_path = tmp_path / "project" / "assets" / "a.png"
    _write_png(asset_path, "#2aa7ff")
    asset = AssetReferenceRecord(
        id="asset", path="assets/a.png", sha256=sha256_file(asset_path)
    )
    session = SceneAuthoringSession(SceneAuthoringModel(_document(asset)))
    view = SceneAuthoringViewport(session, project_root=tmp_path / "project")
    view.resize(640, 480)
    view.show()
    qt_app.processEvents()
    try:
        before_center = view.navigation_center
        for _ in range(3):
            view.sync()
            qt_app.processEvents()
        after_center = view.navigation_center
        assert after_center.x() == pytest.approx(before_center.x())
        assert after_center.y() == pytest.approx(before_center.y())
    finally:
        view.close()
        qt_app.processEvents()
