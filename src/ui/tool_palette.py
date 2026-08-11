# src/ui/tool_palette.py
"""
Widget containing buttons for selecting drawing and selection tools.
"""

from PySide6.QtWidgets import (
    QButtonGroup,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

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


class ToolPalette(QWidget):
    def tool_names(self):
        return [
            "lasso_tool",
            "polygonal_lasso",
            "magnetic_lasso",
            "pen_tool",
            "rect_selection",
            "ellipse_selection",
            "polygon_edit",
            "collision_brush",
            "selection",
        ]

    def __init__(self, canvas_view, parent=None):
        super().__init__(parent)
        self.canvas_view = canvas_view
        self.magnetic_lasso_settings = MagneticLassoSettings()
        self._active_magnetic_lasso = None

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # --- Tool Buttons Definition ---

        # Lasso
        self.btn_lasso = QPushButton("Lasso")
        self.btn_lasso.setCheckable(True)
        self.btn_lasso.setStyleSheet(self._get_button_style())
        self.btn_lasso.clicked.connect(self.select_lasso)

        # Polygonal Lasso
        self.btn_polygonal_lasso = QPushButton("Polygonal\nLasso")
        self.btn_polygonal_lasso.setCheckable(True)
        self.btn_polygonal_lasso.setStyleSheet(self._get_button_style())
        self.btn_polygonal_lasso.clicked.connect(self.select_polygonal_lasso)

        # Magnetic Lasso
        self.btn_magnetic_lasso = QPushButton("Magnetic\nLasso")
        self.btn_magnetic_lasso.setCheckable(True)
        self.btn_magnetic_lasso.setStyleSheet(self._get_button_style())
        self.btn_magnetic_lasso.clicked.connect(self.select_magnetic_lasso)
        self.btn_magnetic_lasso.setToolTip(
            "Magnetic Lasso: precise edge-following mode. "
            "Right-click on the canvas for Legacy mode, presets and edge preview."
        )

        # Pen
        self.btn_pen = QPushButton("Pen")
        self.btn_pen.setCheckable(True)
        self.btn_pen.setStyleSheet(self._get_button_style())
        self.btn_pen.clicked.connect(self.select_pen)

        # Rect
        self.btn_rect = QPushButton("Rect")
        self.btn_rect.setCheckable(True)
        self.btn_rect.setStyleSheet(self._get_button_style())
        self.btn_rect.clicked.connect(self.select_rect)

        # Ellipse
        self.btn_ellipse = QPushButton("Ellipse")
        self.btn_ellipse.setCheckable(True)
        self.btn_ellipse.setStyleSheet(self._get_button_style())
        self.btn_ellipse.clicked.connect(self.select_ellipse)

        # Polygon Edit
        self.btn_polygon_edit = QPushButton("Edit\nPolygon")
        self.btn_polygon_edit.setCheckable(True)
        self.btn_polygon_edit.setStyleSheet(self._get_button_style())
        self.btn_polygon_edit.clicked.connect(self.select_polygon_edit)

        # Collision Brush
        self.btn_collision_brush = QPushButton("Collision\nBrush")
        self.btn_collision_brush.setCheckable(True)
        self.btn_collision_brush.setStyleSheet(self._get_button_style())
        self.btn_collision_brush.clicked.connect(self.select_collision_brush)

        # Selection
        self.btn_selection = QPushButton("Selection")
        self.btn_selection.setCheckable(True)
        self.btn_selection.setStyleSheet(self._get_button_style())
        self.btn_selection.clicked.connect(self.select_selection)

        # --- Button Group (Exclusive Selection) ---
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.btn_lasso)
        self.button_group.addButton(self.btn_polygonal_lasso)
        self.button_group.addButton(self.btn_magnetic_lasso)
        self.button_group.addButton(self.btn_pen)
        self.button_group.addButton(self.btn_rect)
        self.button_group.addButton(self.btn_ellipse)
        self.button_group.addButton(self.btn_polygon_edit)
        self.button_group.addButton(self.btn_collision_brush)
        self.button_group.addButton(self.btn_selection)
        self.button_group.setExclusive(True)

        # --- Layout Assembly ---
        layout.addWidget(self.btn_lasso)
        layout.addWidget(self.btn_polygonal_lasso)
        layout.addWidget(self.btn_magnetic_lasso)
        layout.addWidget(self.btn_pen)
        layout.addWidget(self.btn_rect)
        layout.addWidget(self.btn_ellipse)
        layout.addWidget(self.btn_polygon_edit)
        layout.addWidget(self.btn_collision_brush)
        layout.addWidget(self.btn_selection)
        layout.addStretch()

        self.setLayout(layout)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding,
        )

        # --- Mapping for Logic ---
        # Maps internal tool names to button instances for robust cycling
        self.tool_buttons = {
            "lasso_tool": self.btn_lasso,
            "polygonal_lasso": self.btn_polygonal_lasso,
            "magnetic_lasso": self.btn_magnetic_lasso,
            "pen_tool": self.btn_pen,
            "rect_selection": self.btn_rect,
            "ellipse_selection": self.btn_ellipse,
            "polygon_edit": self.btn_polygon_edit,
            "collision_brush": self.btn_collision_brush,
            "selection": self.btn_selection,
        }

        # Localization
        self.current_lang = "en"
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
        self._refresh_button_geometry()

    def _refresh_button_geometry(self):
        """Size the palette from translated text and the active font/DPI."""
        buttons = tuple(self.tool_buttons.values())
        widest_line = max(
            (
                button.fontMetrics().horizontalAdvance(line)
                for button in buttons
                for line in (button.text().splitlines() or [""])
            ),
            default=0,
        )
        # 16 px layout margins + 16 px button padding + 6 px borders +
        # a small allowance for platform/DPI rounding.
        palette_width = max(132, min(260, widest_line + 46))
        self.setMinimumWidth(palette_width)
        self.setMaximumWidth(palette_width)

        for button in buttons:
            metrics = button.fontMetrics()
            line_count = max(1, len(button.text().splitlines()))
            minimum_height = metrics.lineSpacing() * line_count + 22
            button.setMinimumWidth(palette_width - 16)
            button.setMinimumHeight(minimum_height)
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            button.updateGeometry()

    def recommended_width(self):
        return self.minimumWidth()

    def _get_button_style(self):
        return """
            QPushButton {
                padding: 6px 8px;
            }
            QPushButton:checked {
                border: 3px solid #00BFFF;
                background-color: rgba(0, 191, 255, 50);
            }
            QPushButton:!checked {
                border: 3px solid #FF4500;
                background-color: rgba(255, 69, 0, 30);
            }
        """

    def select_next_tool(self):
        names = self.tool_names()
        current_idx = -1

        # Find currently checked button
        for i, name in enumerate(names):
            btn = self.tool_buttons.get(name)
            if btn and btn.isChecked():
                current_idx = i
                break

        next_idx = (current_idx + 1) % len(names)
        self.select_tool_by_name(names[next_idx])

    def select_prev_tool(self):
        names = self.tool_names()
        current_idx = -1

        for i, name in enumerate(names):
            btn = self.tool_buttons.get(name)
            if btn and btn.isChecked():
                current_idx = i
                break

        prev_idx = (current_idx - 1) % len(names)
        self.select_tool_by_name(names[prev_idx])

    def select_tool_by_name(self, tool_name: str):
        # Update UI state
        btn = self.tool_buttons.get(tool_name)
        if btn:
            btn.setChecked(True)

        mapping = {
            "lasso_tool": self.select_lasso,
            "polygonal_lasso": self.select_polygonal_lasso,
            "magnetic_lasso": self.select_magnetic_lasso,
            "pen_tool": self.select_pen,
            "rect_selection": self.select_rect,
            "ellipse_selection": self.select_ellipse,
            "polygon_edit": self.select_polygon_edit,
            "collision_brush": self.select_collision_brush,
            "selection": self.select_selection,
        }
        if tool_name in mapping:
            mapping[tool_name]()

    def select_lasso(self):
        # CORREÇÃO: LassoTool agora exige (view, model)
        lasso_tool = LassoTool(self.canvas_view, self.canvas_view.model)
        self.canvas_view.set_tool(lasso_tool.interface())

    def select_polygonal_lasso(self):
        # Mantém compatibilidade com __init__(view) se não foi alterado,
        # ou ajusta se necessário. Pelo contexto dos logs anteriores,
        # PolygonalLassoTool acessava o model via view.
        polygonal_lasso_tool = PolygonalLassoTool(self.canvas_view)
        self.canvas_view.set_tool(polygonal_lasso_tool.interface())

    def select_magnetic_lasso(self):
        magnetic_lasso_tool = MagneticLassoTool(
            self.canvas_view,
            settings=self.magnetic_lasso_settings,
        )
        magnetic_lasso_tool.update_language(self.current_lang)
        self._active_magnetic_lasso = magnetic_lasso_tool
        self.canvas_view.set_tool(magnetic_lasso_tool.interface())
        magnetic_lasso_tool.prepare_edge_map_async()

    def select_pen(self):
        pen_tool = PenTool(self.canvas_view)
        self.canvas_view.set_tool(pen_tool.interface())

    def select_rect(self):
        rect_tool = RectSelectionTool(self.canvas_view)
        self.canvas_view.set_tool(rect_tool.interface())

    def select_ellipse(self):
        ellipse_tool = EllipseSelectionTool(self.canvas_view)
        self.canvas_view.set_tool(ellipse_tool.interface())

    def select_polygon_edit(self):
        polygon_edit_tool = PolygonEditTool(self.canvas_view)
        self.canvas_view.set_tool(polygon_edit_tool.interface())

    def select_collision_brush(self):
        collision_brush_tool = CollisionBrushTool(self.canvas_view)
        self.canvas_view.set_tool(collision_brush_tool.interface())

    def select_selection(self):
        selection_tool = SelectionTool(self.canvas_view)
        self.canvas_view.set_tool(selection_tool.interface())

    def update_language(self, lang):
        self.current_lang = lang
        t = self.translations[self.current_lang]
        self.btn_lasso.setText(t["lasso"])
        self.btn_polygonal_lasso.setText(t["polygonal_lasso"])
        self.btn_magnetic_lasso.setText(t["magnetic_lasso"])
        if self.current_lang == "pt":
            self.btn_magnetic_lasso.setToolTip(
                "Laço Magnético em modo preciso. Clique com o botão direito no canvas "
                "para escolher modo legado, nível de precisão e mapa de bordas."
            )
        else:
            self.btn_magnetic_lasso.setToolTip(
                "Magnetic Lasso in precise mode. Right-click the canvas "
                "for Legacy mode, "
                "precision presets and edge-map preview."
            )
        if self._active_magnetic_lasso is not None:
            self._active_magnetic_lasso.update_language(self.current_lang)
        self.btn_pen.setText(t["pen"])
        self.btn_rect.setText(t["rect"])
        self.btn_ellipse.setText(t["ellipse"])
        self.btn_polygon_edit.setText(t["polygon_edit"])
        self.btn_collision_brush.setText(t["collision_brush"])
        self.btn_selection.setText(t["selection"])
        self._refresh_button_geometry()
