"""PACK pilot: contracts and real Qt import/persistence integration, not binary proof."""

import json
from pathlib import Path
import shutil

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.core.asset_packs import bundled_pack_root, discover_packs, read_pack
from src.core.scene_asset_library import SceneAssetError, sha256_file
from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_io import (
    load_scene_authoring,
    save_scene_authoring,
)
from src.persistence.scene_authoring_schema import (
    SceneAuthoringDocumentV1,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
)
from src.ui.asset_pack_dialog import AssetPackDialog
from src.ui.scene_asset_panel import SceneAssetLibrary
from src.ui.scene_authoring_inspector import SceneAuthoringInspector
from src.ui.scene_authoring_layer_stack import SceneAuthoringLayerStack
from src.ui.scene_authoring_viewport import SceneAuthoringViewport


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def library(app, tmp_path):
    doc = SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="Pack test", generator="NeoEng-D-Trace", app_version="0.2.0"
        ),
        project=ProjectReferenceRecord(sha256="a" * 64),
        assets=[],
        layers=[SceneLayerAuthoringRecord(id="fundo", name="Fundo")],
        objects=[],
        groups=[],
    )
    panel = SceneAssetLibrary(
        SceneAuthoringSession(SceneAuthoringModel(doc)), tmp_path / "project"
    )
    panel.update_language("pt")
    yield panel
    panel.close()
    panel.deleteLater()
    app.processEvents()


def test_bundled_inventory_hashes_dimensions_and_alpha(app):
    packs, errors = discover_packs()
    assert errors == []
    assert len(packs) == 1
    pack = packs[0]
    assert pack.name == "Floresta"
    assert len(pack.assets) == 6
    for asset in pack.assets:
        image = QImage(str(pack.resolve_asset(asset)))
        assert not image.isNull()
        assert (image.width(), image.height()) == (asset.width, asset.height)
        assert image.hasAlphaChannel()
        assert image.pixelColor(0, 0).alpha() < 255


@pytest.mark.parametrize(
    "relative",
    [
        "../outside.png",
        "/outside.png",
        "C:/outside.png",
        "..\\outside.png",
        "missing.png",
    ],
)
def test_manifest_rejects_unsafe_or_missing_paths(tmp_path, relative):
    data = json.loads(
        (bundled_pack_root() / "floresta/manifest.json").read_text(encoding="utf-8")
    )
    data["assets"] = [dict(data["assets"][0], path=relative)]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(SceneAssetError):
        read_pack(manifest)


def test_bad_pack_is_isolated_and_hash_tamper_rejected(tmp_path):
    shutil.copytree(bundled_pack_root() / "floresta", tmp_path / "floresta")
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "manifest.json").write_text("{}", encoding="utf-8")
    packs, errors = discover_packs(tmp_path)
    assert len(packs) == len(errors) == 1
    asset = packs[0].assets[0]
    (packs[0].root / asset.path).write_bytes(b"tampered")
    with pytest.raises(SceneAssetError, match="Integridade"):
        packs[0].resolve_asset(asset)


def test_catalog_search_click_import_repeat_place_undo_and_reopen(
    app, library, tmp_path
):
    dialog = AssetPackDialog(library)
    viewport = SceneAuthoringViewport(
        library.session, project_root=library.project_root
    )
    viewport.update_language("pt")
    viewport.resize(640, 480)
    viewport.show()
    dialog.show()
    try:
        QTest.qWait(250)
        assert all(not dialog.grid.item(i).icon().isNull() for i in range(6))
        QTest.mouseClick(dialog.search, Qt.MouseButton.LeftButton)
        QTest.keyClicks(dialog.search, "arvores")
        visible = [
            dialog.grid.item(i) for i in range(6) if not dialog.grid.item(i).isHidden()
        ]
        assert [i.text() for i in visible] == ["Pinheiro"]
        app.processEvents()
        QTest.mouseClick(
            dialog.grid.viewport(),
            Qt.MouseButton.LeftButton,
            pos=dialog.grid.visualItemRect(visible[0]).center(),
        )
        assert dialog.add_button.isEnabled()
        assert not dialog.preview.pixmap().isNull()
        original_hashes = {
            a.path: sha256_file(dialog.pack.root / a.path) for a in dialog.pack.assets
        }
        QTest.mouseClick(dialog.add_button, Qt.MouseButton.LeftButton)
        assert "adicionado" in dialog.status.text()
        assert len(library.session.document.assets) == 1
        imported = library.session.document.assets[0]
        copied = library.project_root / imported.path
        assert copied.is_file() and sha256_file(copied) == imported.sha256
        requested: list[str] = []
        library.asset_place_requested.connect(requested.append)
        library._select_id(imported.id)
        assert library.place_button.isEnabled()
        QTest.mouseClick(library.place_button, Qt.MouseButton.LeftButton)
        assert requested == [imported.id]
        assert (
            library.asset_list.contextMenuPolicy()
            == Qt.ContextMenuPolicy.CustomContextMenu
        )
        context_menu = library._build_context_menu()
        assert [action.text() for action in context_menu.actions()] == [
            "Inserir na cena",
            "Atualizar",
        ]
        requested.clear()
        context_menu.actions()[0].trigger()
        assert requested == [imported.id]
        context_menu.deleteLater()
        QTest.mouseClick(dialog.add_button, Qt.MouseButton.LeftButton)
        assert "já disponível" in dialog.status.text()
        assert len(library.session.document.assets) == 1
        assert len(list((library.project_root / "assets/scene").glob("*.png"))) == 1
        messages: list[str] = []
        viewport.status_message.connect(messages.append)
        assert viewport.navigation_zoom == pytest.approx(1.0)
        assert viewport.place_asset_from_library(imported.id)
        assert "1 objeto" in library.asset_list.currentItem().text()
        assert viewport.navigation_zoom < 1.0
        assert any("Enquadrar Seleção" in message for message in messages)
        layer_stack = SceneAuthoringLayerStack(library.session)
        layer_stack.update_language("pt")
        assert "Profundidade" in layer_stack.layer_list.currentItem().text()
        assert "1 objeto" in layer_stack.layer_list.currentItem().text()
        layer_stack.close()
        layer_stack.deleteLater()
        app.processEvents()
        obj = library.session.document.objects[0]
        assert obj.transform.scale.x == pytest.approx(1.0)
        assert obj.transform.scale.y == pytest.approx(1.0)
        assert obj.transform.scale.z == pytest.approx(1.0)
        assert not viewport._items[obj.id]._pixmap.isNull()
        assert library.session.undo() and not library.session.document.objects
        assert library.session.redo() and len(library.session.document.objects) == 1
        path = library.project_root / "forest.ndtscene.json"
        save_scene_authoring(library.session.document, path)
        assert load_scene_authoring(path) == library.session.document
        portable = tmp_path / "portable"
        shutil.copytree(library.project_root, portable)
        assert load_scene_authoring(portable / path.name) == library.session.document
        assert original_hashes == {
            a.path: sha256_file(dialog.pack.root / a.path) for a in dialog.pack.assets
        }
    finally:
        dialog.close()
        viewport.close()
        app.processEvents()


def test_professional_inspector_empty_state_stays_localized(app, library):
    inspector = SceneAuthoringInspector(library.session)
    try:
        inspector.update_language("pt")
        assert inspector.selection_label.text() == "Nenhum objeto selecionado"
        assert inspector.spatial_summary.text() == "Camada/profundidade: —"
    finally:
        inspector.close()
        inspector.deleteLater()
        app.processEvents()


def test_corrupted_import_does_not_mutate_project(app, library, tmp_path):
    pack_root = tmp_path / "packs"
    shutil.copytree(bundled_pack_root() / "floresta", pack_root / "floresta")
    dialog = AssetPackDialog(library, pack_root=pack_root)
    try:
        dialog.grid.setCurrentRow(0)
        assert dialog.add_button.isEnabled()
        asset = dialog.pack.assets[0]
        (dialog.pack.root / asset.path).write_bytes(b"tampered")
        QTest.mouseClick(dialog.add_button, Qt.MouseButton.LeftButton)
        assert "Integridade inválida" in dialog.status.text()
        assert not library.session.document.assets
        assert not (library.project_root / "assets/scene").exists()
    finally:
        dialog.close()


def test_no_project_can_browse_but_not_import(app, library):
    library.project_root = None
    dialog = AssetPackDialog(library)
    try:
        dialog.grid.setCurrentRow(0)
        assert not dialog.preview.pixmap().isNull()
        assert not dialog.add_button.isEnabled()
        assert "Salve o projeto" in dialog.status.text()
    finally:
        dialog.close()
