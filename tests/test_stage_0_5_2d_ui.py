import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import (
    QApplication,
    QLayout,
    QSizePolicy,
)

from src.models.scene import Scene
from src.ui.export_dialog import ExportDialog
from src.ui.side_panel import SidePanel


class _CanvasStub:
    def update(self):
        pass


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def test_side_panel_tracks_scene_selection_after_polygon_creation(qt_app):
    scene = Scene()
    panel = SidePanel(scene, _CanvasStub())

    object_id = scene.add_polygon([(0, 0), (20, 0), (20, 20), (0, 20)])
    qt_app.processEvents()

    assert scene.selected_id == object_id
    assert panel.list.currentItem() is not None
    assert panel.list.currentItem().text().replace(" [P]", "") == object_id

    scene.select_object(None)
    qt_app.processEvents()
    assert panel.list.currentItem() is None
    assert panel.list.selectedItems() == []
    panel.close()


def test_export_dialog_uses_compact_vertical_policies(qt_app):
    dialog = ExportDialog(Scene())

    assert dialog.layout().sizeConstraint() == QLayout.SizeConstraint.SetFixedSize
    assert dialog.group_2d.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Maximum
    assert dialog.group_3d.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Maximum

    for button in (
        dialog.btn_single,
        dialog.btn_batch,
        dialog.btn_atlas,
        dialog.btn_metadata_selected,
        dialog.btn_gltf_scene,
        dialog.btn_gltf_object,
        dialog.btn_close,
    ):
        assert button.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Fixed

    assert dialog.group_2d.layout().spacing() == 8
    assert dialog.group_3d.layout().spacing() == 8
    dialog.close()
