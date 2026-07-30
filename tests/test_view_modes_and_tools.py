# tests/test_view_modes_and_tools.py
import sys

import pytest
from PySide6.QtWidgets import QApplication

from src.models.scene import Scene
from src.ui.canvas_view import CanvasView


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_canvas_view_modes(qt_app):
    scene = Scene()
    canvas = CanvasView(scene)
    # Testa alternância entre modos de visualização
    for mode in [
        canvas.VIEW_LIT,
        canvas.VIEW_XRAY_1,
        canvas.VIEW_XRAY_2,
        canvas.VIEW_XRAY_3,
        canvas.VIEW_COLLISION,
    ]:
        canvas.set_view_mode(mode)
        assert canvas._view_mode == mode
        # Simula update/render (não testa visual, mas garante que não quebra)
        canvas.update()


def test_canvas_tool_pen(qt_app):
    scene = Scene()
    canvas = CanvasView(scene)
    # Simula ferramenta de desenho manual (pen_tool)
    # Adiciona pontos manualmente
    canvas._current_polygon = [(10, 10), (50, 10), (50, 50), (10, 50)]
    # Simula finalização do polígono
    scene.set_auto_repair(True)
    canvas.model.add_polygon(list(canvas._current_polygon))
    assert len(scene.objects) == 1
    oid = list(scene.objects.keys())[0]
    assert len(scene.objects[oid].polygon) >= 3


def test_canvas_tool_selection(qt_app):
    scene = Scene()
    canvas = CanvasView(scene)
    # Adiciona dois polígonos
    scene.set_auto_repair(True)
    scene.add_object("poly1", [(0, 0), (40, 0), (40, 40), (0, 40)])
    scene.add_object("poly2", [(100, 100), (140, 100), (140, 140), (100, 140)])
    # Simula seleção
    canvas.model.select_object("poly2")
    assert canvas.model.selected_id == "poly2"
