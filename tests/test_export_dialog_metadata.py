import json

import pytest
from PySide6.QtWidgets import QApplication

from src.core.validation_events import start_validation_session, stop_validation_session
from src.models.scene import Scene
from src.ui import export_dialog as export_dialog_module
from src.ui.export_dialog import ExportDialog


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def scene_with_selection():
    scene = Scene()
    scene.add_object(
        "hero/player 01",
        [(10, 10), (50, 10), (50, 50), (10, 50)],
    )
    scene.select_object("hero/player 01")
    return scene


def test_dialog_exposes_all_metadata_profiles(qt_app, scene_with_selection):
    dialog = ExportDialog(scene_with_selection)
    profiles = [
        dialog.metadata_profile.itemData(index)
        for index in range(dialog.metadata_profile.count())
    ]

    assert profiles == ["generic", "godot", "unity", "phaser"]
    assert dialog.btn_single.isEnabled() is export_dialog_module.HAS_SPRITE_EXPORTER
    assert dialog.btn_batch.isEnabled() is export_dialog_module.HAS_SPRITE_EXPORTER
    assert dialog.btn_atlas.isEnabled() is export_dialog_module.HAS_ATLAS_EXPORTER
    assert (
        dialog.btn_metadata_selected.isEnabled()
        is export_dialog_module.HAS_METADATA_EXPORTER
    )
    assert dialog.btn_gltf_scene.isEnabled() is export_dialog_module.HAS_GLTF_EXPORTER
    assert dialog.btn_gltf_object.isEnabled() is export_dialog_module.HAS_GLTF_EXPORTER
    dialog.close()


@pytest.mark.parametrize(
    ("profile", "required_key"),
    [
        ("generic", "id"),
        ("godot", "offset"),
        ("unity", "border"),
        ("phaser", "frame"),
    ],
)
def test_export_selected_metadata_from_dialog(
    qt_app,
    scene_with_selection,
    tmp_path,
    monkeypatch,
    profile,
    required_key,
):
    dialog = ExportDialog(scene_with_selection)
    index = dialog.metadata_profile.findData(profile)
    assert index >= 0
    dialog.metadata_profile.setCurrentIndex(index)

    destination_without_extension = tmp_path / f"metadata-{profile}"
    monkeypatch.setattr(
        export_dialog_module.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(destination_without_extension), ""),
    )

    messages = []
    monkeypatch.setattr(
        export_dialog_module.QMessageBox,
        "information",
        lambda *args: messages.append(args),
    )
    monkeypatch.setattr(
        export_dialog_module.QMessageBox,
        "critical",
        lambda *args: pytest.fail(f"Unexpected critical message: {args}"),
    )

    dialog.export_selected_metadata()

    output = destination_without_extension.with_suffix(".json")
    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert required_key in data
    assert messages
    dialog.close()


def test_metadata_export_does_not_require_source_image(
    qt_app, scene_with_selection, tmp_path, monkeypatch
):
    assert scene_with_selection.image is None
    dialog = ExportDialog(scene_with_selection)
    destination = tmp_path / "without-image.json"

    monkeypatch.setattr(
        export_dialog_module.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(destination), ""),
    )
    monkeypatch.setattr(
        export_dialog_module.QMessageBox,
        "information",
        lambda *args: None,
    )
    monkeypatch.setattr(
        export_dialog_module.QMessageBox,
        "critical",
        lambda *args: pytest.fail(f"Unexpected critical message: {args}"),
    )

    dialog.export_selected_metadata()

    assert destination.exists()
    dialog.close()


def test_metadata_export_requires_a_selected_object(qt_app, monkeypatch):
    scene = Scene()
    scene.add_object(
        "object",
        [(0, 0), (10, 0), (10, 10), (0, 10)],
    )
    dialog = ExportDialog(scene)

    messages = []
    monkeypatch.setattr(
        export_dialog_module.QMessageBox,
        "information",
        lambda *args: messages.append(args),
    )
    monkeypatch.setattr(
        export_dialog_module.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: pytest.fail(
            "Save dialog must not open without a selection"
        ),
    )

    dialog.export_selected_metadata()

    assert messages
    assert "No object selected" in messages[0][2]
    dialog.close()


def test_safe_filename_for_metadata_export():
    assert ExportDialog._safe_filename("hero/player 01") == "hero_player_01"
    assert ExportDialog._safe_filename("***") == "object"


def test_validation_mode_uses_private_output_without_save_dialog(
    qt_app, scene_with_selection, tmp_path, monkeypatch
):
    dialog = ExportDialog(scene_with_selection)
    sandbox = tmp_path / "export_outputs"

    def allocate(relative_path, *, directory=False):
        target = sandbox / relative_path
        if directory:
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
        return target

    monkeypatch.setattr(
        export_dialog_module,
        "validation_output_path",
        allocate,
    )
    monkeypatch.setattr(
        export_dialog_module.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: pytest.fail(
            "Validation sandbox must bypass the native save dialog"
        ),
    )
    monkeypatch.setattr(
        export_dialog_module.QMessageBox,
        "information",
        lambda *args: None,
    )
    monkeypatch.setattr(
        export_dialog_module.QMessageBox,
        "critical",
        lambda *args: pytest.fail(f"Unexpected critical message: {args}"),
    )

    dialog.export_selected_metadata()

    assert (sandbox / "selected-generic-metadata.json").is_file()
    dialog.close()


def test_failed_validation_postcondition_records_one_domain_failure(
    qt_app, scene_with_selection, tmp_path, monkeypatch
):
    log_path = tmp_path / "manual-validation.jsonl"
    dialog = ExportDialog(scene_with_selection)
    messages = []

    monkeypatch.setattr(
        export_dialog_module, "export_metadata", lambda *args, **kwargs: {}
    )
    monkeypatch.setattr(
        export_dialog_module.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: pytest.fail(
            "Validation sandbox must bypass the native save dialog"
        ),
    )
    monkeypatch.setattr(
        export_dialog_module.QMessageBox,
        "information",
        lambda *args: pytest.fail(f"Unexpected success message: {args}"),
    )
    monkeypatch.setattr(
        export_dialog_module.QMessageBox,
        "critical",
        lambda *args: messages.append(args),
    )

    start_validation_session(log_path)
    try:
        dialog.export_selected_metadata()
    finally:
        stop_validation_session(exit_code=0, expected_events=("export.metadata",))
        dialog.close()

    rows = [
        json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()
    ]
    failures = [row for row in rows if row["event"] == "export.metadata"]
    assert len(failures) == 1
    assert failures[0]["status"] == "FAILURE"
    assert failures[0]["details"]["valid_json"] is False
    assert not [row for row in rows if row["event"] == "python.log"]
    assert rows[-1]["status"] == "FAILURE"
    assert rows[-1]["details"]["failure_count"] == 1
    assert messages
