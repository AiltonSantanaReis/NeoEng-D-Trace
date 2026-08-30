"""Focused merge-gate coverage for the professional authoring contracts.

These tests exercise the fail-closed and boundary paths introduced by the
scene-authoring integration.  They intentionally use the public model,
session, persistence, and pure helper contracts rather than changing the
coverage policy or excluding real branches from measurement.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QMimeData, QPointF, Qt, QUrl
from PySide6.QtGui import (
    QColor,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPixmap,
    QPolygonF,
)
from PySide6.QtWidgets import QApplication, QTreeWidgetItemIterator

from src.core.scene_asset_library import (
    SceneAssetError,
    _relative_to_project,
    _safe_stem,
    inspect_scene_asset,
    prepare_scene_asset,
    resolve_scene_asset,
    sha256_file,
    validate_scene_asset_source,
)
from src.core.scene_authoring_clipboard import (
    SCENE_CLIPBOARD_MIME,
    SceneClipboardGroupRecord,
    SceneClipboardPayload,
    decode_scene_clipboard,
    encode_scene_clipboard,
)
from src.core.scene_authoring_groups import (
    child_group_ids,
    group_ancestry,
    group_is_effectively_locked,
    group_is_effectively_visible,
    group_parent_id,
    locked_group_for_object,
    object_group_ids,
    object_ids_for_group,
    object_is_effectively_locked,
    object_is_effectively_visible,
    root_group_ids,
)
from src.core.scene_authoring_model import (
    SceneAuthoringModel,
    SceneSelection,
    snap_transform,
    snap_value,
)
from src.core.scene_authoring_order import (
    layer_index_by_id,
    layer_visual_priority,
    ordered_scene_objects,
)
from src.core.scene_authoring_session import SceneAuthoringSession
from src.core.scene_view_navigation import (
    anchored_navigation_center,
    clamp_navigation_zoom,
    fit_navigation_zoom,
    panned_navigation_center,
    wheel_navigation_zoom,
)
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringDocumentV2,
    SceneCameraAuthoringRecord,
    SceneGroupAuthoringRecord,
    SceneGroupAuthoringRecordV2,
    SceneLayerAuthoringRecord,
    SceneLightSocketRecord,
    SceneObjectAuthoringRecord,
    SceneParallaxLayerRecord,
    SceneSnapRecord,
    SceneTransformRecord,
    SceneTriggerSocketRecord,
    SceneVfxSocketRecord,
)
from src.ui import scene_asset_panel as scene_asset_panel_module
from src.ui import scene_authoring_viewport as scene_authoring_viewport_module
from src.ui.scene_asset_panel import SceneAssetLibrary
from src.ui.scene_authoring_group_stack import SceneAuthoringGroupStack
from src.ui.scene_authoring_layer_stack import SceneAuthoringLayerStack
from src.ui.scene_authoring_viewport import (
    SceneAuthoringViewport,
    SceneObjectGraphicsItem,
    SceneSocketGraphicsItem,
    SceneTransformGizmo,
)

SHA = "a" * 64


def _transform(x: float = 0.0, y: float = 0.0) -> SceneTransformRecord:
    return SceneTransformRecord(
        position=Point3Record(x=x, y=y, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )


def _object(object_id: str, layer_id: str = "back") -> SceneObjectAuthoringRecord:
    return SceneObjectAuthoringRecord(
        id=object_id,
        asset_id="asset",
        layer_id=layer_id,
        transform=_transform(),
    )


def _v1_document(*, groups=None) -> SceneAuthoringDocumentV1:
    return SceneAuthoringDocumentV1(
        metadata={"name": "merge coverage", "generator": "tests", "app_version": "0"},
        project=ProjectReferenceRecord(sha256=SHA),
        assets=[AssetReferenceRecord(id="asset", path="assets/a.png", sha256=SHA)],
        layers=[
            SceneLayerAuthoringRecord(id="back", name="Back"),
            SceneLayerAuthoringRecord(id="front", name="Front"),
        ],
        objects=[_object("a"), _object("b", "front")],
        groups=list(groups or []),
    )


def _v2_document(*, groups=None):
    base = _v1_document()
    data = base.model_dump()
    data["schema_version"] = 2
    data["groups"] = list(groups or [])
    return SceneAuthoringDocumentV2(**data)


def _write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def test_asset_lifecycle_is_fail_closed_and_content_addressed(tmp_path: Path) -> None:
    root = tmp_path / "project"
    external = tmp_path / "external" / "odd name.png"
    _write_bytes(external, b"valid-image-payload")

    with pytest.raises(SceneAssetError, match="does not exist"):
        sha256_file(tmp_path / "missing.png")
    with pytest.raises(SceneAssetError, match="unsupported"):
        validate_scene_asset_source(tmp_path / "source.txt")
    with pytest.raises(SceneAssetError, match="does not exist"):
        validate_scene_asset_source(tmp_path / "source.png")

    assert _safe_stem("...") == "asset"
    assert _relative_to_project(root, external) is None
    assert _relative_to_project(root, root / "assets" / "a.png") == "assets/a.png"

    prepared = prepare_scene_asset(external, root)
    assert prepared.source_path == str(external.resolve())
    assert prepared.path.startswith("assets/scene/")
    assert prepare_scene_asset(external, root).resolved_path == prepared.resolved_path

    digest = prepared.sha256
    short_destination = root / "assets" / "scene" / f"odd_name-{digest[:16]}.png"
    short_destination.write_bytes(b"different-content")
    second = tmp_path / "external" / "other name.png"
    _write_bytes(second, b"second-payload")
    second_digest = sha256_file(second)
    second_short_destination = (
        root / "assets" / "scene" / f"other_name-{second_digest[:16]}.png"
    )
    second_short_destination.write_bytes(b"short-hash-collision")
    second_prepared = prepare_scene_asset(second, root)
    assert second_prepared.resolved_path.name.endswith(f"-{second_prepared.sha256}.png")

    full_destination = (
        root / "assets" / "scene" / f"other_name-{second_prepared.sha256}.png"
    )
    full_destination.write_bytes(b"another-different-content")
    with pytest.raises(SceneAssetError, match="destination collision"):
        prepare_scene_asset(second, root)

    repaired = prepare_scene_asset(external, root)
    ready_asset = AssetReferenceRecord(
        id="asset", path=repaired.path, sha256=repaired.sha256
    )
    resolved, issue = resolve_scene_asset(ready_asset, root)
    assert resolved == repaired.resolved_path and issue is None
    assert inspect_scene_asset(ready_asset, None).state == "unavailable"

    escaping = AssetReferenceRecord.model_construct(
        id="escape", path="../outside.png", sha256=SHA
    )
    resolved, issue = resolve_scene_asset(escaping, root)
    assert resolved is None and issue is not None and "escapes" in issue
    assert inspect_scene_asset(escaping, root).state == "invalid"

    mismatched = ready_asset.model_copy(update={"sha256": "b" * 64})
    assert inspect_scene_asset(mismatched, root).state == "modified"


def test_order_and_hierarchy_helpers_cover_boundaries() -> None:
    root = SceneGroupAuthoringRecordV2(id="root", name="Root", members=["a"])
    child = SceneGroupAuthoringRecordV2(
        id="child", name="Child", members=["b"], parent_group_id="root"
    )
    document = _v2_document(groups=[root, child])

    assert [item.id for item in ordered_scene_objects(document)] == ["a", "b"]
    assert layer_index_by_id(document) == {"back": 0, "front": 1}
    assert layer_visual_priority(1, 0, 2) > layer_visual_priority(0, 1, 2)
    invalid_indexes = [
        (True, 0, 1),
        (0, True, 1),
        (0, 0, True),
        (-1, 0, 1),
        (0, -1, 1),
        (0, 0, 0),
        (0, 2, 2),
    ]
    for values in invalid_indexes:
        with pytest.raises(ValueError):
            layer_visual_priority(*values)

    assert group_parent_id(document.groups[0]) is None
    assert group_parent_id(document.groups[1]) == "root"
    assert root_group_ids(document) == ("root",)
    assert child_group_ids(document, None) == ("root",)
    assert child_group_ids(document, "root") == ("child",)
    with pytest.raises(KeyError):
        child_group_ids(document, "missing")
    assert group_ancestry(document, "child") == ("child", "root")
    with pytest.raises(KeyError):
        group_ancestry(document, "missing")
    assert object_group_ids(document, "a") == ("root",)
    assert object_group_ids(document, "b") == ("child", "root")
    assert object_group_ids(document, "free") == ()
    assert object_ids_for_group(document, "root") == ("a", "b")
    assert object_ids_for_group(document, "child") == ("b",)
    with pytest.raises(KeyError):
        object_ids_for_group(document, "missing")

    assert group_is_effectively_visible(document, "child")
    assert not group_is_effectively_locked(document, "child")
    hidden = document.groups[0].model_copy(update={"visible": False})
    locked = document.groups[0].model_copy(update={"locked": True})
    hidden_document = document.model_copy(
        update={"groups": [hidden, document.groups[1]]}
    )
    locked_document = document.model_copy(
        update={"groups": [locked, document.groups[1]]}
    )
    assert not object_is_effectively_visible(hidden_document, "b")
    assert object_is_effectively_locked(locked_document, "b")
    assert locked_group_for_object(locked_document, "b").id == "root"
    assert object_is_effectively_visible(document, "a", isolated_group_id="root")
    assert not object_is_effectively_visible(document, "a", isolated_group_id="child")
    with pytest.raises(KeyError):
        object_is_effectively_visible(document, "a", isolated_group_id="missing")
    assert not object_is_effectively_visible(document, "missing")
    assert not object_is_effectively_locked(document, "a")
    with pytest.raises(KeyError):
        object_is_effectively_locked(document, "missing")


def test_clipboard_contract_rejects_every_reference_boundary() -> None:
    obj = _object("a")
    group = SceneClipboardGroupRecord(id="group", name="Group", members=["a"])
    encoded = encode_scene_clipboard([obj], [group])
    assert decode_scene_clipboard(encoded).groups[0].members == ["a"]
    assert decode_scene_clipboard(bytearray(encoded)).objects[0].id == "a"

    with pytest.raises(ValueError, match="non-empty"):
        SceneClipboardGroupRecord(id="g", name="G", members=[""])
    with pytest.raises(ValueError, match="unique"):
        SceneClipboardGroupRecord(id="g", name="G", members=["a", "a"])
    with pytest.raises(ValueError):
        SceneClipboardPayload(objects=[], groups=[])
    with pytest.raises(ValueError, match="object IDs"):
        SceneClipboardPayload(objects=[obj, obj], groups=[])
    with pytest.raises(ValueError, match="uncopied object"):
        SceneClipboardPayload(
            objects=[obj],
            groups=[SceneClipboardGroupRecord(id="g", name="G", members=["missing"])],
        )
    with pytest.raises(ValueError, match="uncopied parent"):
        SceneClipboardPayload(
            objects=[obj],
            groups=[
                SceneClipboardGroupRecord(
                    id="g", name="G", members=["a"], parent_group_id="missing"
                )
            ],
        )
    duplicate_group = SceneClipboardGroupRecord(id="g", name="G", members=["a"])
    with pytest.raises(ValueError, match="group IDs"):
        SceneClipboardPayload(objects=[obj], groups=[duplicate_group, duplicate_group])
    cycle_a = SceneClipboardGroupRecord(
        id="a", name="A", members=["a"], parent_group_id="b"
    )
    cycle_b = SceneClipboardGroupRecord(
        id="b", name="B", members=["a"], parent_group_id="a"
    )
    with pytest.raises(ValueError, match="cycle"):
        SceneClipboardPayload(objects=[obj], groups=[cycle_a, cycle_b])
    with pytest.raises(ValueError, match="bytes"):
        decode_scene_clipboard("not-bytes")
    with pytest.raises(ValueError, match="invalid"):
        decode_scene_clipboard(b"not-json")


def test_navigation_math_rejects_invalid_inputs_and_handles_empty_content() -> None:
    for value in (True, "1", math.inf, float("nan")):
        with pytest.raises(ValueError):
            clamp_navigation_zoom(value)
    with pytest.raises(ValueError):
        wheel_navigation_zoom(1.0, True)
    with pytest.raises(ValueError):
        wheel_navigation_zoom("bad", 120.0)

    with pytest.raises(ValueError):
        anchored_navigation_center((1.0,), (1.0, 2.0), (1.0, 2.0), 1.0)
    with pytest.raises(ValueError):
        anchored_navigation_center((True, 1.0), (1.0, 2.0), (1.0, 2.0), 1.0)
    with pytest.raises(ValueError):
        panned_navigation_center((1.0, 2.0), (1.0,), (1.0, 2.0), 1.0)
    with pytest.raises(ValueError):
        panned_navigation_center((1.0, 2.0), (1.0, 2.0), (True, 2.0), 1.0)

    with pytest.raises(ValueError):
        fit_navigation_zoom((800.0,), (10.0, 10.0))
    with pytest.raises(ValueError):
        fit_navigation_zoom((0.0, 600.0), (10.0, 10.0))
    with pytest.raises(ValueError):
        fit_navigation_zoom((800.0, 600.0), (-1.0, 10.0))
    with pytest.raises(ValueError):
        fit_navigation_zoom((800.0, 600.0), (0.0, 0.0), margin=True)
    assert fit_navigation_zoom((800.0, 600.0), (0.0, 0.0), margin=0.0) == 8.0


def test_model_asset_object_layer_and_transform_boundaries() -> None:
    model = SceneAuthoringModel(_v1_document())
    assert SceneSelection.from_ids(["a", "a"]).ids == ("a",)
    assert SceneSelection.from_ids([]).primary is None
    with pytest.raises(ValueError):
        SceneSelection(ids=("a", "a"))
    with pytest.raises(ValueError):
        SceneSelection(ids=("a",), primary="missing")
    with pytest.raises(ValueError):
        snap_value(True, 1.0)
    with pytest.raises(ValueError):
        snap_value(1.0, 0.0)
    assert snap_value(7.0, 4.0) == 8.0
    transform = _transform(7.0, 9.0)
    assert snap_transform(transform, SceneSnapRecord(enabled=False)) == transform
    snapped = snap_transform(
        transform,
        SceneSnapRecord(enabled=True, spacing=PointRecord(x=4.0, y=4.0)),
    )
    assert snapped.position == Point3Record(x=8.0, y=8.0, z=0.0)

    with pytest.raises(KeyError):
        model.set_selection(["missing"])
    model.add_asset(AssetReferenceRecord(id="second", path="assets/b.png", sha256=SHA))
    with pytest.raises(ValueError, match="asset ID"):
        model.add_asset(
            AssetReferenceRecord(id="second", path="assets/c.png", sha256=SHA)
        )
    model.update_asset(
        AssetReferenceRecord(id="second", path="assets/c.png", sha256="b" * 64)
    )
    with pytest.raises(KeyError):
        model.update_asset(
            AssetReferenceRecord(id="missing", path="assets/x.png", sha256=SHA)
        )

    model.add_object(_object("new"), select=True)
    assert model.selection.primary == "new"
    with pytest.raises(ValueError, match="object ID"):
        model.add_object(_object("new"))
    model.update_transform("new", _transform(3.0, 4.0))
    model.remove_object("new")
    with pytest.raises(KeyError):
        model.remove_object("missing")
    with pytest.raises(ValueError, match="unique"):
        model.remove_objects(["a", "a"])
    model.remove_objects([])
    model.clear_selection()
    model.translate_selected(Point3Record(x=1.0, y=1.0, z=0.0))
    with pytest.raises(ValueError, match="rotation"):
        model.transform_selected(rotation_z=math.inf)
    with pytest.raises(ValueError, match="scale"):
        model.transform_selected(scale_factor=0.0)
    model.transform_selected()

    model.add_layer(SceneLayerAuthoringRecord(id="unused", name="Unused"))
    with pytest.raises(ValueError, match="layer ID"):
        model.add_layer(SceneLayerAuthoringRecord(id="unused", name="Again"))
    model.rename_layer("unused", "Renamed")
    model.set_layer_visibility("unused", False)
    model.set_layer_locked("unused", True)
    model.reorder_layer("unused", -10)
    model.remove_layer("unused")
    with pytest.raises(ValueError, match="assigned objects"):
        model.remove_layer("back")
    model.remove_objects(["a", "b"])
    model.remove_layer("front")
    with pytest.raises(ValueError, match="at least one"):
        model.remove_layer("back")
    with pytest.raises(KeyError):
        model.rename_layer("missing", "Missing")


def test_model_v2_sockets_camera_parallax_and_group_boundaries() -> None:
    model = SceneAuthoringModel(_v2_document())
    with pytest.raises(ValueError, match="schema v2"):
        SceneAuthoringModel(_v1_document()).set_camera(SceneCameraAuthoringRecord())
    with pytest.raises(KeyError):
        model.set_parallax_layer(SceneParallaxLayerRecord(layer_id="missing"))
    model.set_camera(SceneCameraAuthoringRecord(position=PointRecord(x=3.0, y=4.0)))
    model.set_parallax_layer(SceneParallaxLayerRecord(layer_id="back", depth=0.5))
    model.set_parallax_layer(SceneParallaxLayerRecord(layer_id="back", depth=0.75))
    socket = SceneLightSocketRecord(
        id="light",
        layer_id="front",
        position=Point3Record(x=1.0, y=2.0, z=0.0),
        color="#ffffff",
    )
    model.add_socket(socket)
    with pytest.raises(KeyError):
        model.add_socket(socket.model_copy(update={"id": "bad", "layer_id": "missing"}))
    model.update_socket_position("light", Point3Record(x=5.0, y=6.0, z=0.0))
    model.remove_socket("light")
    with pytest.raises(KeyError):
        model.remove_socket("light")
    model.add_socket(socket)
    model.remove_object("b")
    with pytest.raises(ValueError, match="sockets"):
        model.remove_layer("front")
    model.remove_socket("light")

    parent = SceneGroupAuthoringRecordV2(id="parent", name="Parent", members=["a"])
    child = SceneGroupAuthoringRecordV2(
        id="child", name="Child", members=["b"], parent_group_id="parent"
    )
    grouped = SceneAuthoringModel(_v2_document(groups=[parent, child]))
    with pytest.raises(KeyError):
        grouped.add_group(
            SceneGroupAuthoringRecordV2(id="bad", name="Bad", members=["missing"])
        )
    grouped.set_selection(["a"])
    with pytest.raises(ValueError, match="group ID"):
        grouped.add_group(
            SceneGroupAuthoringRecordV2(id="parent", name="Duplicate", members=["a"])
        )
    with pytest.raises(ValueError, match="blank"):
        grouped.rename_group("parent", "   ")
    grouped.rename_group("parent", "Renamed")
    with pytest.raises(ValueError, match="own parent"):
        grouped.set_group_parent("parent", "parent")
    with pytest.raises(KeyError):
        grouped.set_group_parent("parent", "missing")
    with pytest.raises(ValueError, match="cycle"):
        grouped.set_group_parent("parent", "child")
    grouped.set_group_parent("child", None)
    grouped.set_group_visibility("parent", False)
    grouped.set_group_locked("parent", True)
    with pytest.raises(KeyError):
        grouped.add_objects_to_group("parent", ["missing"])
    grouped.add_objects_to_group("parent", ["a", "a"])
    grouped.remove_objects_from_group("parent", ["a"])
    grouped.reorder_group("parent", 99)
    grouped.remove_group("parent")

    v1 = SceneAuthoringModel(
        _v1_document(
            groups=[SceneGroupAuthoringRecord(id="g", name="G", members=["a"])]
        )
    )
    with pytest.raises(ValueError, match="nested"):
        v1.set_group_parent("g", "g")
    assert v1.set_group_parent("g", None) is None


def _write_png(path: Path, color: str = "#2aa7ff") -> None:
    image = QImage(8, 8, QImage.Format.Format_RGBA8888)
    image.fill(QColor(color))
    path.parent.mkdir(parents=True, exist_ok=True)
    assert image.save(str(path))


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_asset_library_exercises_fail_closed_selection_and_lifecycle_edges(
    qt_app: QApplication, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "project"
    source = tmp_path / "external" / "source.png"
    _write_png(source)
    prepared = prepare_scene_asset(source, root)
    asset = AssetReferenceRecord(
        id="asset",
        path=prepared.path,
        sha256=prepared.sha256,
        source_path=prepared.source_path,
    )
    document = _v2_document().model_copy(update={"assets": [asset]})
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    panel = SceneAssetLibrary(session, root)
    messages: list[str] = []
    panel.status_message.connect(messages.append)
    try:
        panel.asset_list.clearSelection()
        panel.asset_list.setCurrentItem(None)
        panel.asset_list.setCurrentRow(-1)
        qt_app.processEvents()
        assert panel.selected_asset_id is None
        assert panel.selected_asset is None
        assert panel.replace_asset_from_path(source) is False
        assert any("Select an asset before replace" in message for message in messages)

        messages.clear()
        assert panel.import_asset_from_path(source) is False
        assert any("already in library" in message for message in messages)

        panel._select_id("asset")
        assert panel.relink_asset_from_path(source) is False
        assert any("only for missing" in message for message in messages)

        messages.clear()
        assert panel.replace_asset_from_path(source) is False
        assert any("made no changes" in message for message in messages)

        second = tmp_path / "external" / "second.png"
        _write_png(second, "#ff8c32")
        assert panel.import_asset_from_path(second) is True
        assert len(session.document.assets) == 2
        imported_id = next(
            asset_record.id
            for asset_record in session.document.assets
            if asset_record.sha256 == sha256_file(second)
        )
        panel._select_id(imported_id)
        assert panel.selected_asset_id == imported_id

        invalid = tmp_path / "external" / "invalid.png"
        invalid.write_bytes(b"not an image")
        messages.clear()
        assert panel.replace_asset_from_path(invalid) is False
        assert any("Replace rejected" in message for message in messages)

        digest = sha256_file(second)
        assert panel._new_asset_id(digest).endswith("_1")

        monkeypatch.setattr(
            scene_asset_panel_module.QFileDialog,
            "getOpenFileName",
            staticmethod(lambda *_args, **_kwargs: ("", "")),
        )
        panel._choose_import()
        monkeypatch.setattr(
            scene_asset_panel_module.QFileDialog,
            "getOpenFileName",
            staticmethod(lambda *_args, **_kwargs: (str(second), "")),
        )
        panel._choose_import()
        panel._choose_relink()
        panel._choose_replace()

        panel.update_language("pt")
        assert panel.current_lang == "pt"
        panel.update_language("unsupported")
        assert panel.current_lang == "en"
    finally:
        panel.close()
        qt_app.processEvents()

    no_project = SceneAssetLibrary(session, None)
    try:
        assert no_project.import_button.isEnabled() is False
        assert no_project.import_asset_from_path(source) is False
    finally:
        no_project.close()
        qt_app.processEvents()


def _find_tree_ref(panel: SceneAuthoringGroupStack, kind: str, item_id: str):
    iterator = QTreeWidgetItemIterator(panel.tree)
    while iterator.value() is not None:
        item = iterator.value()
        if (
            item.data(0, panel._KIND_ROLE) == kind
            and item.data(0, panel._ID_ROLE) == item_id
        ):
            return item
        iterator += 1
    raise AssertionError(f"missing group tree item {kind}:{item_id}")


def test_group_stack_exercises_user_operations_and_safe_no_selection_paths(
    qt_app: QApplication,
) -> None:
    groups = [
        SceneGroupAuthoringRecordV2(id="scenario_group", name="Root", members=["a"]),
        SceneGroupAuthoringRecordV2(
            id="scenario_group_2",
            name="Nested",
            members=[],
            parent_group_id="scenario_group",
        ),
    ]
    session = SceneAuthoringSession(SceneAuthoringModel(_v2_document(groups=groups)))
    panel = SceneAuthoringGroupStack(session)
    messages: list[str] = []
    panel.status_message.connect(messages.append)
    try:
        panel.tree.setCurrentItem(None)
        panel._new_group()
        assert any(group.id == "scenario_group_3" for group in session.document.groups)

        root_item = _find_tree_ref(panel, "group", "scenario_group")
        panel.tree.setCurrentItem(root_item)
        qt_app.processEvents()
        panel.name_edit.setText("   ")
        panel._rename_current()
        panel.name_edit.setText("Root Renamed")
        panel._rename_current()
        assert session.document.groups[0].name == "Root Renamed"

        panel._set_visible(False)
        panel._set_visible(True)
        panel._set_locked(True)
        panel._set_locked(False)

        session.set_selection(["b"], "b")
        panel._add_selected()
        assert (
            "b"
            in next(
                group
                for group in session.document.groups
                if group.id == "scenario_group"
            ).members
        )
        panel._remove_selected()
        assert (
            "b"
            not in next(
                group
                for group in session.document.groups
                if group.id == "scenario_group"
            ).members
        )

        panel._refresh_parent_combo("scenario_group")
        panel.parent_combo.setCurrentIndex(0)
        panel._set_parent(0)
        panel._toggle_isolation()
        assert session.isolated_group_id == "scenario_group"
        panel._toggle_isolation()
        assert session.isolated_group_id is None
        panel._move(-1)
        panel._move(1)

        object_item = _find_tree_ref(panel, "object", "b")
        panel.tree.setCurrentItem(object_item)
        qt_app.processEvents()
        panel._set_parent(0)
        panel._set_visible(False)
        panel._set_locked(True)
        panel._delete_group()
        panel._add_selected()
        panel._remove_selected()
        panel._move(1)
        panel._toggle_isolation()

        ungrouped = next(
            panel.tree.topLevelItem(index)
            for index in range(panel.tree.topLevelItemCount())
            if panel.tree.topLevelItem(index).text(0) == "Ungrouped Objects"
        )
        panel.tree.setCurrentItem(ungrouped)
        qt_app.processEvents()
        assert panel._current_ref() is None
        panel.refresh()

        for error in (
            KeyError("key"),
            ValueError("value"),
            PermissionError("permission"),
        ):
            panel._run(lambda error=error: (_ for _ in ()).throw(error))
        assert any(message == "'key'" for message in messages)
        assert any(message == "value" for message in messages)
        assert any(message == "permission" for message in messages)
    finally:
        panel.close()
        qt_app.processEvents()

    legacy_document = _v1_document(
        groups=[
            SceneGroupAuthoringRecord(id="legacy_group", name="Legacy", members=["a"])
        ]
    )
    legacy = SceneAuthoringSession(SceneAuthoringModel(legacy_document))
    legacy_panel = SceneAuthoringGroupStack(legacy)
    legacy_messages: list[str] = []
    legacy_panel.status_message.connect(legacy_messages.append)
    try:
        legacy_panel.tree.setCurrentItem(
            _find_tree_ref(legacy_panel, "group", "legacy_group")
        )
        legacy_panel._new_group()
        assert any("schema V2" in message for message in legacy_messages)
    finally:
        legacy_panel.close()
        qt_app.processEvents()


def test_layer_stack_exercises_editing_and_no_selection_paths(
    qt_app: QApplication,
) -> None:
    document = _v2_document().model_copy(
        update={
            "layers": [
                SceneLayerAuthoringRecord(id="back", name="Back"),
                SceneLayerAuthoringRecord(id="front", name="Front"),
                SceneLayerAuthoringRecord(id="scenario_layer", name="Existing"),
            ]
        }
    )
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    panel = SceneAuthoringLayerStack(session)
    messages: list[str] = []
    panel.status_message.connect(messages.append)
    try:
        panel.layer_list.setCurrentRow(-1)
        panel._rename_current()
        panel._set_visible(False)
        panel._set_locked(True)
        panel._remove()
        panel._move(-1)
        assert panel._current_id() is None

        panel.layer_list.setCurrentRow(0)
        panel.name_edit.setText("   ")
        panel._rename_current()
        panel.name_edit.setText("Back Renamed")
        panel._rename_current()
        panel._set_visible(False)
        panel._set_visible(True)
        panel._set_locked(True)
        panel._set_locked(False)
        assert session.document.layers[0].name == "Back Renamed"

        panel._add()
        assert any(layer.id == "scenario_layer_2" for layer in session.document.layers)
        new_row = next(
            index
            for index, layer in enumerate(session.document.layers)
            if layer.id == "scenario_layer_2"
        )
        panel.layer_list.setCurrentRow(new_row)
        panel._remove()
        assert all(layer.id != "scenario_layer_2" for layer in session.document.layers)

        panel.layer_list.setCurrentRow(0)
        panel._remove()
        assert any("assigned objects" in message for message in messages)
        for error in (
            KeyError("key"),
            ValueError("value"),
            PermissionError("permission"),
        ):
            panel._run(lambda error=error: (_ for _ in ()).throw(error))
        assert any(message == "'key'" for message in messages)
        assert any(message == "value" for message in messages)
        assert any(message == "permission" for message in messages)
    finally:
        panel.close()
        qt_app.processEvents()


class _FakeMouseEvent:
    def __init__(
        self,
        point: QPointF,
        *,
        button: Qt.MouseButton = Qt.MouseButton.LeftButton,
        buttons: Qt.MouseButton = Qt.MouseButton.LeftButton,
    ) -> None:
        self._point = QPointF(point)
        self._button = button
        self._buttons = buttons
        self.accepted = False
        self.ignored = False

    def pos(self) -> QPointF:
        return QPointF(self._point)

    def position(self) -> QPointF:
        return QPointF(self._point)

    def scenePos(self) -> QPointF:
        return QPointF(self._point)

    def button(self) -> Qt.MouseButton:
        return self._button

    def buttons(self) -> Qt.MouseButton:
        return self._buttons

    def modifiers(self) -> Qt.KeyboardModifier:
        return Qt.KeyboardModifier.NoModifier

    def accept(self) -> None:
        self.accepted = True

    def ignore(self) -> None:
        self.ignored = True


class _FakeDropEvent:
    def __init__(self, mime: QMimeData, point: QPointF = QPointF(120.0, 90.0)) -> None:
        self._mime = mime
        self._point = QPointF(point)
        self.accepted = False
        self.ignored = False

    def mimeData(self) -> QMimeData:
        return self._mime

    def position(self) -> QPointF:
        return QPointF(self._point)

    def acceptProposedAction(self) -> None:
        self.accepted = True

    def ignore(self) -> None:
        self.ignored = True


def test_viewport_item_gizmo_and_drop_boundaries(
    qt_app: QApplication, tmp_path: Path
) -> None:
    item = SceneObjectGraphicsItem(
        "item",
        QPolygonF([QPointF(-10.0, -10.0), QPointF(10.0, -10.0), QPointF(0.0, 10.0)]),
    )
    pressed: list[str] = []
    moved: list[str] = []
    released: list[str] = []
    item.pressed.connect(lambda object_id, *_args: pressed.append(object_id))
    item.moved.connect(lambda object_id, *_args: moved.append(object_id))
    item.released.connect(lambda object_id, *_args: released.append(object_id))
    item.set_interaction_enabled(False)
    item.set_interaction_enabled(True)
    item._pressed = True
    item._refresh_style()
    item._pressed = False
    item.set_selected_style(True)
    item._hovered = True
    item._refresh_style()
    image = QImage(64, 64, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    item.paint(painter, None, None)
    painter.end()
    item.mousePressEvent(_FakeMouseEvent(QPointF(1.0, 2.0)))
    item.mouseMoveEvent(_FakeMouseEvent(QPointF(2.0, 3.0)))
    item.mouseReleaseEvent(_FakeMouseEvent(QPointF(3.0, 4.0)))
    assert pressed == ["item"] and moved == ["item"] and released == ["item"]

    gizmo = SceneTransformGizmo()
    started: list[str] = []
    changed: list[str] = []
    finished: list[str] = []
    gizmo.gesture_started.connect(lambda mode, *_args: started.append(mode))
    gizmo.gesture_changed.connect(lambda mode, *_args: changed.append(mode))
    gizmo.gesture_finished.connect(lambda mode, *_args: finished.append(mode))
    gizmo.hoverMoveEvent(_FakeMouseEvent(QPointF(30.0, 0.0)))
    gizmo.hoverMoveEvent(_FakeMouseEvent(QPointF(30.0, 0.0)))
    gizmo.hoverLeaveEvent(_FakeMouseEvent(QPointF(0.0, 0.0)))
    invalid = _FakeMouseEvent(QPointF(55.0, -20.0))
    gizmo.mousePressEvent(invalid)
    assert invalid.ignored is True
    gizmo.mousePressEvent(_FakeMouseEvent(QPointF(0.0, 0.0)))
    gizmo.mouseMoveEvent(_FakeMouseEvent(QPointF(5.0, 6.0)))
    gizmo.mouseReleaseEvent(_FakeMouseEvent(QPointF(7.0, 8.0)))
    gizmo.mouseMoveEvent(_FakeMouseEvent(QPointF(8.0, 9.0)))
    gizmo.mouseReleaseEvent(_FakeMouseEvent(QPointF(8.0, 9.0)))
    assert started == ["translate"]
    assert changed == ["translate"]
    assert finished == ["translate"]

    socket = SceneSocketGraphicsItem("socket", "light", "#ffffff")
    selected_sockets: list[str] = []
    socket.pressed.connect(selected_sockets.append)
    socket.mousePressEvent(_FakeMouseEvent(QPointF(0.0, 0.0)))
    assert selected_sockets == ["socket"]
    assert item.boundingRect().width() > 0.0
    assert socket.boundingRect().height() > 0.0

    root = tmp_path / "project"
    asset_path = root / "assets" / "a.png"
    _write_png(asset_path)
    asset = AssetReferenceRecord(
        id="asset", path="assets/a.png", sha256=sha256_file(asset_path)
    )
    session = SceneAuthoringSession(
        SceneAuthoringModel(_v2_document().model_copy(update={"assets": [asset]}))
    )
    view = SceneAuthoringViewport(session, project_root=root)
    view.resize(640, 480)
    view.show()
    messages: list[str] = []
    view.status_message.connect(messages.append)
    try:
        with pytest.raises(TypeError):
            view.set_preview_enabled(1)
        with pytest.raises(TypeError):
            view.set_authoring_enabled(1)
        with pytest.raises(TypeError):
            view.set_overlay_visible(1)
        with pytest.raises(ValueError):
            view._set_navigation_state(1.0, QPointF(float("inf"), 0.0))
        assert view._zoom_at(QPointF(100.0, 100.0), 0.0) is False
        assert view._fit_object_ids(("missing",), "Frame") is False
        assert view._select_all_visible() == ("a", "b")
        view._apply_marquee_selection(
            QPointF(-100.0, -100.0),
            QPointF(100.0, 100.0),
            Qt.KeyboardModifier.NoModifier,
        )
        view._marquee_selection_before = ("a",)
        view._marquee_primary_before = "a"
        view._apply_marquee_selection(
            QPointF(-100.0, -100.0),
            QPointF(100.0, 100.0),
            Qt.KeyboardModifier.ShiftModifier,
        )
        view._apply_marquee_selection(
            QPointF(-100.0, -100.0),
            QPointF(100.0, 100.0),
            Qt.KeyboardModifier.ControlModifier,
        )
        view.session.clear_selection()
        view._handle_nudge_key(int(Qt.Key.Key_Left), Qt.KeyboardModifier.NoModifier)
        view._handle_duplicate_key()
        view._handle_delete_key()
        view._handle_copy_key()
        qt_app.clipboard().clear()
        view._handle_paste_key()
        view._handle_history_key(redo=False)
        view._handle_history_key(redo=True)
        view.set_overlay_visible(True)
        view.grab()
        view.set_overlay_visible(False)
        view._gesture_start = QPointF(1.0, 1.0)
        view._item_gesture_id = "a"
        view._gesture_layer_id = "back"
        session.begin_gesture()
        view.set_authoring_enabled(False)
        assert view.is_authoring_enabled() is False
        view.set_authoring_enabled(True)

        empty_mime = QMimeData()
        empty_enter = _FakeDropEvent(empty_mime)
        view.dragEnterEvent(empty_enter)
        assert empty_enter.ignored is True
        url_mime = QMimeData()
        url_mime.setUrls([QUrl.fromLocalFile(str(asset_path))])
        url_enter = _FakeDropEvent(url_mime)
        view.dragEnterEvent(url_enter)
        assert url_enter.accepted is True
        text_mime = QMimeData()
        text_mime.setText(str(asset_path))
        text_enter = _FakeDropEvent(text_mime)
        view.dragEnterEvent(text_enter)
        assert text_enter.accepted is True

        view.set_authoring_enabled(False)
        readonly_drop = _FakeDropEvent(url_mime)
        view.dropEvent(readonly_drop)
        assert readonly_drop.ignored is True
        view.set_authoring_enabled(True)
        empty_drop = _FakeDropEvent(empty_mime)
        view.dropEvent(empty_drop)
        assert empty_drop.ignored is True

        invalid_path = tmp_path / "external" / "invalid.png"
        invalid_path.parent.mkdir(parents=True, exist_ok=True)
        invalid_path.write_bytes(b"not an image")
        invalid_mime = QMimeData()
        invalid_mime.setUrls([QUrl.fromLocalFile(str(invalid_path))])
        invalid_drop = _FakeDropEvent(invalid_mime)
        view.dropEvent(invalid_drop)
        assert invalid_drop.ignored is True

        source = tmp_path / "external" / "dropped.png"
        _write_png(source, "#ff8c32")
        drop_mime = QMimeData()
        drop_mime.setUrls([QUrl.fromLocalFile(str(source))])
        first_drop = _FakeDropEvent(drop_mime)
        view.dropEvent(first_drop)
        assert first_drop.accepted is True
        second_drop = _FakeDropEvent(drop_mime)
        view.dropEvent(second_drop)
        assert second_drop.accepted is True
        assert len(session.document.objects) == 4
        assert len(session.document.assets) == 3
    finally:
        view.close()
        qt_app.processEvents()

    no_project_view = SceneAuthoringViewport(session, project_root=None)
    try:
        no_project_drop = _FakeDropEvent(drop_mime)
        no_project_view.dropEvent(no_project_drop)
        assert no_project_drop.ignored is True
    finally:
        no_project_view.close()
        qt_app.processEvents()


def test_viewport_events_socket_states_and_edit_error_paths(
    qt_app: QApplication, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "project"
    asset_path = root / "assets" / "a.png"
    _write_png(asset_path)
    asset = AssetReferenceRecord(
        id="asset", path="assets/a.png", sha256=sha256_file(asset_path)
    )
    document = _v2_document().model_copy(
        update={
            "assets": [asset],
            "sockets": [
                SceneLightSocketRecord(
                    id="light",
                    layer_id="back",
                    position=Point3Record(x=10.0, y=10.0, z=0.0),
                    color="#ffffff",
                ),
                SceneVfxSocketRecord(
                    id="vfx",
                    layer_id="front",
                    position=Point3Record(x=20.0, y=20.0, z=0.0),
                    effect_id="spark",
                ),
                SceneTriggerSocketRecord(
                    id="trigger",
                    layer_id="front",
                    position=Point3Record(x=30.0, y=30.0, z=0.0),
                    event_id="open",
                    size=Point3Record(x=10.0, y=10.0, z=1.0),
                ),
            ],
        }
    )
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    view = SceneAuthoringViewport(session, project_root=root)
    view.resize(640, 480)
    view.show()
    messages: list[str] = []
    view.status_message.connect(messages.append)
    try:
        assert set(view._socket_items) == {"light", "vfx", "trigger"}
        session.set_layer_visibility("front", False)
        assert set(view._socket_items) == {"light"}
        session.set_layer_visibility("front", True)
        assert set(view._socket_items) == {"light", "vfx", "trigger"}
        view._socket_items["vfx"].pressed.emit("vfx")
        assert any("Socket selected: vfx" in message for message in messages)

        pixmap = QPixmap.fromImage(QImage(8, 8, QImage.Format.Format_ARGB32))
        pixmap_item = SceneObjectGraphicsItem(
            "pixmap",
            QPolygonF([QPointF(-4.0, -4.0), QPointF(4.0, -4.0), QPointF(4.0, 4.0)]),
            pixmap,
        )
        pixmap_item.hoverEnterEvent(_FakeMouseEvent(QPointF(0.0, 0.0)))
        pixmap_item.hoverLeaveEvent(_FakeMouseEvent(QPointF(0.0, 0.0)))
        image = QImage(32, 32, QImage.Format.Format_ARGB32)
        painter = QPainter(image)
        pixmap_item.paint(painter, None, None)
        painter.end()
        socket_image = QImage(32, 32, QImage.Format.Format_ARGB32)
        socket_painter = QPainter(socket_image)
        view._socket_items["light"].paint(socket_painter, None, None)
        socket_painter.end()

        class _Wheel:
            def __init__(self, delta: int) -> None:
                self._delta = delta
                self.accepted = False

            def angleDelta(self):
                return type("_Delta", (), {"y": lambda _self: self._delta})()

            def position(self) -> QPointF:
                return QPointF(100.0, 100.0)

            def accept(self) -> None:
                self.accepted = True

        zero_wheel = _Wheel(0)
        view.wheelEvent(zero_wheel)
        assert zero_wheel.accepted is True
        zoom_wheel = _Wheel(120)
        view.wheelEvent(zoom_wheel)
        assert zoom_wheel.accepted is True

        middle_press = _FakeMouseEvent(
            QPointF(100.0, 100.0),
            button=Qt.MouseButton.MiddleButton,
            buttons=Qt.MouseButton.MiddleButton,
        )
        view.mousePressEvent(middle_press)
        view.mouseMoveEvent(
            _FakeMouseEvent(
                QPointF(120.0, 120.0),
                button=Qt.MouseButton.NoButton,
                buttons=Qt.MouseButton.MiddleButton,
            )
        )
        view.mouseReleaseEvent(
            _FakeMouseEvent(
                QPointF(120.0, 120.0),
                button=Qt.MouseButton.MiddleButton,
                buttons=Qt.MouseButton.NoButton,
            )
        )
        blank_press = _FakeMouseEvent(QPointF(620.0, 460.0))
        view.mousePressEvent(blank_press)
        view.mouseMoveEvent(_FakeMouseEvent(QPointF(600.0, 440.0)))
        view.mouseReleaseEvent(_FakeMouseEvent(QPointF(600.0, 440.0)))
        assert blank_press.accepted is True

        view._marquee_selection_before = ("a",)
        view._marquee_primary_before = "b"
        assert view._apply_marquee_selection(
            QPointF(1000.0, 1000.0),
            QPointF(1100.0, 1100.0),
            Qt.KeyboardModifier.ShiftModifier,
        ) == ("a",)

        view.set_preview_enabled(True)
        view.resize(700, 500)
        view.set_preview_enabled(False)

        session.clear_selection()

        def fail(*_args, **_kwargs):
            raise ValueError("forced failure")

        monkeypatch.setattr(session, "nudge_selected", fail)
        monkeypatch.setattr(session, "duplicate_selected", fail)
        monkeypatch.setattr(session, "delete_selected", fail)
        monkeypatch.setattr(session, "copy_selected_payload", fail)
        view._handle_nudge_key(int(Qt.Key.Key_Left), Qt.KeyboardModifier.NoModifier)
        view._handle_duplicate_key()
        view._handle_delete_key()
        view._handle_copy_key()
        mime = QMimeData()
        mime.setData(SCENE_CLIPBOARD_MIME, b"invalid")
        qt_app.clipboard().setMimeData(mime)
        monkeypatch.setattr(session, "paste_payload", fail)
        view._handle_paste_key()
        qt_app.clipboard().clear()

        view._set_selection(["a"], "a")
        view._object_pressed("b", QPointF(0.0, 0.0), Qt.KeyboardModifier.ShiftModifier)
        view._object_released("b", QPointF(1.0, 1.0))
        view._set_selection(["a"], "a")
        view._object_pressed(
            "a", QPointF(0.0, 0.0), Qt.KeyboardModifier.ControlModifier
        )
        view._set_selection(["a"], "a")
        view.set_authoring_enabled(False)
        view._object_pressed("a", QPointF(0.0, 0.0), Qt.KeyboardModifier.NoModifier)
        view.set_authoring_enabled(True)

        view._set_selection(["a"], "a")
        for mode, start, current in (
            ("translate_x", QPointF(0.0, 0.0), QPointF(20.0, 8.0)),
            ("translate_y", QPointF(0.0, 0.0), QPointF(8.0, 20.0)),
            ("scale", QPointF(0.0, 0.0), QPointF(16.0, 16.0)),
            ("rotate", QPointF(40.0, 0.0), QPointF(0.0, 40.0)),
        ):
            view._gizmo_started(mode, start)
            view._gizmo_changed(mode, current)
            view._gizmo_finished(mode, current)
        view._gizmo_started("invalid", QPointF(0.0, 0.0))
        view._gizmo_changed("invalid", QPointF(4.0, 4.0))
        view._gizmo_finished("other", QPointF(4.0, 4.0))
        view._gizmo_start = QPointF(0.0, 0.0)
        view._gesture_mode = "translate"
        session.clear_selection()
        view._gizmo_changed("translate", QPointF(4.0, 4.0))
        view._gizmo_start = None
        view._gesture_mode = None
        view._gizmo_finished("translate", QPointF(0.0, 0.0))

        assert view._edit_block_reason("missing") is None
        locked_object = session.document.objects[0].model_copy(update={"locked": True})
        session.model.document = session.document.model_copy(
            update={
                "objects": [locked_object, *session.document.objects[1:]],
                "sockets": [],
            }
        )
        view.sync()
        assert "object is locked" in view._edit_block_reason("a")
        unlocked_object = locked_object.model_copy(update={"locked": False})
        locked_layer = session.document.layers[0].model_copy(update={"locked": True})
        session.model.document = session.document.model_copy(
            update={
                "objects": [unlocked_object, *session.document.objects[1:]],
                "layers": [locked_layer, *session.document.layers[1:]],
            }
        )
        view.sync()
        assert "layer is locked" in view._edit_block_reason("a")
    finally:
        view.close()
        qt_app.processEvents()

    invalid_svg = tmp_path / "invalid.svg"
    invalid_svg.write_bytes(b"<svg>")
    with pytest.raises(ValueError, match="SVG"):
        SceneAuthoringViewport._load_asset_pixmap(invalid_svg)
    valid_svg = tmp_path / "valid.svg"
    valid_svg.write_bytes(
        b'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="7">'
        b'<rect width="12" height="7" fill="white"/></svg>'
    )
    svg_pixmap = SceneAuthoringViewport._load_asset_pixmap(valid_svg)
    assert svg_pixmap.size().width() == 12
    assert svg_pixmap.size().height() == 7


def test_viewport_remaining_policy_paths(
    qt_app: QApplication, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "project"
    asset_path = root / "assets" / "a.png"
    _write_png(asset_path)
    asset = AssetReferenceRecord(
        id="asset", path="assets/a.png", sha256=sha256_file(asset_path)
    )
    document = _v2_document().model_copy(update={"assets": [asset]})
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    view = SceneAuthoringViewport(session, project_root=root)
    view.resize(640, 480)
    view.show()
    messages: list[str] = []
    view.status_message.connect(messages.append)
    try:
        view._set_selection(["a"], "a")

        class _UnavailableClipboard:
            @staticmethod
            def clipboard():
                return None

        monkeypatch.setattr(
            scene_authoring_viewport_module,
            "QApplication",
            _UnavailableClipboard,
        )
        view._handle_copy_key()
        monkeypatch.undo()

        first_center = view.navigation_center
        assert math.isfinite(first_center.x())
        view._navigation_center = QPointF(3.0, 4.0)
        second_center = view.navigation_center
        assert second_center.x() == pytest.approx(3.0)
        view._navigation_center = None

        assert view._content_bounds(("missing",)) is None
        hidden_item = view._items["a"]
        hidden_item.setVisible(False)
        assert view._content_bounds(("a",)) is None
        hidden_item.setVisible(True)

        view._marquee_selection_before = ("a",)
        view._marquee_primary_before = "missing"
        assert view._apply_marquee_selection(
            QPointF(1000.0, 1000.0),
            QPointF(1100.0, 1100.0),
            Qt.KeyboardModifier.ShiftModifier,
        ) == ("a",)
        view._marquee_primary_before = "a"
        assert view._apply_marquee_selection(
            QPointF(1000.0, 1000.0),
            QPointF(1100.0, 1100.0),
            Qt.KeyboardModifier.ShiftModifier,
        ) == ("a",)

        class _ModifiedMouseEvent(_FakeMouseEvent):
            def __init__(self, point: QPointF, modifier: Qt.KeyboardModifier) -> None:
                super().__init__(point)
                self._modifier = modifier

            def modifiers(self) -> Qt.KeyboardModifier:
                return self._modifier

        view.mousePressEvent(
            _ModifiedMouseEvent(
                QPointF(620.0, 460.0),
                Qt.KeyboardModifier.ShiftModifier,
            )
        )
        view._clear_marquee()
        view.grab()
        view.keyPressEvent(
            QKeyEvent(
                QEvent.Type.KeyPress,
                int(Qt.Key.Key_Space),
                Qt.KeyboardModifier.NoModifier,
            )
        )
        view.mousePressEvent(
            QMouseEvent(
                QEvent.Type.MouseButtonPress,
                QPointF(620.0, 460.0),
                Qt.MouseButton.RightButton,
                Qt.MouseButton.RightButton,
                Qt.KeyboardModifier.NoModifier,
            )
        )

        session.set_selection(["a"], "a")
        reduced_document = document.model_copy(
            update={"objects": [document.objects[1]]}
        )
        session.model.document = reduced_document
        view.sync()
        monkeypatch.setattr(view, "_set_selection", lambda *_args: None)
        view._object_pressed("a", QPointF(0.0, 0.0), Qt.KeyboardModifier.NoModifier)
        monkeypatch.undo()
        session.model.document = document
        view.sync()

        view.set_authoring_enabled(False)
        view._handle_history_key(redo=False)
        view.set_authoring_enabled(True)

        view.keyPressEvent(
            QKeyEvent(
                QEvent.Type.KeyPress,
                int(Qt.Key.Key_Escape),
                Qt.KeyboardModifier.NoModifier,
            )
        )
        view._set_selection(["a"], "a")
        view._marquee_origin = QPointF(0.0, 0.0)
        view._marquee_current = QPointF(8.0, 8.0)
        view._marquee_selection_before = ("a",)
        view._marquee_primary_before = "b"
        view.keyPressEvent(
            QKeyEvent(
                QEvent.Type.KeyPress,
                int(Qt.Key.Key_Escape),
                Qt.KeyboardModifier.NoModifier,
            )
        )

        view._set_selection((), None)
        view._object_pressed("b", QPointF(0.0, 0.0), Qt.KeyboardModifier.ShiftModifier)
        view._object_released("b", QPointF(2.0, 2.0))

        view.set_authoring_enabled(False)
        disabled_enter = _FakeDropEvent(QMimeData())
        view.dragEnterEvent(disabled_enter)
        assert disabled_enter.ignored is True
        view.set_authoring_enabled(True)

        locked_group = SceneGroupAuthoringRecordV2(
            id="locked_group",
            name="Locked",
            members=["a"],
            locked=True,
        )
        session.model.document = document.model_copy(update={"groups": [locked_group]})
        view.sync()
        view._set_selection(["a"], "a")
        assert "group 'Locked' is locked" in view._edit_block_reason("a")
        view._gizmo_start = QPointF(0.0, 0.0)
        view._gesture_mode = "translate"
        session.begin_gesture()
        view._gizmo_changed("translate", QPointF(8.0, 8.0))
        assert view._gizmo_start is None
        view._item_gesture_id = "a"
        view._gesture_layer_id = "back"
        view._gesture_start = QPointF(0.0, 0.0)
        session.begin_gesture()
        view._object_moved("a", QPointF(8.0, 8.0))
        assert view._gesture_start is None

        view._authoring_enabled = False
        view._gizmo_start = QPointF(0.0, 0.0)
        view._gesture_mode = "translate"
        view._gizmo_finished("translate", QPointF(4.0, 4.0))
        assert view._gizmo_start is not None
        view._gizmo_start = None
        view._gesture_mode = None
        view._authoring_enabled = True

        missing_object = document.objects[0].model_copy(
            update={"asset_id": "missing_asset"}
        )
        session.model.document = document.model_copy(
            update={"objects": [missing_object, *document.objects[1:]]}
        )
        view.sync()
        assert any(
            "asset record is missing" in diagnostic
            for diagnostic in view._asset_diagnostics
        )
    finally:
        view.close()
        qt_app.processEvents()
