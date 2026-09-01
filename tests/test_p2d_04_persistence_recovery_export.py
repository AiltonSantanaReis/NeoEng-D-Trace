"""P2D-04 persistence, recovery, target export and engine-boundary tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QMessageBox

from src.core.commands import CommandManager
from src.core.scenario_authoring import ScenarioAuthoringState
from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.exporters.scene_authoring_export import (
    SceneAuthoringExportError,
    build_scene_authoring_export,
    save_scene_authoring_export,
)
from src.models.scene import Scene
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_io import (
    load_scene_authoring_recovery,
    load_scene_authoring_v2,
    save_scene_authoring,
    scene_authoring_recovery_path,
)
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
    upgrade_scene_authoring_document,
)
from src.ui import scenario_editor_window as scenario_editor_window_module
from src.ui.scenario_editor_window import ScenarioEditorWindow


def _document(tmp_path: Path) -> tuple[SceneAuthoringDocumentV1, Path]:
    asset = tmp_path / "assets" / "hero.bin"
    asset.parent.mkdir()
    asset.write_bytes(b"p2d-04 real asset")
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    return (
        SceneAuthoringDocumentV1(
            metadata=SceneAuthoringMetadataRecord(
                name="P2D-04 fixture",
                generator="NeoEng-D-Trace",
                app_version="0.2.0",
            ),
            project=ProjectReferenceRecord(sha256="a" * 64),
            assets=[
                AssetReferenceRecord(
                    id="hero_asset", path="assets/hero.bin", sha256=digest
                )
            ],
            layers=[SceneLayerAuthoringRecord(id="foreground", name="Foreground")],
            objects=[
                SceneObjectAuthoringRecord(
                    id="hero",
                    asset_id="hero_asset",
                    layer_id="foreground",
                    transform=SceneTransformRecord(
                        position=Point3Record(x=10.0, y=20.0, z=3.0),
                        rotation=Point3Record(x=0.0, y=0.0, z=15.0),
                        scale=Point3Record(x=1.0, y=1.0, z=1.0),
                        pivot=PointRecord(x=0.5, y=1.0),
                        flip_x=True,
                    ),
                )
            ],
            groups=[],
        ),
        asset,
    )


def _window(tmp_path: Path, qt_app: QApplication) -> ScenarioEditorWindow:
    project = tmp_path / "scene.ndtproj"
    project.write_bytes(b"p2d-04 project")
    image = tmp_path / "scene.png"
    rendered = QImage(40, 24, QImage.Format.Format_RGBA8888)
    rendered.fill(0xFF336699)
    assert rendered.save(str(image))
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image_path = str(image)
    scene.add_object("scene_object", [(0, 0), (40, 0), (40, 24), (0, 24)])
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project)
    window = ScenarioEditorWindow(authoring, scene)
    window.show()
    qt_app.processEvents()
    return window


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_save_creates_last_valid_recovery_without_mutating_current_document(
    tmp_path: Path,
) -> None:
    v1, _asset = _document(tmp_path)
    first = upgrade_scene_authoring_document(v1)
    path = tmp_path / "scene.ndtscene.json"
    save_scene_authoring(first, path)

    second = first.model_copy(
        update={"metadata": first.metadata.model_copy(update={"name": "Second"})}
    )
    save_scene_authoring(second, path)
    recovery = scene_authoring_recovery_path(path)

    assert load_scene_authoring_v2(path) == second
    assert load_scene_authoring_v2(recovery) == first
    assert recovery.is_file()

    third = second.model_copy(
        update={"metadata": second.metadata.model_copy(update={"name": "Third"})}
    )
    save_scene_authoring(third, path)
    assert load_scene_authoring_v2(recovery) == second


def test_corrupt_current_file_does_not_replace_recovery_and_recovery_is_explicit(
    tmp_path: Path,
) -> None:
    v1, _asset = _document(tmp_path)
    document = upgrade_scene_authoring_document(v1)
    path = tmp_path / "scene.ndtscene.json"
    save_scene_authoring(document, path)
    changed = document.model_copy(
        update={"metadata": document.metadata.model_copy(update={"name": "Changed"})}
    )
    save_scene_authoring(changed, path)
    recovery = scene_authoring_recovery_path(path)
    recovery_before = recovery.read_bytes()

    path.write_bytes(b"not a scene")
    replacement = changed.model_copy(
        update={"metadata": changed.metadata.model_copy(update={"name": "Replacement"})}
    )
    save_scene_authoring(replacement, path)

    assert recovery.read_bytes() == recovery_before
    assert load_scene_authoring_recovery(path) == document


def test_export_with_source_path_blocks_missing_or_tampered_asset(
    tmp_path: Path,
) -> None:
    v1, asset = _document(tmp_path)
    document = upgrade_scene_authoring_document(v1)
    source = tmp_path / "scene.ndtscene.json"
    destination = tmp_path / "scene.godot.runtime.json"
    save_scene_authoring(document, source)

    asset.write_bytes(b"tampered")
    with pytest.raises(
        SceneAuthoringExportError, match="asset is unavailable or changed"
    ):
        save_scene_authoring_export(
            document,
            destination,
            target="godot",
            source_document_path=source,
        )
    assert not destination.exists()


def test_mark_unsaved_requires_explicit_save_boundary(tmp_path: Path) -> None:
    v1, _asset = _document(tmp_path)
    document = upgrade_scene_authoring_document(v1)
    session = SceneAuthoringSession(SceneAuthoringModel(document))

    assert session.is_dirty is False
    session.mark_unsaved()
    assert session.is_dirty is True
    session.mark_saved()
    assert session.is_dirty is False


def test_real_ui_export_selects_target_and_uses_active_document(
    tmp_path: Path,
    qt_app: QApplication,
) -> None:
    window = _window(tmp_path, qt_app)
    try:
        assert window.professional_session is not None
        assert window.export_target_combo.findData("godot") >= 0
        window.export_target_combo.setCurrentIndex(
            window.export_target_combo.findData("godot")
        )
        assert window._export_professional() is True
        destination = tmp_path / "scene.ndtscene.godot.runtime.json"
        payload = json.loads(destination.read_text(encoding="utf-8"))
        assert payload["target"] == "godot"
        assert payload["scene"]["objects"]
        assert all("source_path" not in asset for asset in payload["scene"]["assets"])

        image = tmp_path / "scene.png"
        image.write_bytes(b"tampered image")
        before = destination.read_bytes()
        assert window._export_professional() is False
        assert destination.read_bytes() == before
    finally:
        window.close()
        qt_app.processEvents()


def test_v1_upgrade_is_explicit_and_does_not_rewrite_file_until_save(
    tmp_path: Path,
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "scene.ndtproj"
    project.write_bytes(b"p2d-04 project")
    image = tmp_path / "scene.png"
    rendered = QImage(40, 24, QImage.Format.Format_RGBA8888)
    rendered.fill(0xFF336699)
    assert rendered.save(str(image))
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image_path = str(image)
    scene.add_object("scene_object", [(0, 0), (40, 0), (40, 24), (0, 24)])
    authoring = ScenarioAuthoringState(scene)
    authoring.bind_project(project)

    v1, _asset = _document(tmp_path)
    source = project.with_suffix(".ndtscene.json")
    save_scene_authoring(v1, source)
    original = source.read_bytes()

    window = ScenarioEditorWindow(authoring, scene)
    window.show()
    qt_app.processEvents()
    try:
        assert window.professional_session is None
        assert window.upgrade_action.isEnabled()
        monkeypatch.setattr(
            scenario_editor_window_module.QMessageBox,
            "question",
            lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
        )
        assert window._upgrade_professional() is True
        assert window.professional_session is not None
        assert window.professional_session.is_dirty is True
        assert source.read_bytes() == original
        assert window._save_professional() is True
        assert load_scene_authoring_v2(source).schema_version == 2
    finally:
        window.close()
        qt_app.processEvents()


def test_ui_recovery_and_target_fallback_paths_are_explicit(
    tmp_path: Path,
    qt_app: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = _window(tmp_path, qt_app)
    try:
        assert window._recover_professional() is False

        v1, _asset = _document(tmp_path)
        source = window.professional_scene_path
        assert source is not None
        save_scene_authoring(v1, source)
        window._pending_v1_document = v1
        monkeypatch.setattr(
            scenario_editor_window_module.QMessageBox,
            "question",
            lambda *_args, **_kwargs: QMessageBox.StandardButton.No,
        )
        assert window._upgrade_professional() is False

        first_v2 = upgrade_scene_authoring_document(v1)
        second_v2 = first_v2.model_copy(
            update={"metadata": first_v2.metadata.model_copy(update={"name": "Second"})}
        )
        save_scene_authoring(first_v2, source)
        save_scene_authoring(second_v2, source)
        recovery = scene_authoring_recovery_path(source)
        source.write_bytes(b"broken")
        window._pending_recovery_path = recovery

        assert window._recover_professional() is True
        assert window.professional_session is not None
        assert window.professional_session.is_dirty is True

        window.export_target_combo.setItemData(0, "unsupported")
        window.export_target_combo.setCurrentIndex(0)
        assert window._export_professional() is True
        assert tmp_path.joinpath("scene.ndtscene.runtime.json").is_file()
    finally:
        window.close()
        qt_app.processEvents()


def test_export_rejects_unsupported_target_before_serialization(tmp_path: Path) -> None:
    document, _asset = _document(tmp_path)
    document_v2 = upgrade_scene_authoring_document(document)

    with pytest.raises(
        SceneAuthoringExportError, match="unsupported scene export target"
    ):
        build_scene_authoring_export(
            document_v2, target="unsupported"  # type: ignore[arg-type]
        )


def test_native_importers_expose_p2d04_transform_camera_and_parallax_contract() -> None:
    godot = Path(
        "integrations/godot/addons/neoeng_d_trace/professional_scene_importer.gd"
    ).read_text(encoding="utf-8")
    godot_validator = Path(
        "tools/godot_professional_scene_stage5_validator.gd"
    ).read_text(encoding="utf-8")
    unity_editor = Path(
        "integrations/unity/package/com.neoeng.dtrace/Editor/"
        "ProfessionalSceneImportGenerator.cs"
    ).read_text(encoding="utf-8")
    unity_runtime = Path(
        "integrations/unity/package/com.neoeng.dtrace/Runtime/"
        "NeoEngProfessionalParallax.cs"
    ).read_text(encoding="utf-8")

    assert "Camera2D.new()" in godot
    assert "Parallax2D.new()" in godot
    assert "sprite.offset" in godot
    assert 'has_meta("neoeng_layer_id")' in godot_validator
    assert "GODOT_PROFESSIONAL_SCENE_LAYERS=" in godot_validator
    assert "AddComponent<Camera>()" in unity_editor
    assert "AddComponent<NeoEngProfessionalParallax>()" in unity_editor
    assert (
        "GetComponentsInChildren<NeoEngProfessionalLayerMetadata>(true).Length"
        in unity_editor
    )
    assert "GameObject visual" in unity_editor
    assert "LateUpdate" in unity_runtime
