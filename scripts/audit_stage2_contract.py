"""Audit the Stage 2 project icon-library contract.

The audit treats later-stage-only glyphs such as mask and collision overlay as
forward-compatible extensions.  The normative Stage 2 catalog must nevertheless
own every icon listed by the implementation plan, including undo, redo and snap.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QApplication

from src.ui.icon_library import ICON_SPECS, icon_for

REQUIRED_KEYS = {
    "selection",
    "lasso",
    "polygon",
    "magnetic",
    "pen",
    "rect",
    "ellipse",
    "polygon_edit",
    "collision_brush",
    "move",
    "zoom",
    "fit",
    "focus",
    "open",
    "save",
    "export",
    "undo",
    "redo",
    "visible",
    "lock",
    "add",
    "remove",
    "up",
    "down",
    "lit",
    "xray_1",
    "xray_2",
    "xray_3",
    "gizmo",
    "snap",
    "grid",
    "scenario",
    "validation",
}
REQUIRED_SIZES = (16, 20, 24)
STAGE2_DUPLICATE_KEYS = {"undo", "redo", "snap"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def _duplicate_stage2_svg_keys(repo_root: Path) -> list[str]:
    source = (repo_root / "src/ui/top_toolbar.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    keys: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_ACTION_ICON_BODIES"
            for target in node.targets
        ):
            if isinstance(node.value, ast.Dict):
                for key in node.value.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        keys.add(key.value)
    return sorted(keys & STAGE2_DUPLICATE_KEYS)


def _emoji_codepoints(text: str) -> list[str]:
    return [f"U+{ord(char):04X}" for char in text if ord(char) > 0xFFFF]


def _runtime_contract() -> dict[str, Any]:
    from scripts.audit_ui_capture import AuditConfig
    from src.models.scene import Scene
    from src.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow(Scene(), AuditConfig())
    app.processEvents()
    action_names = (
        "open_project_action",
        "open_image_action",
        "save_project_action",
        "save_project_as_action",
        "act_export",
        "undo_action",
        "redo_action",
        "act_snap",
    )
    failures: list[str] = []
    records: dict[str, Any] = {}
    for name in action_names:
        action = getattr(window, name)
        icon = action.icon()
        record = {
            "text": action.text(),
            "tooltip": action.toolTip(),
            "accessible_name": action.property("accessibleName"),
            "icon_key": action.property("iconKey"),
            "icon_null": icon.isNull(),
            "icon_fallback": bool(action.property("iconFallback")),
            "available_sizes": [[size.width(), size.height()] for size in icon.availableSizes()],
        }
        records[name] = record
        for field in ("text", "tooltip", "accessible_name", "icon_key"):
            if not record[field]:
                failures.append(f"{name}: missing {field}")
        if record["icon_null"] or record["icon_fallback"]:
            failures.append(f"{name}: icon unavailable or fallback active")
    window.close()
    return {"status": "PASS" if not failures else "FAIL", "failures": failures, "actions": records}


def run(repo_root: Path, historical_report: Path | None = None) -> dict[str, Any]:
    app = QApplication.instance() or QApplication(sys.argv)
    missing_keys = sorted(REQUIRED_KEYS - set(ICON_SPECS))
    invalid_specs = [
        key
        for key in sorted(REQUIRED_KEYS & set(ICON_SPECS))
        if not ICON_SPECS[key].svg_body
        or "assets/" in ICON_SPECS[key].svg_body
        or "<image" in ICON_SPECS[key].svg_body.lower()
        or "<text" in ICON_SPECS[key].svg_body.lower()
    ]
    size_records: dict[str, list[list[int]]] = {}
    size_failures: list[str] = []
    for key in sorted(REQUIRED_KEYS & set(ICON_SPECS)):
        icon = icon_for(key)
        sizes = sorted([[size.width(), size.height()] for size in icon.availableSizes()])
        size_records[key] = sizes
        for required in REQUIRED_SIZES:
            if [required, required] not in sizes:
                size_failures.append(f"{key}: missing {required}px raster")
    library_source = (repo_root / "src/ui/icon_library.py").read_text(encoding="utf-8")
    emoji_codepoints = _emoji_codepoints(library_source)
    duplicate_keys = _duplicate_stage2_svg_keys(repo_root)
    runtime = _runtime_contract()
    checks = {
        "required_catalog_complete": not missing_keys,
        "required_specs_are_embedded_vectors": not invalid_specs,
        "required_sizes_16_20_24": not size_failures,
        "no_functional_emoji_in_library": not emoji_codepoints,
        "no_stage2_duplicate_svg_owners": not duplicate_keys,
        "runtime_actions_have_accessible_icons": runtime["status"] == "PASS",
    }
    historical: dict[str, Any]
    if historical_report and historical_report.exists():
        old = json.loads(historical_report.read_text(encoding="utf-8"))
        historical = {
            "status": old.get("status", "UNKNOWN"),
            "classification": "HISTORICAL_ONLY",
            "source": historical_report.as_posix(),
            "sha256": _sha256(historical_report),
            "interpretation": "Retained as a previous DPI/icon audit reference; current contract is evaluated independently.",
        }
    else:
        historical = {
            "status": "NOT_AVAILABLE",
            "classification": "REVIEW_REQUIRED",
            "source": None,
            "sha256": None,
            "interpretation": "No prior report supplied.",
        }
    current_pass = all(checks.values())
    return {
        "schema": "neoeng.stage2-contract-audit",
        "schema_version": 1,
        "stage": 2,
        "stage_name": "Biblioteca de ícones própria",
        "source": {
            "commit": _git("rev-parse", "HEAD"),
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "worktree_clean_tracked": not bool(_git("status", "--porcelain", "--untracked-files=no")),
        },
        "environment": {"platform": platform.platform(), "python": sys.version},
        "current_contract_result": "PASS" if current_pass else "FAIL",
        "historical_result": historical,
        "consolidated_decision": "PASS_WITH_HISTORICAL_EVOLUTION" if current_pass else "REVIEW_REQUIRED",
        "checks": checks,
        "evidence": {
            "required_keys": sorted(REQUIRED_KEYS),
            "catalog_keys": sorted(ICON_SPECS),
            "catalog_size": len(ICON_SPECS),
            "missing_keys": missing_keys,
            "invalid_specs": invalid_specs,
            "size_records": size_records,
            "size_failures": size_failures,
            "emoji_codepoints": emoji_codepoints,
            "duplicate_stage2_svg_keys": duplicate_keys,
            "runtime": runtime,
        },
        "limitations": [
            "Mask and collision overlay glyphs remain later-stage-specific extensions and are not used to inflate the Stage 2 normative catalog.",
            "DPI rendering of the full production window is covered by the separate four-scale matrix auditor.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--historical-report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.repo_root.resolve(), args.historical_report.resolve() if args.historical_report else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"current_contract_result": report["current_contract_result"], "consolidated_decision": report["consolidated_decision"]}, sort_keys=True))
    return 0 if report["current_contract_result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
