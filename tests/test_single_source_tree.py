from __future__ import annotations

import ast
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_only_one_runtime_source_tree_exists() -> None:
    assert (ROOT / "src").is_dir()
    assert not (ROOT / "neoeng_d_trace").exists()


def test_runtime_has_no_imports_from_removed_namespace() -> None:
    paths = [ROOT / "app.py", *sorted((ROOT / "src").rglob("*.py"))]
    violations: list[str] = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            elif isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            if any(name == "neoeng_d_trace" or name.startswith("neoeng_d_trace.") for name in names):
                violations.append(str(path.relative_to(ROOT)))
    assert violations == []


def test_distribution_and_console_entry_use_single_src_tree() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    poetry = data["tool"]["poetry"]
    assert poetry["name"] == "neoeng-d-trace"
    assert poetry["packages"] == [{"include": "src"}]
    assert poetry["scripts"]["neoeng-d-trace"] == "src.launcher:main"


def test_launcher_keeps_legacy_config_in_project_root() -> None:
    source = (ROOT / "src" / "launcher.py").read_text(encoding="utf-8")
    assert 'get_project_root() / "config.json"' in source
    assert 'os.path.dirname(__file__), "config.json"' not in source


def test_app_help_uses_neoeng_d_trace_identity() -> None:
    result = subprocess.run(
        [sys.executable, "app.py", "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    assert result.returncode == 0, result.stdout
    assert "NeoEng-D-Trace" in result.stdout
