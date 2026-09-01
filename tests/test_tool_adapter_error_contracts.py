"""Regression tests for tool adapters used outside the concrete Qt canvas."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
from PySide6.QtWidgets import QMessageBox

from src.tools.base_tool import BaseTool
from src.tools.magnetic_lasso import MagneticLassoTool


class _Tool(BaseTool):
    def __init__(self, canvas_view):
        super().__init__(canvas_view)
        self._last_error = None


class _FailingManager:
    def execute(self, command, scene):
        raise RuntimeError("sentinel command failure")


def test_tool_error_dialog_does_not_replace_root_error_for_non_widget_adapter(
    monkeypatch,
):
    canvas = Mock()
    canvas.model = SimpleNamespace(cmd=_FailingManager())
    tool = _Tool(canvas)
    calls = []
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda *args: calls.append(args),
    )

    result = tool.commit_polygon_command([(0, 0), (10, 0), (0, 10)])

    assert result is None
    assert tool._last_error == "The creation request failed (RuntimeError)."
    assert calls == []


def test_magnetic_lasso_uses_model_when_scene_adapter_has_no_image_getter():
    image = np.zeros((4, 5), dtype=np.uint8)

    class SceneAdapterWithoutImage:
        pass

    class ModelAdapter:
        def get_image(self):
            return image

    canvas = SimpleNamespace(
        scene=SceneAdapterWithoutImage(),
        model=ModelAdapter(),
    )
    tool = MagneticLassoTool(canvas)

    assert tool._get_scene_image() is image
    np.testing.assert_array_equal(tool._get_image_array(), image)
