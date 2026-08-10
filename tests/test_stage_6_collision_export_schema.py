from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from src.core.commands import CommandManager
from src.exporters import collision_exporter
from src.exporters.collision_exporter import (
    COLLISION_FORMAT_ID,
    COLLISION_SCHEMA_VERSION,
    collision_shape_record,
    export_collision_document,
)
from src.exporters.json_exporter import export_metadata, export_scene_metadata
from src.models.scene import Scene
from src.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


class _ConfigStub:
    def get(self, key, default=None):
        return default

    def set(self, key, value):
        return None


def _scene() -> Scene:
    scene = Scene()
    scene.cmd = CommandManager()
    scene.add_object("B", [(10.0, 10.0), (14.0, 10.0), (14.0, 14.0)])
    scene.add_object("A", [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0)])
    scene.collision_shapes = {
        "B": [(11.0, 11.0), (13.0, 11.0), (13.0, 13.0)],
        "A": [(0.0, 0.0), (3.0, 0.0), (3.0, 3.0)],
    }
    return scene


def test_collision_document_is_versioned_deterministic_and_json_round_trips(
    tmp_path: Path,
) -> None:
    scene = _scene()
    document = export_collision_document(
        scene,
        results=[
            {
                "obj1_id": "A",
                "obj2_id": "B",
                "colliding": True,
                "mtv": (1, -2),
            }
        ],
        statistics={"collision_rate": 0.5, "total_objects": 2},
    )

    assert document["format_id"] == COLLISION_FORMAT_ID
    assert document["schema_version"] == COLLISION_SCHEMA_VERSION
    assert document["coordinate_space"] == "image"
    assert [shape["object_id"] for shape in document["shapes"]] == ["A", "B"]
    assert document["shapes"][0]["points"][2] == [3.0, 3.0]
    assert document["results"][0]["mtv"] == [1.0, -2.0]

    output = tmp_path / "collisions.json"
    output.write_text(json.dumps(document, indent=2), encoding="utf-8")
    assert json.loads(output.read_text(encoding="utf-8")) == document


def test_generic_scene_and_object_metadata_share_the_canonical_collision() -> None:
    scene = _scene()
    expected = collision_shape_record(scene, "A")

    scene_entry = next(
        entry for entry in export_scene_metadata(scene)["sprites"] if entry["id"] == "A"
    )
    object_entry = export_metadata("A", scene, "", profile="generic")

    assert scene_entry["collision"] == expected
    assert object_entry["collision"] == expected


@pytest.mark.parametrize(
    "points, message",
    [
        ([(0.0, 0.0), (1.0, 1.0)], "three distinct points"),
        ([(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)], "non-zero area"),
        ([(0.0, 0.0), (1.0, 0.0), (math.inf, 1.0)], "finite number"),
    ],
)
def test_invalid_collision_geometry_is_rejected(points, message: str) -> None:
    scene = _scene()
    scene.collision_shapes["A"] = points

    with pytest.raises(ValueError, match=message):
        export_collision_document(scene)


def test_orphan_collision_is_rejected() -> None:
    scene = _scene()
    scene.collision_shapes["missing"] = [(0, 0), (1, 0), (1, 1)]

    with pytest.raises(ValueError, match="unknown object: missing"):
        export_collision_document(scene)


def test_toolbar_and_panel_write_the_same_canonical_root_schema(
    qt_app, tmp_path: Path, monkeypatch
) -> None:
    scene = _scene()
    window = MainWindow(scene, _ConfigStub())
    outputs = iter((tmp_path / "toolbar.json", tmp_path / "panel.json"))
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(next(outputs)), "JSON Files (*.json)"),
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)
    window.collision_panel.collision_results = [
        {"obj1_id": "A", "obj2_id": "B", "colliding": False, "mtv": None}
    ]

    assert window.export_collision_json() is True
    assert window._on_collision_export() is True

    toolbar = json.loads((tmp_path / "toolbar.json").read_text(encoding="utf-8"))
    panel = json.loads((tmp_path / "panel.json").read_text(encoding="utf-8"))
    assert (
        set(toolbar)
        == set(panel)
        == {
            "format_id",
            "schema_version",
            "coordinate_space",
            "shapes",
            "results",
            "statistics",
        }
    )
    assert toolbar["shapes"] == panel["shapes"]
    assert toolbar["results"] == []
    assert panel["results"][0]["obj1_id"] == "A"

    window._mark_document_clean()
    window.close()


def test_collision_text_export_is_atomic_and_derived_from_canonical_schema(
    tmp_path: Path, monkeypatch
) -> None:
    document = export_collision_document(_scene())
    output = tmp_path / "collisions.txt"
    output.write_text("previous", encoding="utf-8")

    original_replace = collision_exporter.os.replace
    replacements = []

    def tracked_replace(source, destination):
        replacements.append((Path(source), Path(destination)))
        original_replace(source, destination)

    monkeypatch.setattr(collision_exporter.os, "replace", tracked_replace)
    collision_exporter.save_collision_text(document, str(output))

    assert replacements and replacements[0][1] == output
    assert output.read_text(encoding="utf-8") == (
        "Object A:\n"
        "  (0.0, 0.0)\n"
        "  (3.0, 0.0)\n"
        "  (3.0, 3.0)\n"
        "\n"
        "Object B:\n"
        "  (11.0, 11.0)\n"
        "  (13.0, 11.0)\n"
        "  (13.0, 13.0)\n"
    )
    assert [path.name for path in tmp_path.iterdir()] == [output.name]


def test_collision_text_replace_failure_preserves_destination(
    tmp_path: Path, monkeypatch
) -> None:
    output = tmp_path / "collisions.txt"
    output.write_text("previous", encoding="utf-8")

    def fail_replace(source, destination):
        raise OSError("replace failed")

    monkeypatch.setattr(collision_exporter.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        collision_exporter.save_collision_text(
            export_collision_document(_scene()),
            str(output),
        )

    assert output.read_text(encoding="utf-8") == "previous"
    assert [path.name for path in tmp_path.iterdir()] == [output.name]


def test_invalid_collision_fails_closed_before_file_dialog(qt_app, monkeypatch) -> None:
    scene = _scene()
    scene.collision_shapes["A"] = [(0, 0), (1, 1), (2, 2)]
    window = MainWindow(scene, _ConfigStub())
    errors = []
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: pytest.fail("dialog must not open for invalid data"),
    )
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda *args, **kwargs: errors.append(args[2]),
    )

    assert window.export_collision_json() is False
    assert len(errors) == 1
    assert "non-zero area" in errors[0]

    window._mark_document_clean()
    window.close()
