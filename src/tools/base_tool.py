# src/tools/base_tool.py
from typing import Tuple, Optional, TYPE_CHECKING, Any
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui import QMouseEvent, QPainter

# Evita importação circular apenas para tipagem
if TYPE_CHECKING:
    from src.ui.canvas_view import CanvasView, ToolInterface


class BaseTool:
    """
    Classe base para todas as ferramentas de interação no Canvas.
    Fornece métodos utilitários de conversão de coordenadas e 
    interface padrão para o sistema de eventos.
    """

    def __init__(self, canvas_view: 'CanvasView'):
        self.canvas_view = canvas_view

    def interface(self) -> 'ToolInterface':
        """
        Adapter Method: Converte a instância da ferramenta para a ToolInterface
        que o CanvasView espera receber.
        """
        # Importação local para evitar dependência circular
        from src.ui.canvas_view import ToolInterface

        return ToolInterface(
            on_mouse_press=self.on_mouse_press,
            on_mouse_move=self.on_mouse_move,
            on_mouse_release=self.on_mouse_release,
            on_double_click=self.on_double_click,
            on_cancel=self.on_cancel,
            on_key_press=self.on_key_press,
            on_undo=self.on_undo,
            on_redo=self.on_redo,
            draw_overlay=self.draw_overlay,
            update_language=self.update_language,
        )

    @staticmethod
    def _point_coordinates(value: Any) -> Optional[Tuple[float, float]]:
        """Return numeric coordinates from QPointF-like or sequence values."""
        if isinstance(value, QPointF):
            return float(value.x()), float(value.y())

        if isinstance(value, (tuple, list)) and len(value) >= 2:
            try:
                return float(value[0]), float(value[1])
            except (TypeError, ValueError):
                return None

        x_getter = getattr(value, "x", None)
        y_getter = getattr(value, "y", None)
        if callable(x_getter) and callable(y_getter):
            try:
                return float(x_getter()), float(y_getter())
            except (TypeError, ValueError):
                return None
        return None

    def get_canvas_zoom(self, default: float = 1.0) -> float:
        """Return a finite positive canvas zoom without trusting mock objects."""
        candidates = []
        getter = getattr(self.canvas_view, "get_zoom", None)
        if callable(getter):
            try:
                candidates.append(getter())
            except Exception:
                pass
        candidates.append(getattr(self.canvas_view, "_zoom", None))
        candidates.append(default)

        for value in candidates:
            try:
                zoom = float(value)
            except (TypeError, ValueError):
                continue
            if math.isfinite(zoom) and zoom > 0:
                return zoom
        return 1.0

    def image_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """Convert image coordinates to widget coordinates with safe fallback."""
        transformer = getattr(self.canvas_view, "image_to_widget", None)
        if callable(transformer):
            try:
                converted = self._point_coordinates(transformer(x, y))
            except Exception:
                converted = None
            if converted is not None:
                return converted

        zoom = self.get_canvas_zoom()
        pan = self._point_coordinates(getattr(self.canvas_view, "_pan", None))
        pan_x, pan_y = pan if pan is not None else (0.0, 0.0)
        return float(x) * zoom + pan_x, float(y) * zoom + pan_y

    def screen_to_image(self, x: float, y: float) -> Tuple[int, int]:
        """Convert widget coordinates to image pixels with safe fallback."""
        transformer = getattr(self.canvas_view, "widget_to_image", None)
        if callable(transformer):
            try:
                converted = self._point_coordinates(transformer(QPointF(x, y)))
            except Exception:
                converted = None
            if converted is not None:
                return int(round(converted[0])), int(round(converted[1]))

        zoom = self.get_canvas_zoom()
        pan = self._point_coordinates(getattr(self.canvas_view, "_pan", None))
        pan_x, pan_y = pan if pan is not None else (0.0, 0.0)
        return int(round((x - pan_x) / zoom)), int(round((y - pan_y) / zoom))

    # --- Interface Methods (Override these in subclasses) ---

    def update_language(self, lang: str):
        """Atualiza textos da ferramenta baseado no idioma (ex: tooltips)."""
        pass

    def on_mouse_press(self, event: QMouseEvent, image_pos: Tuple[int, int]):
        """Callback de clique do mouse."""
        pass

    def on_mouse_move(self, event: QMouseEvent, image_pos: Tuple[int, int]):
        """Callback de movimento do mouse."""
        pass

    def on_mouse_release(self, event: QMouseEvent, image_pos: Tuple[int, int]):
        """Callback de soltura do mouse."""
        pass

    def on_double_click(self, event: QMouseEvent, image_pos: Tuple[int, int]):
        """Callback de duplo clique."""
        pass

    def on_cancel(self):
        """Chamado quando a ferramenta é cancelada (ex: ESC ou troca de ferramenta)."""
        pass

    def on_key_press(self, event) -> bool:
        """Handle a key press. Return True when the tool consumed the event."""
        return False

    def on_undo(self) -> bool:
        """Handle Undo inside an active tool operation."""
        return False

    def on_redo(self) -> bool:
        """Handle Redo inside an active tool operation."""
        return False

    def draw_overlay(self, painter: QPainter):
        """
        Desenha overlays visuais sobre o canvas.
        Nota: O Painter geralmente vem em coordenadas de TELA, a menos que 
        especificado o contrário no CanvasView.
        """
        pass