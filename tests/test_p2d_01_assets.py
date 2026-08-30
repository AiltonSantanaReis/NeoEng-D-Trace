"""P2D-01A coverage for controlled scene assets and real viewport rendering."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

from src.core.scene_asset_library import (
    prepare_scene_asset,
    resolve_scene_asset,
    sha256_file,
)
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


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _document(asset: AssetReferenceRecord) -> SceneAuthoringDocumentV1:
    return SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="P2D-01A", generator="NeoEng-D-Trace", app_version="0.2.0"
        ),
        project=ProjectReferenceRecord(sha256="a" * 64),
        assets=[asset],
        layers=[SceneLayerAuthoringRecord(id="background", name="Background")],
        objects=[
            SceneObjectAuthoringRecord(
                id="object",
                asset_id=asset.id,
                layer_id="background",
                transform=SceneTransformRecord(
                    position=Point3Record(x=40.0, y=40.0, z=0.0),
                    rotation=Point3Record(x=0.0, y=0.0, z=0.0),
                    scale=Point3Record(x=1.0, y=1.0, z=1.0),
                    pivot=PointRecord(x=0.5, y=0.5),
                ),
            )
        ],
        groups=[],
    )


def test_external_asset_is_copied_atomically_and_reused_by_hash(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    source = tmp_path / "external source" / "Original asset.PNG"
    source.parent.mkdir()
    source.write_bytes(b"original asset payload")

    prepared = prepare_scene_asset(source, project_root)
    repeated = prepare_scene_asset(source, project_root)

    assert prepared.path.startswith("assets/scene/")
    assert prepared.source_path == str(source.resolve())
    assert prepared.resolved_path.is_file()
    assert prepared.resolved_path.read_bytes() == source.read_bytes()
    assert prepared.sha256 == hashlib.sha256(source.read_bytes()).hexdigest()
    assert repeated == prepared
    assert len(list((project_root / "assets" / "scene").glob("*.png"))) == 1


def test_project_asset_keeps_relative_reference_without_external_provenance(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    asset = project_root / "assets" / "scene" / "internal.png"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"internal asset payload")

    prepared = prepare_scene_asset(asset, project_root)

    assert prepared.path == "assets/scene/internal.png"
    assert prepared.source_path is None
    assert prepared.resolved_path == asset.resolve()


def test_asset_resolution_reports_missing_and_hash_drift_without_fallback(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    asset_path = root / "assets" / "scene" / "tamper.png"
    asset_path.parent.mkdir(parents=True)
    asset_path.write_bytes(b"known bytes")
    record = AssetReferenceRecord(
        id="tamper",
        path="assets/scene/tamper.png",
        sha256=sha256_file(asset_path),
    )

    assert resolve_scene_asset(record, root) == (asset_path.resolve(), None)
    asset_path.write_bytes(b"changed bytes")
    resolved, issue = resolve_scene_asset(record, root)
    assert resolved is None
    assert issue is not None and "hash mismatch" in issue

    asset_path.unlink()
    resolved, issue = resolve_scene_asset(record, root)
    assert resolved is None
    assert issue is not None and "missing" in issue


def test_asset_provenance_is_optional_and_validated() -> None:
    record = AssetReferenceRecord(
        id="external",
        path="assets/scene/external.png",
        sha256="b" * 64,
        source_path=r"C:\external\Original asset.png",
    )
    assert record.source_path == r"C:\external\Original asset.png"
    with pytest.raises(ValueError, match="non-empty"):
        AssetReferenceRecord(
            id="invalid",
            path="assets/scene/invalid.png",
            sha256="c" * 64,
            source_path=" ",
        )


def test_viewport_renders_verified_raster_asset_instead_of_only_polygon(
    qt_app, tmp_path: Path
) -> None:
    asset_path = tmp_path / "assets" / "scene" / "visible.png"
    asset_path.parent.mkdir(parents=True)
    source = QImage(8, 6, QImage.Format.Format_RGBA8888)
    source.fill(QColor("#ff0000"))
    assert source.save(str(asset_path))
    record = AssetReferenceRecord(
        id="visible",
        path="assets/scene/visible.png",
        sha256=sha256_file(asset_path),
    )
    viewport = SceneAuthoringViewport(
        SceneAuthoringSession(SceneAuthoringModel(_document(record))),
        project_root=tmp_path,
    )
    try:
        viewport.set_geometry(
            "object",
            [(-4.0, -3.0), (4.0, -3.0), (4.0, 3.0), (-4.0, 3.0)],
        )
        assert viewport._items["object"]._pixmap is not None
        frame = QImage(100, 100, QImage.Format.Format_RGBA8888)
        frame.fill(0xFF111820)
        painter = QPainter(frame)
        viewport.graphics_scene.render(
            painter, QRectF(0, 0, 100, 100), QRectF(0, 0, 100, 100)
        )
        painter.end()
        center = frame.pixelColor(40, 40)
        assert center.red() > 200
        assert center.green() < 80
    finally:
        viewport.close()
        qt_app.processEvents()


def test_viewport_loads_original_svg_and_reports_missing_asset(
    qt_app, tmp_path: Path
) -> None:
    svg_path = tmp_path / "assets" / "scene" / "original.svg"
    svg_path.parent.mkdir(parents=True)
    svg_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="10" '
        'viewBox="0 0 12 10"><rect width="12" height="10" fill="#00ff00"/></svg>',
        encoding="utf-8",
    )
    record = AssetReferenceRecord(
        id="svg",
        path="assets/scene/original.svg",
        sha256=sha256_file(svg_path),
    )
    viewport = SceneAuthoringViewport(
        SceneAuthoringSession(SceneAuthoringModel(_document(record))),
        project_root=tmp_path,
    )
    messages: list[str] = []
    viewport.status_message.connect(messages.append)
    try:
        assert viewport._items["object"]._pixmap is not None
        assert viewport._image_size(svg_path) == (12.0, 10.0)
        missing = record.model_copy(update={"path": "assets/scene/missing.svg"})
        viewport.session.model.document = _document(missing)
        viewport.sync()
        assert any("missing" in message for message in messages)
    finally:
        viewport.close()
        qt_app.processEvents()
