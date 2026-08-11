from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

import tools.run_legacy_tests as legacy_runner
from src.collision import polygon_collision_sat
from src.core.commands import CommandManager
from src.core.view_processor import ViewProcessor
from src.exporters.atlas_exporter import pack_sprites_to_atlas
from src.launcher import build_parser, run_headless
from src.models.scene import Scene
from src.tools.edge_utils import sobel_magnitude
from src.tools.lasso import LassoTool as CompatibilityLassoTool
from src.tools.lasso_tool import LassoTool as CanonicalLassoTool
from src.ui.layers_panel import LayersPanel
from src.ui.main_window import MainWindow
from src.ui.mask_viewer import MaskViewer
from src.ui.theme_qss import QSS
from tools.run_legacy_tests import (
    reconcile_failures,
    resolve_tested_commit,
    working_tree_is_dirty,
)


def test_legacy_report_records_verified_tested_commit(
    monkeypatch, tmp_path: Path
) -> None:
    expected = "a" * 40
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    monkeypatch.setattr(
        legacy_runner.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, expected + "\n", ""
        ),
    )

    assert resolve_tested_commit(tmp_path) == expected


def test_legacy_report_rejects_ci_commit_mismatch(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GITHUB_SHA", "b" * 40)
    monkeypatch.setattr(
        legacy_runner.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, "a" * 40 + "\n", ""
        ),
    )

    with pytest.raises(RuntimeError, match="does not match CI commit"):
        resolve_tested_commit(tmp_path)


@pytest.mark.parametrize(("output", "expected"), [("", False), (" M file.py\n", True)])
def test_legacy_report_records_working_tree_state(
    monkeypatch, tmp_path: Path, output: str, expected: bool
) -> None:
    monkeypatch.setattr(
        legacy_runner.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, output, ""),
    )

    assert working_tree_is_dirty(tmp_path) is expected


class _ConfigStub:
    def get(self, key, default=None):
        return default


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def test_headless_object_export_requires_object_id(tmp_path: Path) -> None:
    output = tmp_path / "object.glb"
    args = build_parser().parse_args(
        ["--headless", "--export-object-gltf", str(output)]
    )

    assert run_headless(args) == 1
    assert not output.exists()


def test_atlas_crop_preserves_transparent_frame_bounds() -> None:
    image = Image.new("RGBA", (291, 219), (255, 255, 255, 255))
    for y in range(image.height):
        image.putpixel((image.width - 1, y), (0, 0, 0, 0))

    [(atlas, entries)] = pack_sprites_to_atlas(
        [(image, {"name": "transparent-edge"})],
        max_size=(300, 230),
        padding=0,
    )

    rect = entries[0]["rect"]
    assert atlas.size == image.size
    assert rect["x"] + rect["w"] <= atlas.width
    assert rect["y"] + rect["h"] <= atlas.height


def test_rotated_atlas_metadata_uses_physical_dimensions() -> None:
    image = Image.new("RGBA", (3, 5), (255, 255, 255, 255))

    [(atlas, entries)] = pack_sprites_to_atlas(
        [(image, {"name": "rotated"})],
        max_size=(5, 4),
        padding=0,
        allow_rotate=True,
    )

    assert atlas.size == (5, 3)
    assert entries[0]["rotated"] is True
    assert entries[0]["rect"] == {"x": 0, "y": 0, "w": 5, "h": 3}


def test_collision_panel_export_writes_real_atomic_json(
    qt_app, tmp_path: Path, monkeypatch
) -> None:
    scene = Scene()
    scene.cmd = CommandManager()
    scene.add_object("BOX", [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0)])
    scene.collision_shapes = {"BOX": [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0)]}
    window = MainWindow(scene, _ConfigStub())
    output = tmp_path / "collision-results.json"
    messages = []
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(output), "JSON Files (*.json)"),
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: messages.append(args[2]),
    )
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)
    window.collision_panel.collision_results = [
        {"obj1_id": "BOX", "obj2_id": "OTHER", "colliding": False}
    ]

    assert window._on_collision_export() is True
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["format_id"] == "neoeng-d-trace-collisions"
    assert payload["shapes"][0]["object_id"] == "BOX"
    assert payload["shapes"][0]["points"][2] == [4.0, 4.0]
    assert payload["results"][0]["obj1_id"] == "BOX"
    assert messages == [f"Collision data exported to {output}"]
    assert [path.name for path in tmp_path.iterdir()] == [output.name]

    window._mark_document_clean()
    window.close()


def test_collision_panel_export_cancel_has_no_success(qt_app, monkeypatch) -> None:
    scene = Scene()
    scene.cmd = CommandManager()
    window = MainWindow(scene, _ConfigStub())
    messages = []
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: ("", ""),
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: messages.append(args[2]),
    )

    assert window._on_collision_export() is False
    assert messages == []

    window._mark_document_clean()
    window.close()


def test_sobel_magnitude_uses_float32_without_clipping() -> None:
    image = np.zeros((16, 16), dtype=np.uint8)
    image[:, 8:] = 255

    magnitude = sobel_magnitude(image)

    assert magnitude.dtype == np.float32
    assert np.isfinite(magnitude).all()
    assert float(magnitude.max()) > 255.0


def test_mask_viewer_reset_fills_and_centers_viewport(qt_app) -> None:
    viewer = MaskViewer()
    viewer.resize(400, 300)
    viewer.set_numpy_image(np.zeros((200, 300, 3), dtype=np.uint8))

    viewer.reset_view()

    zoom, pan_x, pan_y = viewer.get_view_transform()
    assert zoom == 1.5
    assert pan_x == -25.0
    assert pan_y == 0.0
    viewer.close()


def test_pil_image_converts_to_qimage() -> None:
    image = Image.new("RGBA", (7, 5), (10, 20, 30, 255))

    converted = ViewProcessor.to_qimage(image)

    assert converted is not None
    assert converted.width() == 7
    assert converted.height() == 5


def test_lasso_compatibility_module_reexports_canonical_class() -> None:
    assert CompatibilityLassoTool is CanonicalLassoTool


def test_collision_compatibility_api_is_covered() -> None:
    first = np.asarray([(0, 0), (4, 0), (4, 4), (0, 4)], dtype=np.float64)
    overlapping = np.asarray([(3, 1), (6, 1), (6, 3), (3, 3)], dtype=np.float64)
    separate = np.asarray([(5, 5), (7, 5), (7, 7), (5, 7)], dtype=np.float64)

    collides, mtv = polygon_collision_sat(first, overlapping)
    misses, no_mtv = polygon_collision_sat(first, separate)

    assert collides is True
    assert mtv is not None and mtv.shape == (2,)
    assert misses is False
    assert no_mtv is None


def test_theme_and_layers_are_connected_to_runtime(qt_app) -> None:
    assert "QMainWindow" in QSS
    scene = Scene()
    scene.cmd = CommandManager()
    window = MainWindow(scene, _ConfigStub())

    assert isinstance(window.layers, LayersPanel)
    assert window.layers.list.count() == len(scene.layers)

    window._mark_document_clean()
    window.close()


def test_legacy_reconciliation_rejects_duplicate_failure_ids() -> None:
    detail = {
        "classname": "tests.test_sample.TestSample",
        "name": "test_contract",
        "kind": "failure",
        "message": "expected signature",
        "body": "",
    }
    identifier = "test_sample::tests.test_sample.TestSample::test_contract"
    report = reconcile_failures(
        [{"path": "tests/test_sample.py"}],
        [{"file": "test_sample.py", "failure_details": [detail, detail.copy()]}],
        {
            identifier: {
                "kind": "failure",
                "message_contains": "expected signature",
            }
        },
    )

    assert report["status"] == "failed"
    assert report["matched_failures"] == 1
    assert report["unexpected_failures"] == [
        {"id": identifier, "reason": "duplicate observed failure id"}
    ]
