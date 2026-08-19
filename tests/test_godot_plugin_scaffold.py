from __future__ import annotations

import configparser
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "integrations" / "godot"
ADDON_ROOT = PLUGIN_ROOT / "addons" / "neoeng_d_trace"


def test_godot_addon_is_source_only_and_has_stable_identity():
    config = configparser.ConfigParser()
    config.read(ADDON_ROOT / "plugin.cfg", encoding="utf-8")

    assert config["plugin"]["name"].strip('"') == "NeoEng D-Trace"
    assert config["plugin"]["version"].strip('"') == "0.3.0"
    assert config["plugin"]["script"].strip('"') == "plugin.gd"
    assert (ADDON_ROOT / "plugin.gd").is_file()
    assert (ADDON_ROOT / "manifest_diagnostic.gd").is_file()
    assert (ADDON_ROOT / "import_generator.gd").is_file()
    assert (ADDON_ROOT / "scenario_importer.gd").is_file()
    assert (ADDON_ROOT / "README.md").is_file()
    plugin = (ADDON_ROOT / "plugin.gd").read_text(encoding="utf-8")
    assert "filesystem_changed" in plugin
    assert "NEOENG_GODOT_AUTO_SYNC=" in plugin
    assert not [
        path
        for path in PLUGIN_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".dll", ".exe", ".so", ".dylib"}
    ]


def test_godot_addon_package_is_deterministic_and_contains_only_sources(tmp_path):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    command = [sys.executable, "scripts/package_godot_plugin.py"]
    subprocess.run([*command, "--output", str(first)], cwd=ROOT, check=True)
    subprocess.run([*command, "--output", str(second)], cwd=ROOT, check=True)

    assert first.read_bytes() == second.read_bytes()
    with ZipFile(first) as archive:
        names = sorted(archive.namelist())
        assert names == [
            "neoeng-d-trace-godot/addons/neoeng_d_trace/README.md",
            "neoeng-d-trace-godot/addons/neoeng_d_trace/animation_collision_driver.gd",
            "neoeng-d-trace-godot/addons/neoeng_d_trace/import_generator.gd",
            "neoeng-d-trace-godot/addons/neoeng_d_trace/manifest_diagnostic.gd",
            "neoeng-d-trace-godot/addons/neoeng_d_trace/plugin.cfg",
            "neoeng-d-trace-godot/addons/neoeng_d_trace/plugin.gd",
            "neoeng-d-trace-godot/addons/neoeng_d_trace/scenario_importer.gd",
        ]
        assert all(
            Path(name).suffix.lower() in {".gd", ".cfg", ".md"} for name in names
        )
