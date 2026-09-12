"""Deterministic contract tests for the isolated E01-B fixture."""

from __future__ import annotations

import pytest
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from scripts.e01_backend_bench import SCENE, _draw_fixture


@pytest.fixture
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_e01_backend_fixture_declares_required_scene_contract() -> None:
    assert SCENE["camera"]["projection"] == "orthographic"
    assert SCENE["coordinates"]["origin"] == "top_left"
    assert SCENE["texture"]["alpha"] is True
    assert SCENE["light"]["alters_pixels"] is True
    assert SCENE["particles"]["visible"] is True


def test_e01_backend_fixture_raster_frame_is_nonempty_and_deterministic(qt_app) -> None:
    first = QImage(640, 360, QImage.Format.Format_ARGB32_Premultiplied)
    painter = QPainter(first)
    _draw_fixture(painter, 640, 360)
    painter.end()

    second = QImage(640, 360, QImage.Format.Format_ARGB32_Premultiplied)
    painter = QPainter(second)
    _draw_fixture(painter, 640, 360)
    painter.end()

    assert not first.isNull()
    assert first.size() == second.size()
    assert first.bits().tobytes() == second.bits().tobytes()
