"""E08-C.4 material authoring, renderer wiring and persistence tests."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.core.scene_lighting import SceneLightingSettings, shade_color
from src.persistence.scene_authoring_io import (
    load_scene_authoring_v2,
    save_scene_authoring,
)
from src.persistence.scene_authoring_schema import (
    SceneMaterialAuthoringRecord,
    SceneObjectAuthoringRecord,
)
from src.ui.scene_authoring_inspector import SceneAuthoringInspector
from src.ui.scene_authoring_viewport import SceneAuthoringViewport

FIXTURE = Path(__file__).parent / "fixtures" / "e08_lighting_smoke.ndtscene.json"


def _document():
    return load_scene_authoring_v2(FIXTURE, verify_assets=False)


def test_v2_material_is_typed_and_changes_renderer_pixels() -> None:
    document = _document()
    receiver = next(item for item in document.objects if item.id == "lighting-receiver")
    assert isinstance(receiver, SceneObjectAuthoringRecord)
    assert receiver.material.albedo == "#405070"
    lighting_material = SceneAuthoringViewport._lighting_material_for_object(receiver)

    lit, _, _ = shade_color((-200.0, -20.0), lighting_material, SceneLightingSettings())
    default, _, _ = shade_color(
        (-200.0, -20.0),
        SceneAuthoringViewport._lighting_material_for_object(
            receiver.model_copy(update={"material": SceneMaterialAuthoringRecord()})
        ),
        SceneLightingSettings(),
    )
    assert lit != default


def test_v2_material_save_reopen_preserves_all_authoring_fields(tmp_path: Path) -> None:
    document = _document()
    destination = tmp_path / "lighting.ndtscene.json"
    save_scene_authoring(document, destination)

    reopened = load_scene_authoring_v2(destination, verify_assets=False)
    receiver = next(item for item in reopened.objects if item.id == "lighting-receiver")
    assert receiver.material.normal_map_xy.x == 0.7
    assert receiver.material.normal_map_xy.y == -0.3
    assert receiver.material.normal_strength == 0.8
    assert receiver.material.emission == "#101820"
    assert receiver.material.emission_strength == 0.1
    assert receiver.material.opacity == 0.92
    assert receiver.material.receives_shadow is True
    assert receiver.material.casts_shadow is True


def test_material_inspector_edit_is_transactional_and_undoable() -> None:
    app = QApplication.instance() or QApplication([])
    del app
    session = SceneAuthoringSession(SceneAuthoringModel(_document()))
    session.set_selection(["lighting-receiver"])
    inspector = SceneAuthoringInspector(session)
    inspector.update_language("pt")
    inspector.material_albedo.setText("#ff2200")
    inspector.material_normal_x.setValue(-0.4)
    inspector.material_normal_strength.setValue(0.9)
    inspector.material_apply_button.click()

    changed = next(
        item for item in session.document.objects if item.id == "lighting-receiver"
    )
    assert changed.material.albedo == "#ff2200"
    assert changed.material.normal_map_xy.x == -0.4
    assert session.can_undo is True
    assert session.undo() is True
    restored = next(
        item for item in session.document.objects if item.id == "lighting-receiver"
    )
    assert restored.material.albedo == "#405070"
    inspector.close()


def test_material_inspector_can_initialize_material_for_new_v2_object() -> None:
    app = QApplication.instance() or QApplication([])
    del app
    document = _document()
    document = document.model_copy(
        update={
            "objects": [
                (
                    item.model_copy(update={"material": None})
                    if item.id == "lighting-receiver"
                    else item
                )
                for item in document.objects
            ]
        }
    )
    session = SceneAuthoringSession(SceneAuthoringModel(document))
    session.set_selection(["lighting-receiver"])
    inspector = SceneAuthoringInspector(session)
    try:
        assert inspector.material_albedo.isEnabled()
        assert inspector.material_apply_button.isEnabled()
        assert inspector.material_albedo.text() == "#ffffff"

        inspector.material_albedo.setText("#ff2200")
        inspector.material_apply_button.click()

        changed = next(
            item for item in session.document.objects if item.id == "lighting-receiver"
        )
        assert changed.material is not None
        assert changed.material.albedo == "#ff2200"
        assert session.can_undo is True
    finally:
        inspector.close()
