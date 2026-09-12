"""Qt-level E09 contour workflow coverage."""

from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
)
from src.ui.vector_contour_panel import VectorContourPanel


@pytest.fixture
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def _fixture(tmp_path: Path) -> tuple[SceneAuthoringSession, Path]:
    project = tmp_path / "project"
    asset_path = project / "assets" / "scene" / "subject.png"
    asset_path.parent.mkdir(parents=True)
    image = np.zeros((96, 128, 4), dtype=np.uint8)
    image[18:78, 24:104, 3] = 255
    ok, encoded = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA))
    assert ok
    asset_path.write_bytes(encoded.tobytes())
    document = SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="E09 UI", generator="NeoEng-D-Trace", app_version="0.3.0"
        ),
        project=ProjectReferenceRecord(sha256="a" * 64),
        assets=[
            AssetReferenceRecord(
                id="subject",
                path="assets/scene/subject.png",
                sha256=hashlib.sha256(asset_path.read_bytes()).hexdigest(),
            )
        ],
        layers=[SceneLayerAuthoringRecord(id="foreground", name="Foreground")],
        objects=[],
        groups=[],
    )
    return SceneAuthoringSession(SceneAuthoringModel(document)), project


def test_native_contour_flow_detect_edit_undo_redo_cancel_and_create(
    qapp: QApplication, tmp_path: Path
) -> None:
    session, project = _fixture(tmp_path)
    panel = VectorContourPanel(session, project)
    panel.update_language("pt")
    panel.set_selected_asset("subject")

    assert panel.detect_selected()
    assert "source" in panel.state_label.text() or "origem" in panel.state_label.text()
    panel.vertex_index.setValue(1)
    panel.vertex_x.setValue(110.0)
    panel.vertex_y.setValue(20.0)
    assert panel.apply_vertex()
    assert panel.undo()
    assert panel.redo()
    assert panel.create_object()
    assert session.document.objects[0].vector_geometry is not None
    assert session.document.objects[0].vector_geometry.polygon[1].x == 110.0

    assert panel.detect_selected()
    assert panel.cancel()
    assert panel._editing is not None and panel._editing.cancelled
    assert panel.title.text() == "Contorno vetorial"


def test_native_contour_flow_reports_missing_asset(
    qapp: QApplication, tmp_path: Path
) -> None:
    session, project = _fixture(tmp_path)
    panel = VectorContourPanel(session, project)
    panel.set_selected_asset("missing")
    assert not panel.detect_selected()
    assert "asset" in panel.diagnostics_label.text().lower()
