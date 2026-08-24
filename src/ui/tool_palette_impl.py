"""Vertical, action-backed toolbar for the main editor tools.

The public ``btn_*``, ``tool_buttons`` and ``button_group`` attributes are
kept as compatibility views for existing integrations and tests. The
presentation itself is a real ``QToolBar`` with exclusive ``QAction`` groups,
compact icon-first controls and keyboard-focusable buttons.
"""

from __future__ import annotations

from typing import Final

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QButtonGroup, QSizePolicy, QToolBar, QToolButton

from src.tools.collision_brush_tool import CollisionBrushTool
from src.tools.ellipse_selection import EllipseSelectionTool
from src.tools.lasso_tool import LassoTool
from src.tools.magnetic_lasso import MagneticLassoTool
from src.tools.magnetic_lasso_engine import MagneticLassoSettings
from src.tools.pen_tool import PenTool
from src.tools.polygon_edit_tool import PolygonEditTool
from src.tools.polygonal_lasso import PolygonalLassoTool
from src.tools.rect_selection import RectSelectionTool
from src.tools.selection_tool import SelectionTool
from src.ui.icon_library import configure_action, configure_widget

_TOOL_SPECS: Final[tuple[tuple[str, str, str, str | None], ...]] = (
    # Keep the action order aligned with the normative rail groups:
    # selection, outline, collision. IDs and shortcuts remain unchanged.
    ("selection", "selection", "selection", None),
    ("rect_selection", "rect", "rect", "3"),
    ("ellipse_selection", "ellipse", "ellipse", "4"),
    ("lasso_tool", "lasso", "lasso", "2"),
    ("polygonal_lasso", "polygon", "polygonal_lasso", "1"),
    ("magnetic_lasso", "magnetic", "magnetic_lasso", "6"),
    ("pen_tool", "pen", "pen", "5"),
    ("polygon_edit", "polygon_edit", "polygon_edit", None),
    ("collision_brush", "collision_brush", "collision_brush", None),
)

_AUXILIARY_SPECS: Final[tuple[tuple[str, str, str], ...]] = (
    ("validation", "validation", "Validate collision geometry"),
    ("move_viewport", "move", "Move viewport"),
    ("zoom_viewport", "zoom", "Zoom viewport"),
    ("fit_view", "fit", "Fit viewport"),
    ("focus_selected", "focus", "Focus selected object"),
)


class ToolPalette(QToolBar):
    """Compact vertical toolbar preserving the historical tool API."""

    auxiliary_action_requested = Signal(str)

    def tool_names(self) -> list[str]:
        return [spec[0] for spec in _TOOL_SPECS]

    def __init__(self, canvas_view, parent=None):
        super().__init__("Tools", parent)
        self.canvas_view = canvas_view
        self.magnetic_lasso_settings = MagneticLassoSettings()
        self._active_magnetic_lasso = None
        self.current_lang = "en"
        self._enabled = True

        self.setObjectName("left_tool_toolbar")
        self.setOrientation(Qt.Orientation.Vertical)
        self.setMovable(False)
        self.setFloatable(False)
        self.setAllowedAreas(
            Qt.ToolBarArea.LeftToolBarArea | Qt.ToolBarArea.RightToolBarArea
        )
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setIconSize(QSize(20, 20))
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding,
        )
        self.setProperty("uiRole", "tool_palette")

        self.translations = {
            "en": {
                "lasso": "Lasso",
                "polygonal_lasso": "Polygonal\nLasso",
                "magnetic_lasso": "Magnetic\nLasso",
                "pen": "Pen",
                "rect": "Rect",
                "ellipse": "Ellipse",
                "polygon_edit": "Edit\nPolygon",
                "collision_brush": "Collision\nBrush",
                "selection": "Selection",
            },
            "pt": {
                "lasso": "Laço",
                "polygonal_lasso": "Laço\nPoligonal",
                "magnetic_lasso": "Laço\nMagnético",
                "pen": "Caneta",
                "rect": "Retângulo",
                "ellipse": "Elipse",
                "polygon_edit": "Editar\nPolígono",
                "collision_brush": "Pincel\nColisão",
                "selection": "Seleção",
            },
        }
        self._tooltips = {
            "en": {
                "lasso": "Lasso tool (2)",
                "polygonal_lasso": "Polygonal lasso (1)",
                "magnetic_lasso": (
                    "Magnetic lasso (6). Right-click the canvas for modes and presets."
                ),
                "pen": "Pen tool (5)",
                "rect": "Rectangle selection (3)",
                "ellipse": "Ellipse selection (4)",
                "polygon_edit": "Edit polygon vertices",
                "collision_brush": "Paint collision geometry",
                "selection": "Select objects",
            },
            "pt": {
                "lasso": "Ferramenta laço (2)",
                "polygonal_lasso": "Laço poligonal (1)",
                "magnetic_lasso": (
                    "Laço magnético (6). Clique direito no canvas para modos e presets."
                ),
                "pen": "Ferramenta caneta (5)",
                "rect": "Seleção retangular (3)",
                "ellipse": "Seleção elíptica (4)",
                "polygon_edit": "Editar vértices do polígono",
                "collision_brush": "Pintar geometria de colisão",
                "selection": "Selecionar objetos",
            },
        }
        self._tool_actions: dict[str, QAction] = {}
        self._auxiliary_actions: dict[str, QAction] = {}
        self.tool_buttons: dict[str, QToolButton] = {}
        self.action_group = QActionGroup(self)
        self.action_group.setExclusive(True)
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        for index, (tool_name, icon_key, label_key, _shortcut) in enumerate(
            _TOOL_SPECS
        ):
            if index in (3, 8):
                self.addSeparator()
            action = QAction(self)
            action.setObjectName(f"tool_action_{tool_name}")
            action.setCheckable(True)
            action.setData(tool_name)
            configure_action(
                action,
                icon_key,
                text=self.translations["en"][label_key],
                accessible_name=tool_name,
            )
            self.action_group.addAction(action)
            self.addAction(action)
            button = self.widgetForAction(action)
            if not isinstance(button, QToolButton):
                raise RuntimeError(
                    f"Toolbar action did not create a tool button: {tool_name}"
                )
            button.setObjectName(f"tool_button_{tool_name}")
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            button.setMinimumSize(QSize(44, 40))
            button.setProperty("uiRole", "tool")
            button.setProperty("toolName", tool_name)
            configure_widget(button, icon_key, accessible_name=tool_name)
            self.button_group.addButton(button)
            callback = getattr(self, f"select_{self._callback_name(tool_name)}")
            action.triggered.connect(callback)
            self._tool_actions[tool_name] = action
            self.tool_buttons[tool_name] = button

        self.btn_lasso = self.tool_buttons["lasso_tool"]
        self.btn_polygonal_lasso = self.tool_buttons["polygonal_lasso"]
        self.btn_magnetic_lasso = self.tool_buttons["magnetic_lasso"]
        self.btn_pen = self.tool_buttons["pen_tool"]
        self.btn_rect = self.tool_buttons["rect_selection"]
        self.btn_ellipse = self.tool_buttons["ellipse_selection"]
        self.btn_polygon_edit = self.tool_buttons["polygon_edit"]
        self.btn_collision_brush = self.tool_buttons["collision_brush"]
        self.btn_selection = self.tool_buttons["selection"]
        self._build_auxiliary_actions()
        self._refresh_button_geometry()
        self._refresh_tool_feedback()

    def _build_auxiliary_actions(self) -> None:
        """Expose the remaining source-required rail groups as real actions."""

        for action_name, icon_key, label in _AUXILIARY_SPECS:
            action = QAction(self)
            action.setObjectName(f"rail_action_{action_name}")
            action.setData(action_name)
            action.setCheckable(action_name == "move_viewport")
            configure_action(
                action,
                icon_key,
                text=label,
                tooltip=label,
                accessible_name=label,
            )
            action.setProperty(
                "railGroup",
                "navigation" if action_name != "validation" else "collision",
            )
            action.triggered.connect(
                lambda _checked=False, name=action_name:
                self.auxiliary_action_requested.emit(name)
            )
            self.addAction(action)
            self._auxiliary_actions[action_name] = action
            if action_name == "validation":
                self.addSeparator()
        self.navigation_actions = dict(self._auxiliary_actions)

    @staticmethod
    def _callback_name(tool_name: str) -> str:
        return {
            "lasso_tool": "lasso",
            "polygonal_lasso": "polygonal_lasso",
            "magnetic_lasso": "magnetic_lasso",
            "pen_tool": "pen",
            "rect_selection": "rect",
            "ellipse_selection": "ellipse",
            "polygon_edit": "polygon_edit",
            "collision_brush": "collision_brush",
            "selection": "selection",
        }[tool_name]

    def _refresh_button_geometry(self) -> None:
        """Keep a stable compact hit target at every DPI and language."""
        self.setMinimumWidth(56)
        self.setMaximumWidth(64)
        for button in self.tool_buttons.values():
            button.setIconSize(QSize(20, 20))
            button.setMinimumSize(QSize(44, 40))
            button.setMaximumWidth(56)
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            button.updateGeometry()
        self.updateGeometry()

    def recommended_width(self) -> int:
        return self.minimumWidth()

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self._enabled = enabled
        if hasattr(self, "_tool_actions"):
            self._refresh_tool_feedback()

    def _refresh_tool_feedback(self) -> None:
        language = self.current_lang if self.current_lang in self.translations else "en"
        labels = self.translations[language]
        tips = self._tooltips[language]
        for tool_name, action in self._tool_actions.items():
            label_key = next(spec[2] for spec in _TOOL_SPECS if spec[0] == tool_name)
            label = labels[label_key]
            tooltip = tips[label_key]
            if not self._enabled:
                tooltip += (
                    " — Open an image to enable tools."
                    if language == "en"
                    else " — Abra uma imagem para habilitar as ferramentas."
                )
            action.setText(label)
            action.setToolTip(tooltip)
            action.setStatusTip(tooltip)
            button = self.tool_buttons[tool_name]
            button.setToolTip(tooltip)
            button.setStatusTip(tooltip)
            button.setAccessibleName(label.replace("\n", " "))

    def select_next_tool(self) -> None:
        names = self.tool_names()
        current_idx = next(
            (
                index
                for index, name in enumerate(names)
                if self.tool_buttons[name].isChecked()
            ),
            -1,
        )
        self.select_tool_by_name(names[(current_idx + 1) % len(names)])

    def select_prev_tool(self) -> None:
        names = self.tool_names()
        current_idx = next(
            (
                index
                for index, name in enumerate(names)
                if self.tool_buttons[name].isChecked()
            ),
            -1,
        )
        self.select_tool_by_name(names[(current_idx - 1) % len(names)])

    def select_tool_by_name(self, tool_name: str) -> None:
        action = self._tool_actions.get(tool_name)
        button = self.tool_buttons.get(tool_name)
        if action is None or button is None:
            return
        action.setChecked(True)
        button.setChecked(True)
        if "move_viewport" in self._auxiliary_actions:
            self._auxiliary_actions["move_viewport"].setChecked(False)
        getattr(self, f"select_{self._callback_name(tool_name)}")()

    def select_lasso(self):
        tool = LassoTool(self.canvas_view, self.canvas_view.model)
        self.canvas_view.set_tool(tool.interface())

    def select_polygonal_lasso(self):
        tool = PolygonalLassoTool(self.canvas_view)
        self.canvas_view.set_tool(tool.interface())

    def select_magnetic_lasso(self):
        tool = MagneticLassoTool(
            self.canvas_view,
            settings=self.magnetic_lasso_settings,
        )
        tool.update_language(self.current_lang)
        self._active_magnetic_lasso = tool
        self.canvas_view.set_tool(tool.interface())
        tool.prepare_edge_map_async()

    def select_pen(self):
        self.canvas_view.set_tool(PenTool(self.canvas_view).interface())

    def select_rect(self):
        self.canvas_view.set_tool(RectSelectionTool(self.canvas_view).interface())

    def select_ellipse(self):
        self.canvas_view.set_tool(EllipseSelectionTool(self.canvas_view).interface())

    def select_polygon_edit(self):
        self.canvas_view.set_tool(PolygonEditTool(self.canvas_view).interface())

    def select_collision_brush(self):
        self.canvas_view.set_tool(CollisionBrushTool(self.canvas_view).interface())

    def select_selection(self):
        self.canvas_view.set_tool(SelectionTool(self.canvas_view).interface())

    def update_language(self, lang):
        self.current_lang = lang if lang in self.translations else "en"
        self._refresh_tool_feedback()
        if self._active_magnetic_lasso is not None:
            self._active_magnetic_lasso.update_language(self.current_lang)
