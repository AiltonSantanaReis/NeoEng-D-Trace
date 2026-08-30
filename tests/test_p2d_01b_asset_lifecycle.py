"""P2D-01B coverage for asset library state and lifecycle actions."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from src.core.commands import CommandManager
from src.core.scenario_authoring import ScenarioAuthoringState
from src.core.scene_asset_library import inspect_scene_asset, sha256_file
from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.models.scene import Scene
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_io import save_scene_authoring
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
    upgrade_scene_authoring_document,
)
from src.ui.scenario_editor_window import ScenarioEditorWindow
from src.ui.scene_asset_panel import SceneAssetLibrary
from src.ui.scene_authoring_viewport import SceneAuthoringViewport


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def _write_image(path: Path, width: int, height: int, color: str) -> None:
    image = QImage(width, height, QImage.Format.Format_RGBA8888)
    image.fill(QColor(color))
    path.parent.mkdir(parents=True, exist_ok=True)
    assert image.save(str(path))


def _record(asset_id: str, path: Path) -> AssetReferenceRecord:
    return AssetReferenceRecord(
        id=asset_id,
        path=path.relative_to(path.parents[2]).as_posix(),
        sha256=sha256_file(path),
    )


def _document(
    assets: list[AssetReferenceRecord],
) -> SceneAuthoringDocumentV1:
    objects = []
    for asset in assets:
        repetitions = 2 if asset.id == "hero" else 1
        for _ in range(repetitions):
            index = len(objects)
            objects.append(
                SceneObjectAuthoringRecord(
                    id=f"object_{index}",
                    asset_id=asset.id,
                    layer_id="background",
                    transform=SceneTransformRecord(
                        position=Point3Record(x=40.0 + index * 80.0, y=50.0, z=0.0),
                        rotation=Point3Record(x=0.0, y=0.0, z=float(index)),
                        scale=Point3Record(x=1.0, y=1.0, z=1.0),
                        pivot=PointRecord(x=0.5, y=0.5),
                    ),
                )
            )
    return SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="P2D-01B", generator="NeoEng-D-Trace", app_version="0.2.0"
        ),
        project=ProjectReferenceRecord(sha256="a" * 64),
        assets=assets,
        layers=[SceneLayerAuthoringRecord(id="background", name="Background")],
        objects=objects,
        groups=[],
    )


def test_core_inspection_distinguishes_ready_missing_and_modified(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    asset_path = root / "assets" / "scene" / "hero.png"
    _write_image(asset_path, 8, 6, "#32a8ff")
    asset = _record("hero", asset_path)

    ready = inspect_scene_asset(asset, root)
    assert ready.state == "ready"
    asset_path.write_bytes(b"tampered")
    modified = inspect_scene_asset(asset, root)
    assert modified.state == "modified"
    asset_path.unlink()
    missing = inspect_scene_asset(asset, root)
    assert missing.state == "missing"


def test_relink_repairs_missing_asset_with_undo_redo_and_preserves_objects(
    qt_app, tmp_path: Path
) -> None:
    root = tmp_path / "project"
    missing = AssetReferenceRecord(
        id="hero",
        path="assets/scene/missing.png",
        sha256="b" * 64,
    )
    document = _document([missing])
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    panel = SceneAssetLibrary(session, root)
    replacement = tmp_path / "external" / "hero-repaired.png"
    _write_image(replacement, 12, 10, "#32a8ff")
    before_objects = session.document.objects
    try:
        panel._select_id("hero")
        assert panel.inspections["hero"].state == "missing"
        assert panel.relink_button.isEnabled()
        assert panel.relink_asset_from_path(replacement) is True
        updated = session.document.assets[0]
        assert updated.id == "hero"
        assert updated.path.startswith("assets/scene/")
        assert updated.source_path == str(replacement.resolve())
        assert session.document.objects == before_objects
        assert panel.inspections["hero"].state == "ready"
        assert session.undo() is True
        assert session.document.assets[0] == missing
        assert panel.inspections["hero"].state == "missing"
        assert session.redo() is True
        assert panel.inspections["hero"].state == "ready"
    finally:
        panel.close()
        qt_app.processEvents()


def test_replace_preserves_shared_asset_identity_and_viewport_render(
    qt_app, tmp_path: Path
) -> None:
    root = tmp_path / "project"
    hero_path = root / "assets" / "scene" / "hero.png"
    _write_image(hero_path, 8, 6, "#32a8ff")
    hero = _record("hero", hero_path)
    session = SceneAuthoringSession(SceneAuthoringModel(_document([hero])))
    panel = SceneAssetLibrary(session, root)
    viewport = SceneAuthoringViewport(session, project_root=root)
    replacement = tmp_path / "external" / "hero-replacement.png"
    _write_image(replacement, 18, 14, "#ff8c32")
    before_objects = session.document.objects
    try:
        panel._select_id("hero")
        assert panel.replace_button.isEnabled()
        assert panel.replace_asset_from_path(replacement) is True
        assert session.document.assets[0].id == "hero"
        assert session.document.objects == before_objects
        assert viewport._items["object_0"]._pixmap.size().width() == 18
        assert viewport._items["object_0"]._pixmap.size().height() == 14
        assert session.undo() is True
        assert session.document.assets[0].sha256 == hero.sha256
        assert session.redo() is True
        assert session.document.assets[0].id == "hero"
    finally:
        viewport.close()
        panel.close()
        qt_app.processEvents()


def test_invalid_import_is_rejected_without_document_mutation(
    qt_app, tmp_path: Path
) -> None:
    root = tmp_path / "project"
    asset_path = root / "assets" / "scene" / "hero.png"
    _write_image(asset_path, 8, 6, "#32a8ff")
    hero = _record("hero", asset_path)
    session = SceneAuthoringSession(SceneAuthoringModel(_document([hero])))
    panel = SceneAssetLibrary(session, root)
    invalid = tmp_path / "external" / "not-an-image.png"
    invalid.parent.mkdir(parents=True, exist_ok=True)
    invalid.write_bytes(b"not an image")
    messages: list[str] = []
    panel.status_message.connect(messages.append)
    before = session.document
    try:
        assert panel.import_asset_from_path(invalid) is False
        assert session.document == before
        assert any("rejected" in message for message in messages)
    finally:
        panel.close()
        qt_app.processEvents()


def test_professional_window_hosts_asset_library_and_refreshes_missing_state(
    qt_app, tmp_path: Path
) -> None:
    project = tmp_path / "scene.ndtproj"
    project.write_bytes(b"p2d-01b-window-fixture")
    image_path = tmp_path / "scene.png"
    _write_image(image_path, 16, 12, "#32a8ff")
    scene = Scene()
    scene.cmd = CommandManager(max_history=10)
    scene.image_path = str(image_path)
    scene.add_object("scene_object", [(0, 0), (16, 0), (16, 12), (0, 12)])
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project)
    window = ScenarioEditorWindow(authoring, scene)
    try:
        window.show()
        qt_app.processEvents()
        assert window.asset_library is not None
        library = window.asset_library
        assert library.asset_list.count() == 1
        assert next(iter(library.inspections.values())).state == "ready"
        library._select_id("project_image")
        image_path.unlink()
        library.refresh_button.click()
        assert next(iter(library.inspections.values())).state == "missing"
        assert library.relink_button.isEnabled() is True
    finally:
        window.close()
        qt_app.processEvents()


def test_professional_window_opens_missing_sidecar_for_diagnostics(
    qt_app, tmp_path: Path
) -> None:
    project = tmp_path / "scene.ndtproj"
    project.write_bytes(b"p2d-01b-missing-sidecar")
    missing = AssetReferenceRecord(
        id="hero",
        path="assets/scene/missing.png",
        sha256="b" * 64,
    )
    save_scene_authoring(
        upgrade_scene_authoring_document(_document([missing])),
        project.with_suffix(".ndtscene.json"),
    )
    scene = Scene()
    scene.cmd = CommandManager(max_history=10)
    scene.add_object("object_0", [(0, 0), (32, 0), (32, 32), (0, 32)])
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project)
    window = ScenarioEditorWindow(authoring, scene)
    try:
        window.show()
        qt_app.processEvents()
        assert window.professional_session is not None
        assert window.asset_library is not None
        assert window.asset_library.inspections["hero"].state == "missing"
        assert window.asset_library.diagnostics_label.text()
    finally:
        window.close()
        qt_app.processEvents()
