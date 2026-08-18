"""Stage 1 characterization for the accepted scenario extension plan."""

from __future__ import annotations

import sys

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

from src.models.scene import Scene
from src.persistence.project_schema import (
    LayerRecord,
    Point3Record,
    PointRecord,
    ProjectDocumentV1,
    ProjectMetadataRecord,
    SceneObjectRecord,
    TransformRecord,
)
from src.ui.main_window import MainWindow


def _document_with_transform() -> ProjectDocumentV1:
    return ProjectDocumentV1(
        metadata=ProjectMetadataRecord(
            generator="NeoEng-D-Trace",
            app_version="0.2.0",
        ),
        layers=[
            LayerRecord(
                id="layer_default",
                name="Default",
                visible=True,
                locked=False,
            )
        ],
        objects=[
            SceneObjectRecord(
                id="object-1",
                layer_id="layer_default",
                polygon=[
                    PointRecord(x=0, y=0),
                    PointRecord(x=10, y=0),
                    PointRecord(x=0, y=10),
                ],
                transform=TransformRecord(
                    position=Point3Record(x=1.0, y=2.0, z=3.0),
                    rotation=Point3Record(x=0.0, y=0.0, z=45.0),
                    scale=Point3Record(x=1.0, y=1.0, z=1.0),
                    pivot=PointRecord(x=0.5, y=0.5),
                ),
            )
        ],
        groups=[],
    )


def test_stage1_preserves_schema_v1_and_object_depth_contract() -> None:
    document = _document_with_transform()

    assert document.format_id == "neoeng-d-trace-project"
    assert document.schema_version == 1
    assert document.objects[0].transform is not None
    assert document.objects[0].transform.position.z == 3.0
    assert document.model_dump()["objects"][0]["transform"]["position"]["z"] == 3.0


def test_stage1_characterizes_existing_main_window_actions_without_ctrl_k() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow(Scene(), {})
    try:
        action_texts = {
            action.text() for action in window.findChildren(QAction) if action.text()
        }
        assert {
            "Open Project...",
            "Open Image",
            "Save",
            "Save As...",
            "Exit",
            "Undo",
            "Redo",
            "Mask Viewer (Auto-Detect)",
            "Collision Overlay",
            "X-Ray 1",
            "X-Ray 2",
            "X-Ray 3",
        } <= action_texts
        assert all(
            action.shortcut().toString() != "Ctrl+K"
            for action in window.findChildren(QAction)
        )
    finally:
        window.close()
        app.processEvents()
