from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

import src.launcher as launcher
from src.models.scene import Scene

ROOT = Path(__file__).resolve().parents[1]


def _args(*values):
    return launcher.build_parser().parse_args(list(values))


def _project(path: Path) -> str:
    scene = Scene()
    scene.add_object("box", [(0, 0), (20, 0), (20, 20), (0, 20)])
    scene.save_project(str(path))
    return str(path)


def _subprocess(*values):
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    return subprocess.run(
        [sys.executable, str(ROOT / "app.py"), *values],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )


def _module_subprocess(*values):
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    return subprocess.run(
        [sys.executable, "-m", "src.launcher", *values],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )


@pytest.mark.parametrize(
    "values",
    [
        ("--headless",),
        ("--image", "image.png"),
        ("--project", "project.ndtproj"),
        ("--export-scene-gltf", "scene.glb"),
        ("--export-object-gltf", "object.glb"),
        ("--object-id", "box"),
        ("--export-json", "scene.json"),
        ("--export-profile", "unity"),
        ("--save-project", "saved.ndtproj"),
    ],
)
def test_every_headless_field_is_dispatched(values):
    assert launcher._headless_requested(_args(*values)) is True


def test_gui_only_arguments_do_not_trigger_headless():
    assert launcher._headless_requested(_args()) is False
    assert (
        launcher._headless_requested(_args("--validation-log", "events.jsonl")) is False
    )


@pytest.mark.parametrize(
    ("values", "message"),
    [
        (("--headless",), "requires an input or output operation"),
        (("--object-id", "box"), "requires --export-object-gltf"),
        (("--export-object-gltf", "box.glb"), "requires --object-id"),
        (("--export-profile", "unity"), "requires --export-json"),
        (
            ("--headless", "--validation-log", "events.jsonl"),
            "available only in GUI mode",
        ),
    ],
)
def test_invalid_headless_contracts_return_one_and_stderr(values, message, capsys):
    assert launcher.run_headless(_args(*values)) == launcher.EXIT_FAILURE
    assert message in capsys.readouterr().err


def test_parser_rejects_mutually_exclusive_sources_and_unknown_flags(capsys):
    with pytest.raises(SystemExit) as conflict:
        _args("--image", "one.png", "--project", "one.ndtproj")
    assert conflict.value.code == 2
    assert "not allowed with argument" in capsys.readouterr().err

    with pytest.raises(SystemExit) as unknown:
        _args("--unknown")
    assert unknown.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("flag", "name", "message"),
    [
        ("--image", "missing.png", "Image file not found"),
        ("--project", "missing.ndtproj", "Project file not found"),
    ],
)
def test_missing_inputs_return_one_without_traceback(
    tmp_path, flag, name, message, capsys
):
    missing = tmp_path / name
    assert launcher.run_headless(_args(flag, str(missing))) == launcher.EXIT_FAILURE
    captured = capsys.readouterr()
    assert message in captured.err
    assert "Traceback" not in captured.err


def test_invalid_image_and_project_return_controlled_failure(tmp_path, capsys):
    image = tmp_path / "broken.png"
    image.write_bytes(b"not an image")
    assert launcher.run_headless(_args("--image", str(image))) == 1
    assert "Failed to load image" in capsys.readouterr().err

    project = tmp_path / "broken.ndtproj"
    project.write_text("{}", encoding="utf-8")
    assert launcher.run_headless(_args("--project", str(project))) == 1
    assert "Failed to load project" in capsys.readouterr().err


def test_real_image_load_is_a_successful_headless_operation(tmp_path, capsys):
    path = tmp_path / "image.png"
    Image.new("RGBA", (4, 3), (10, 20, 30, 255)).save(path)

    assert launcher.run_headless(_args("--image", str(path))) == 0
    assert "completed successfully" in capsys.readouterr().out


def test_real_project_combines_json_save_and_gltf_outputs(tmp_path, capsys):
    source = _project(tmp_path / "source.ndtproj")
    metadata = tmp_path / "metadata.json"
    saved = tmp_path / "saved.ndtproj"
    scene_glb = tmp_path / "scene.glb"
    object_glb = tmp_path / "object.glb"

    values = (
        "--project",
        source,
        "--export-json",
        str(metadata),
        "--save-project",
        str(saved),
        "--export-scene-gltf",
        str(scene_glb),
        "--export-object-gltf",
        str(object_glb),
        "--object-id",
        "box",
    )
    assert launcher.run_headless(_args(*values)) == 0

    assert json.loads(metadata.read_text(encoding="utf-8"))["sprites"][0]["id"] == "box"
    assert saved.read_text(encoding="utf-8").startswith("{")
    assert scene_glb.read_bytes()[:4] == b"glTF"
    assert object_glb.read_bytes()[:4] == b"glTF"
    assert "completed successfully" in capsys.readouterr().out


def test_real_project_exports_engine_json_profiles(tmp_path, capsys):
    source = _project(tmp_path / "source.ndtproj")
    for profile, schema in (
        ("godot", "neoeng-d-trace-godot-sprite"),
        ("unity", "neoeng-d-trace-unity-sprite"),
    ):
        metadata = tmp_path / f"{profile}.json"
        assert (
            launcher.run_headless(
                _args(
                    "--project",
                    source,
                    "--export-json",
                    str(metadata),
                    "--export-profile",
                    profile,
                )
            )
            == 0
        )
        payload = json.loads(metadata.read_text(encoding="utf-8"))
        assert payload["profile"] == profile
        assert payload["sprites"][0]["schema"] == schema
    assert "completed successfully" in capsys.readouterr().out


def test_unknown_object_and_exporter_false_are_failures(tmp_path, monkeypatch, capsys):
    source = _project(tmp_path / "source.ndtproj")
    output = tmp_path / "object.glb"
    args = _args(
        "--project",
        source,
        "--export-object-gltf",
        str(output),
        "--object-id",
        "missing",
    )
    assert launcher.run_headless(args) == 1
    assert not output.exists()
    assert "Failed to export object" in capsys.readouterr().err

    monkeypatch.setattr(
        "src.exporters.gltf_exporter.export_scene_to_gltf", lambda *_: False
    )
    assert launcher.run_headless(_args("--export-scene-gltf", str(output))) == 1
    assert "Failed to export scene" in capsys.readouterr().err


def test_json_failure_preserves_existing_destination(tmp_path, monkeypatch, capsys):
    destination = tmp_path / "metadata.json"
    destination.write_text("preserved", encoding="utf-8")

    def fail_replace(*_):
        raise OSError("replace blocked")

    monkeypatch.setattr("src.exporters.json_exporter.os.replace", fail_replace)
    assert launcher.run_headless(_args("--export-json", str(destination))) == 1
    assert destination.read_text(encoding="utf-8") == "preserved"
    assert list(tmp_path.glob("*.json")) == [destination]
    assert "Failed to export JSON" in capsys.readouterr().err


def test_save_and_unexpected_setup_failures_return_one(tmp_path, monkeypatch, capsys):
    def fail_save(self, path):
        raise OSError("disk full")

    monkeypatch.setattr(Scene, "save_project", fail_save)
    output = tmp_path / "saved.ndtproj"
    assert launcher.run_headless(_args("--save-project", str(output))) == 1
    assert "Failed to save project" in capsys.readouterr().err

    monkeypatch.setattr(
        launcher,
        "ConfigManager",
        lambda *_: (_ for _ in ()).throw(RuntimeError("setup failed")),
    )
    assert launcher.run_headless(_args("--export-json", str(tmp_path / "x.json"))) == 1
    assert "Headless processing failed" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("values", "expected_code", "stream", "marker"),
    [
        (("--help",), 0, "stdout", "--export-object-gltf"),
        (("--version",), 0, "stdout", "0.3.0"),
        (("--unknown",), 2, "stderr", "unrecognized arguments"),
        (("--headless",), 1, "stderr", "requires an input or output operation"),
        (
            ("--export-object-gltf", "object.glb"),
            1,
            "stderr",
            "requires --object-id",
        ),
    ],
)
def test_real_subprocess_argument_output_exit_matrix(
    values, expected_code, stream, marker
):
    result = _subprocess(*values)
    assert result.returncode == expected_code
    assert marker in getattr(result, stream)
    assert "Traceback" not in result.stderr


def test_module_entrypoint_propagates_operational_failure():
    result = _module_subprocess("--headless")

    assert result.returncode == 1
    assert "requires an input or output operation" in result.stderr
    assert "Traceback" not in result.stderr


def test_real_subprocess_creates_reopenable_outputs(tmp_path):
    source = _project(tmp_path / "source.ndtproj")
    metadata = tmp_path / "metadata.json"
    saved = tmp_path / "saved.ndtproj"

    result = _subprocess(
        "--project",
        source,
        "--export-json",
        str(metadata),
        "--save-project",
        str(saved),
    )

    assert result.returncode == 0
    assert "completed successfully" in result.stdout
    assert json.loads(metadata.read_text(encoding="utf-8"))["sprites"]
    reopened = Scene()
    reopened.load_project(str(saved))
    assert "box" in reopened.objects


class _SignalProbe:
    def __init__(self):
        self.callback = None

    def connect(self, callback):
        self.callback = callback


class _ApplicationProbe:
    instance = None

    def __init__(self, args):
        self.aboutToQuit = _SignalProbe()
        _ApplicationProbe.instance = self

    def setFont(self, font):
        self.font = font

    def setStyleSheet(self, stylesheet):
        self.stylesheet = stylesheet

    def exec(self):
        self.aboutToQuit.callback()
        return 0


class _WindowProbe:
    def __init__(self, scene, config):
        self._last_folder = None
        self._current_tool = "polygonal_lasso"
        self.selected_tool = None

    def show(self):
        self.visible = True

    def isVisible(self):
        return self.visible

    def set_last_folder(self, folder):
        self._last_folder = folder

    def select_tool(self, tool):
        self.selected_tool = tool
        self._current_tool = tool

    def restoreGeometry(self, data):
        return data == b"geometry"

    def saveGeometry(self):
        return SimpleNamespace(data=lambda: b"saved-geometry")


class _ConfigProbe:
    def __init__(self, folder):
        self.values = {
            "last_folder": str(folder),
            "tool": "rect_selection",
            "window_geometry": base64.b64encode(b"geometry").decode("ascii"),
        }
        self.saved = False

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value

    def save(self):
        self.saved = True


def test_main_gui_dispatch_restores_and_saves_state(tmp_path, monkeypatch):
    config = _ConfigProbe(tmp_path)
    events = []
    monkeypatch.setattr(
        sys,
        "argv",
        ["neoeng-d-trace", "--validation-log", str(tmp_path / "events.jsonl")],
    )
    monkeypatch.setattr(launcher, "ConfigManager", lambda *_: config)
    monkeypatch.setattr("PySide6.QtWidgets.QApplication", _ApplicationProbe)
    monkeypatch.setattr("src.ui.main_window.MainWindow", _WindowProbe)
    monkeypatch.setattr(
        launcher,
        "start_validation_session",
        lambda path: events.append(("start", path)),
    )
    monkeypatch.setattr(
        launcher,
        "record_validation_event",
        lambda name, status, **data: events.append((name, status, data)),
    )
    monkeypatch.setattr(
        launcher,
        "stop_validation_session",
        lambda **data: events.append(("stop", data)),
    )

    assert launcher.main() == 0
    assert config.saved is True
    assert config.values["tool"] == "rect_selection"
    assert base64.b64decode(config.values["window_geometry"]) == b"saved-geometry"
    assert any(event[0] == "application.opened" for event in events)
    assert any(event[0] == "application.state.saved" for event in events)
    assert events[-1][0] == "stop"
