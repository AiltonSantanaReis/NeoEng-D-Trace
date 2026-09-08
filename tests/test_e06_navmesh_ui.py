from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.navmesh_panel import NavMeshPanel


@pytest.fixture
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_navmesh_panel_runs_surface_flow_and_persists(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = NavMeshPanel(tmp_path)
    panel.add_region()
    panel.add_obstacle()
    panel.bake_source()
    panel.save_document()
    assert panel.document_path.is_file()
    panel.open_document()
    assert len(panel.source.regions) == 1
    assert len(panel.source.obstacles) == 1
    assert panel.bake is None


def test_navmesh_panel_marks_bake_obsolete_after_source_edit(
    qt_app: QApplication, tmp_path: Path
) -> None:
    panel = NavMeshPanel(tmp_path)
    panel.add_region()
    panel.bake_source()
    panel.add_obstacle()
    assert panel.bake is not None
    assert panel.bake.is_obsolete(panel.source)
