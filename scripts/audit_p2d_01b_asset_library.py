"""Capture and audit the P2D-01B asset library in the real Qt window."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402
from PySide6.QtCore import QPoint, QSize  # noqa: E402
from PySide6.QtGui import QColor, QImage  # noqa: E402
from PySide6.QtWidgets import QApplication, QWidget  # noqa: E402

from scripts.audit_visual_artifacts import run_audit  # noqa: E402
from src.core.commands import CommandManager  # noqa: E402
from src.core.scenario_authoring import ScenarioAuthoringState  # noqa: E402
from src.core.scene_asset_library import sha256_file  # noqa: E402
from src.models.scene import Scene  # noqa: E402
from src.persistence.project_schema import Point3Record, PointRecord  # noqa: E402
from src.persistence.scenario_schema import ProjectReferenceRecord  # noqa: E402
from src.persistence.scene_authoring_io import save_scene_authoring  # noqa: E402
from src.persistence.scene_authoring_schema import (  # noqa: E402
    AssetReferenceRecord,
    SceneAuthoringDocumentV2,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneObjectAuthoringRecord,
    SceneTransformRecord,
)
from src.persistence.scene_authoring_schema import (  # noqa: E402
    SceneAuthoringDocumentV1,
    upgrade_scene_authoring_document,
)
from src.ui.scenario_editor_window import ScenarioEditorWindow  # noqa: E402
from src.ui.theme_qss import QSS  # noqa: E402

RESOLUTIONS = {
    "1280x720": (1280, 720),
    "1366x768": (1366, 768),
    "1920x1080": (1920, 1080),
}


def _digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _git_state() -> dict[str, Any]:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    return {
        "source_commit": head,
        "worktree_clean_at_capture_start": not bool(status.strip()),
    }


def _widget_record(widget: QWidget, root: QWidget) -> dict[str, Any]:
    rect = widget.geometry()
    top_left = widget.mapTo(root, QPoint(0, 0))
    return {
        "class": widget.metaObject().className(),
        "object_name": widget.objectName(),
        "visible": widget.isVisible(),
        "enabled": widget.isEnabled(),
        "geometry": [rect.x(), rect.y(), rect.width(), rect.height()],
        "root_geometry": [top_left.x(), top_left.y(), widget.width(), widget.height()],
    }


def _scenario_geometry(window: ScenarioEditorWindow) -> dict[str, Any]:
    widgets: dict[str, QWidget] = {
        "scenario_editor_toolbar": window.toolbar,
        "scenario_editor_splitter": window.centralWidget(),
        "professional_viewport_pages": window.professional_pages,
        "scenario_right_pages": window.right_pages,
    }
    if window.professional_viewport is not None:
        widgets["professional_scene_viewport"] = window.professional_viewport
    if window.professional_inspector_scroll is not None:
        widgets["professional_inspector_scroll"] = window.professional_inspector_scroll
    if window.professional_inspector is not None:
        widgets["professional_scene_inspector"] = window.professional_inspector
    records = {name: _widget_record(widget, window) for name, widget in widgets.items()}
    records["professional_inspector_scroll"]["scroll_area"] = True
    records["professional_scene_inspector"].update(
        {"scrollable": True, "scroll_area_parent": "professional_inspector_scroll"}
    )
    asset_library = window.asset_library
    if asset_library is not None:
        records["professional_scene_asset_library"] = _widget_record(
            asset_library, window
        )
        for name, widget in (
            ("scene_asset_library_list", asset_library.asset_list),
            ("scene_asset_library_diagnostics", asset_library.diagnostics_label),
            ("scene_asset_import_button", asset_library.import_button),
            ("scene_asset_relink_button", asset_library.relink_button),
            ("scene_asset_replace_button", asset_library.replace_button),
            ("scene_asset_refresh_button", asset_library.refresh_button),
        ):
            records[name] = _widget_record(widget, window)
    return {
        "profile": "professional_scene_editor",
        "professional_editor": records,
    }


def _write_image(path: Path, size: tuple[int, int], color: str) -> None:
    image = QImage(*size, QImage.Format.Format_RGBA8888)
    image.fill(QColor(color))
    path.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(path)):
        raise RuntimeError(f"could not create fixture image {path.name}")


def _fixture(root: Path) -> tuple[Path, Path, Scene]:
    project = root / "fixture.ndtproj"
    project.write_bytes(b"p2d-01b-asset-library-fixture-v1\n")
    assets = root / "assets" / "scene"
    hero_path = assets / "hero.png"
    _write_image(hero_path, (180, 120), "#d4a36a")
    hero = AssetReferenceRecord(
        id="hero", path="assets/scene/hero.png", sha256=sha256_file(hero_path)
    )
    missing = AssetReferenceRecord(
        id="missing", path="assets/scene/missing.png", sha256="b" * 64
    )
    layer = SceneLayerAuthoringRecord(id="background", name="Background")

    def transform(x: float, y: float) -> SceneTransformRecord:
        return SceneTransformRecord(
            position=Point3Record(x=x, y=y, z=0.0),
            rotation=Point3Record(x=0.0, y=0.0, z=0.0),
            scale=Point3Record(x=1.0, y=1.0, z=1.0),
            pivot=PointRecord(x=0.5, y=0.5),
        )

    document = SceneAuthoringDocumentV2(
        metadata=SceneAuthoringMetadataRecord(
            name="P2D-01B Fixture", generator="NeoEng-D-Trace", app_version="0.2.0"
        ),
        project=ProjectReferenceRecord(sha256="a" * 64),
        assets=[hero, missing],
        layers=[layer],
        objects=[
            SceneObjectAuthoringRecord(
                id="hero_object",
                asset_id="hero",
                layer_id="background",
                transform=transform(80, 80),
            ),
            SceneObjectAuthoringRecord(
                id="missing_object",
                asset_id="missing",
                layer_id="background",
                transform=transform(320, 80),
            ),
        ],
        groups=[],
    )
    save_scene_authoring(document, project.with_suffix(".ndtscene.json"))
    scene = Scene()
    scene.cmd = CommandManager(max_history=20)
    scene.image_path = str(hero_path)
    scene.add_object("hero_object", [(0, 0), (180, 0), (180, 120), (0, 120)])
    scene.add_object("missing_object", [(240, 0), (400, 0), (400, 120), (240, 120)])
    return project, hero_path, scene


def _capture(
    window: ScenarioEditorWindow, path: Path, size: tuple[int, int]
) -> dict[str, Any]:
    window.resize(QSize(*size))
    window.show()
    QApplication.processEvents()
    if (window.width(), window.height()) != size:
        raise RuntimeError(f"Qt did not apply requested size {size}")
    if not window.grab().save(str(path), "PNG"):
        raise RuntimeError(f"could not save {path.name}")
    with Image.open(path) as image:
        image.verify()
        actual = [image.width, image.height]
    return {
        "requested_size": list(size),
        "actual_window_size": [window.width(), window.height()],
        "actual_capture_size": actual,
        "files": {path.name: _digest(path)},
        "widget_geometry": _scenario_geometry(window),
    }


def capture(output: Path) -> dict[str, Any]:
    output = output.resolve()
    capture_dir = output / "captures"
    capture_dir.mkdir(parents=True, exist_ok=True)
    state = _git_state()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    captures: dict[str, Any] = {}
    lifecycle: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="neoeng-p2d-01b-") as temp:
        project, hero_path, scene = _fixture(Path(temp))
        authoring = ScenarioAuthoringState(scene)
        authoring.bind_project(project)
        window = ScenarioEditorWindow(authoring, scene, language="en")
        try:
            library = window.asset_library
            session = window.professional_session
            viewport = window.professional_viewport
            if library is None or session is None or viewport is None:
                raise RuntimeError("professional asset library was not created")
            library._select_id("hero")
            lifecycle["ready"] = {
                "state": library.inspections["hero"].state,
                "relink_enabled": library.relink_button.isEnabled(),
                "replace_enabled": library.replace_button.isEnabled(),
                "objects_using_asset": 1,
            }
            for label, size in RESOLUTIONS.items():
                captures[f"ready_{label}"] = _capture(
                    window, capture_dir / f"{label}_scenario_authoring.png", size
                )
            library._select_id("missing")
            lifecycle["missing"] = {
                "state": library.inspections["missing"].state,
                "relink_enabled": library.relink_button.isEnabled(),
                "replace_enabled": library.replace_button.isEnabled(),
                "diagnostic_present": bool(library.inspections["missing"].issue),
            }
            captures["missing_1366x768"] = _capture(
                window,
                capture_dir / "1366x768_scenario_overlays.png",
                RESOLUTIONS["1366x768"],
            )
            repaired = Path(temp) / "external" / "missing-repaired.png"
            _write_image(repaired, (96, 64), "#57c7a5")
            before_objects = session.document.objects
            if not library.relink_asset_from_path(repaired):
                raise RuntimeError("relink operation was not applied")
            if session.document.objects != before_objects:
                raise RuntimeError("relink changed authored objects")
            lifecycle["after_relink"] = {
                "state": library.inspections["missing"].state,
                "same_asset_id": session.document.assets[1].id == "missing",
                "objects_preserved": session.document.objects == before_objects,
            }
            library._select_id("hero")
            replacement = Path(temp) / "external" / "hero-replaced.png"
            _write_image(replacement, (220, 144), "#ff8c32")
            before_objects = session.document.objects
            if not library.replace_asset_from_path(replacement):
                raise RuntimeError("replace operation was not applied")
            lifecycle["after_replace"] = {
                "same_asset_id": session.document.assets[0].id == "hero",
                "objects_preserved": session.document.objects == before_objects,
                "rendered_size": [
                    viewport._items["hero_object"]._pixmap.width(),
                    viewport._items["hero_object"]._pixmap.height(),
                ],
            }
        finally:
            window.close()
    manifest = {
        "schema_version": 2,
        "generator": "scripts/audit_p2d_01b_asset_library.py",
        **state,
        "privacy": {"absolute_paths_persisted": False, "fixture_is_temporary": True},
        "lifecycle": lifecycle,
        "captures": captures,
    }
    (capture_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    report = run_audit(capture_dir, output / "audited")
    report["source_commit"] = state["source_commit"]
    report["lifecycle"] = lifecycle
    (output / "p2d-01b-capture-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = capture(args.output)
    print(
        json.dumps(
            {"status": report["status"], "finding_count": report["finding_count"]}
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
