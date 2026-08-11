"""Stage 11 residual branch contracts for collision UI and sprite export."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication, QMessageBox

import src.exporters.sprite_exporter as sprite_module
from src.core.commands import CommandManager, CommandStatus
from src.exporters.sprite_exporter import (
    export_sprite,
    extract_masked_sprite,
    save_sprite,
)
from src.models.scene import Scene
from src.ui.collision_panel import CollisionPanel

BEZIERS = [((0.0, 0.0), (0.0, -2.0), (2.0, -2.0), (2.0, 0.0))]


class _CollisionObject:
    def __init__(self, shape):
        self.shape = shape


class _Manager:
    def __init__(self):
        self.objects = {}
        self.fail_register = False
        self.fail_clear = False

    def clear(self):
        if self.fail_clear:
            raise RuntimeError("clear failed")
        self.objects.clear()

    def register(self, object_id, shape):
        if self.fail_register:
            raise RuntimeError("register failed")
        self.objects[object_id] = _CollisionObject(shape)

    def batch_test(self):
        return [
            SimpleNamespace(obj1_id="A", obj2_id="B", colliding=True, mtv=(1.0, 2.0))
        ]

    def get_stats(self):
        return {"total_objects": len(self.objects), "collision_rate": 1.0}


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def quiet_messages(monkeypatch):
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)


def test_collision_panel_optional_subscription_alias_stats_and_results(qt_app) -> None:
    bare_scene = SimpleNamespace(collision_shapes={}, cmd=None)
    panel = CollisionPanel(bare_scene)
    assert panel._sync_collision_manager_from_scene() is True

    manager = _Manager()
    panel.set_physics_manager(manager)
    assert panel.collision_manager is manager
    panel.update_statistics({})
    assert "No statistics" in panel.stats_text.toPlainText()
    panel.update_statistics(
        {
            "total_objects": 2,
            "grid_cell_size": 64,
            "occupied_cells": 1,
            "avg_objects_per_cell": 2.0,
            "total_collision_tests": 1,
            "total_collisions_found": 1,
            "collision_rate": 1.0,
        }
    )
    assert "Total Objects: 2" in panel.stats_text.toPlainText()

    panel.update_collision_results([])
    assert "No collision results" in panel.results_text.toPlainText()
    panel.update_collision_results(
        [
            {"obj1_id": "A", "obj2_id": "B", "colliding": True, "mtv": (1, 2)},
            {"obj1_id": "A", "obj2_id": "C", "colliding": True},
            {"obj1_id": "B", "obj2_id": "C", "colliding": False},
        ]
    )
    text = panel.results_text.toPlainText()
    assert "MTV: (1.00, 2.00)" in text and "2 collisions" in text
    panel.close()


def test_collision_panel_sync_failure_restore_and_restore_failure(qt_app) -> None:
    scene = SimpleNamespace(
        collision_shapes={"NEW": [(0, 0), (2, 0), (0, 2)]}, cmd=None
    )
    panel = CollisionPanel(scene)
    manager = _Manager()
    manager.objects = {"OLD": _CollisionObject([(0, 0), (1, 0), (0, 1)])}
    manager.fail_register = True
    panel.collision_manager = manager
    assert panel._sync_collision_manager_from_scene() is False

    manager = _Manager()
    manager.objects = {"OLD": _CollisionObject([(0, 0), (1, 0), (0, 1)])}
    calls = 0

    def fail_clear_twice():
        nonlocal calls
        calls += 1
        raise RuntimeError(f"clear {calls}")

    manager.clear = fail_clear_twice
    panel.collision_manager = manager
    assert panel._sync_collision_manager_from_scene() is False
    assert calls == 2
    panel.close()


def test_collision_panel_batch_export_and_auto_generate_failures(
    qt_app, monkeypatch
) -> None:
    scene = Scene()
    scene.cmd = CommandManager()
    panel = CollisionPanel(scene)
    panel._on_batch_test()

    manager = _Manager()
    panel.collision_manager = manager
    panel._on_batch_test()
    scene.collision_shapes = {"A": [(0, 0), (2, 0), (0, 2)]}
    monkeypatch.setattr(panel, "_sync_collision_manager_from_scene", lambda: False)
    panel._on_batch_test()

    manager.objects = {"A": _CollisionObject(scene.collision_shapes["A"])}
    manager.batch_test = lambda: (_ for _ in ()).throw(RuntimeError("batch failed"))
    panel._on_batch_test()

    panel.collision_results = []
    panel._on_export_collisions()
    emitted = []
    panel.export_collisions_requested.connect(lambda: emitted.append(True))
    panel.collision_results = [{"colliding": False}]
    panel._on_export_collisions()
    assert emitted == [True]

    for status in (CommandStatus.FAILED, CommandStatus.REJECTED):
        scene.cmd = SimpleNamespace(
            execute=lambda *args, status=status: SimpleNamespace(
                changed=False, status=status, message=status.value
            )
        )
        panel._on_auto_generate()

    scene.cmd = SimpleNamespace(
        execute=lambda *args: SimpleNamespace(
            changed=True, status=CommandStatus.APPLIED
        )
    )
    panel._on_auto_generate()
    scene.cmd = SimpleNamespace(
        execute=lambda *args: (_ for _ in ()).throw(RuntimeError("generate failed"))
    )
    panel._on_auto_generate()
    panel.close()


def test_sprite_input_conversion_with_and_without_cv2(monkeypatch) -> None:
    pil = Image.new("RGB", (2, 2), (1, 2, 3))
    assert sprite_module._to_pil_rgba(pil).mode == "RGBA"
    with pytest.raises(ValueError, match="np.ndarray"):
        sprite_module._to_pil_rgba(object())
    with pytest.raises(ValueError, match="Unsupported"):
        sprite_module._to_pil_rgba(np.zeros((2, 2), dtype=np.uint8))

    bgr = np.zeros((2, 2, 3), dtype=np.uint8)
    bgra = np.zeros((2, 2, 4), dtype=np.uint8)
    assert sprite_module._to_pil_rgba(bgr).mode == "RGBA"
    assert sprite_module._to_pil_rgba(bgra).mode == "RGBA"
    monkeypatch.setattr(sprite_module, "_HAS_CV2", False)
    assert sprite_module._to_pil_rgba(bgr).mode == "RGBA"
    assert sprite_module._to_pil_rgba(bgra).mode == "RGBA"


def test_sprite_extraction_quality_trim_empty_and_transparency(monkeypatch) -> None:
    image = Image.new("RGBA", (8, 8), (255, 0, 0, 255))
    assert extract_masked_sprite(image, [(0, 0), (1, 1)]).size == (1, 1)
    fast = extract_masked_sprite(
        image, [(-2, -2), (7, 0), (0, 7)], antialias="fast", trim=False
    )
    assert fast.width > 1 and fast.height > 1
    plain = extract_masked_sprite(
        image, [(0, 0), (7, 0), (0, 7)], antialias="none", trim=True
    )
    assert plain.getbbox() is not None

    monkeypatch.setattr(sprite_module, "_HAS_CV2", False)
    high = extract_masked_sprite(image, [(0, 0), (7, 0), (0, 7)], antialias="high")
    assert high.getbbox() is not None
    transparent = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    assert extract_masked_sprite(transparent, [(0, 0), (7, 0), (0, 7)]).size == (1, 1)


def test_export_sprite_validation_fallback_and_failures(tmp_path, monkeypatch) -> None:
    with pytest.raises(ValueError, match="loaded image"):
        export_sprite("A", SimpleNamespace(image=None, objects={}), "")
    scene = SimpleNamespace(
        image=Image.new("RGBA", (8, 8), (255, 0, 0, 255)), objects={}
    )
    with pytest.raises(ValueError, match="not found"):
        export_sprite("A", scene, "")

    obj = SimpleNamespace(polygon=[(0, 0), (7, 0), (0, 7)], beziers=BEZIERS)
    scene.objects["A"] = obj
    sprite = export_sprite("A", scene, "")
    assert sprite.getbbox() is not None
    obj.beziers = None
    obj.polygon = []
    with pytest.raises(ValueError, match="invalid polygon"):
        export_sprite("A", scene, "")

    obj.polygon = [(0, 0), (7, 0), (0, 7)]
    monkeypatch.setattr(
        sprite_module,
        "extract_masked_sprite",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("extract failed")),
    )
    with pytest.raises(RuntimeError, match="extract failed"):
        export_sprite("A", scene, "")

    monkeypatch.setattr(
        sprite_module,
        "extract_masked_sprite",
        lambda *args, **kwargs: Image.new("RGBA", (2, 2)),
    )
    monkeypatch.setattr(
        sprite_module,
        "save_sprite",
        lambda *args: (_ for _ in ()).throw(OSError("save failed")),
    )
    with pytest.raises(OSError, match="Save failed"):
        export_sprite("A", scene, str(tmp_path / "sprite.png"))


def test_save_sprite_directory_extensionless_and_cleanup(tmp_path, monkeypatch) -> None:
    sprite = Image.new("RGBA", (2, 2), (255, 0, 0, 255))
    nested = tmp_path / "nested" / "sprite.png"
    save_sprite(sprite, str(nested))
    assert nested.is_file()
    extensionless = tmp_path / "sprite"
    save_sprite(sprite, str(extensionless))
    assert extensionless.is_file()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sprite_module.os,
        "replace",
        lambda *args: (_ for _ in ()).throw(OSError("replace failed")),
    )
    with pytest.raises(OSError, match="replace failed"):
        save_sprite(sprite, "failed.png")
    assert list(tmp_path.glob("tmp_sprite_*")) == []
