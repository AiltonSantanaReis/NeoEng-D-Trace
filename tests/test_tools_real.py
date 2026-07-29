import sys

import pytest
from PySide6.QtWidgets import QApplication

from src.models.scene import Scene
from src.ui.canvas_view import CanvasView


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_pen_tool_real(qt_app):
    scene = Scene()
    canvas = CanvasView(scene)
    # Simula desenho manual (pen_tool)
    canvas._current_polygon = [(10, 10), (50, 10), (50, 50), (10, 50)]
    scene.set_auto_repair(True)
    canvas.model.add_polygon(list(canvas._current_polygon))
    assert len(scene.objects) == 1
    oid = list(scene.objects.keys())[0]
    assert len(scene.objects[oid].polygon) == 4


def test_lasso_tool_real(qt_app):
    scene = Scene()
    canvas = CanvasView(scene)
    # Simula lasso_tool: desenha polígono irregular
    lasso_poly = [(5, 5), (60, 10), (55, 60), (10, 55)]
    scene.set_auto_repair(True)
    canvas.model.add_polygon(list(lasso_poly))
    assert len(scene.objects) == 1
    oid = list(scene.objects.keys())[0]
    assert len(scene.objects[oid].polygon) == 4


def test_polygon_edit_tool_real(qt_app):
    scene = Scene()
    canvas = CanvasView(scene)
    # Adiciona polígono e edita
    poly = [(0, 0), (40, 0), (40, 40), (0, 40)]
    oid = scene.add_polygon(poly)
    # Simula edição: move um vértice
    scene.objects[oid].polygon[1] = (60, 0)
    assert scene.objects[oid].polygon[1] == (60, 0)


def test_selection_tool_real(qt_app):
    scene = Scene()
    canvas = CanvasView(scene)
    # Adiciona dois polígonos
    scene.set_auto_repair(True)
    scene.add_object("poly1", [(0, 0), (40, 0), (40, 40), (0, 40)])
    scene.add_object("poly2", [(100, 100), (140, 100), (140, 140), (100, 140)])
    # Simula seleção
    canvas.model.select_object("poly2")
    assert canvas.model.selected_id == "poly2"


def test_rect_selection_tool_real(qt_app):
    scene = Scene()
    canvas = CanvasView(scene)
    # Simula seleção retangular
    rect_poly = [(10, 10), (60, 10), (60, 60), (10, 60)]
    scene.set_auto_repair(True)
    canvas.model.add_polygon(list(rect_poly))
    assert len(scene.objects) == 1
    oid = list(scene.objects.keys())[0]
    assert len(scene.objects[oid].polygon) == 4


def test_ellipse_selection_tool_real(qt_app):
    scene = Scene()
    canvas = CanvasView(scene)
    # Simula seleção elíptica (aproximação por polígono)
    ellipse_poly = [
        (30, 10),
        (50, 20),
        (60, 40),
        (50, 60),
        (30, 70),
        (10, 60),
        (0, 40),
        (10, 20),
    ]
    scene.set_auto_repair(True)
    canvas.model.add_polygon(list(ellipse_poly))
    assert len(scene.objects) == 1
    oid = list(scene.objects.keys())[0]
    assert len(scene.objects[oid].polygon) == 8
