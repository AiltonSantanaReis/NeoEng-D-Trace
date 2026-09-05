# src/tools/base_tool.py
import math
from typing import TYPE_CHECKING, Any, Optional, Sequence, Tuple

from PySide6.QtCore import QPointF
from PySide6.QtGui import QMouseEvent, QPainter
from PySide6.QtWidgets import QMessageBox, QWidget

from src.core.logger import logger

# Evita importação circular apenas para tipagem
if TYPE_CHECKING:
    from src.ui.canvas_view import CanvasView, ToolInterface


class BaseTool:
    """
    Classe base para todas as ferramentas de interação no Canvas.
    Fornece métodos utilitários de conversão de coordenadas e
    interface padrão para o sistema de eventos.
    """

    def __init__(self, canvas_view: "CanvasView"):
        self.canvas_view = canvas_view

    def interface(self) -> "ToolInterface":
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

    def _message_parent(self) -> Optional[QWidget]:
        """Return a valid Qt parent while keeping adapter/headless tools usable."""
        return self.canvas_view if isinstance(self.canvas_view, QWidget) else None

    def _show_message(self, level: str, title: str, message: str) -> None:
        """Show a tool message without replacing the original error with Qt
        type errors.
        """
        parent = self._message_parent()
        if parent is None:
            logger.warning("%s: %s", title, message)
            return
        getattr(QMessageBox, level)(parent, title, message)

    def _p2d05_language(self) -> str:
        """Return the active language for the P2D-05 presentation boundary."""

        language = getattr(self, "current_lang", None)
        if not isinstance(language, str):
            language = getattr(self.canvas_view, "current_lang", "en")
        if not isinstance(language, str):
            return "en"
        return language if language in {"en", "pt"} else "en"

    def _present_p2d05_error(
        self,
        exc: BaseException,
        *,
        operation: str,
        severity: str = "warning",
        channel: str = "modal",
    ) -> str:
        """Present a safe P2D-05 error and retain its user-facing message."""

        from src.ui.error_presentation import show_p2d05_error

        presentation = show_p2d05_error(
            self._message_parent(),
            exc,
            operation=operation,
            language=self._p2d05_language(),
            severity=severity,
            channel=channel,
        )
        if hasattr(self, "_last_error"):
            setattr(self, "_last_error", presentation.message)
        return presentation.message

    def _safe_p2d05_message(self, exc: BaseException, *, operation: str) -> str:
        """Build a safe message without interrupting a continuous preview."""

        from src.ui.error_presentation import build_p2d05_presentation

        return build_p2d05_presentation(
            exc,
            operation=operation,
            language=self._p2d05_language(),
        ).message

    def commit_polygon_command(
        self,
        polygon: Sequence[Tuple[int, int]],
        *,
        action_name: str = "Polygon Creation",
    ) -> Optional[str]:
        """Create one polygon only through the scene CommandManager."""
        model = getattr(self.canvas_view, "model", None)
        manager = getattr(model, "cmd", None)
        if manager is None:
            message = "Undo/Redo command history is unavailable."
            if hasattr(self, "_last_error"):
                setattr(self, "_last_error", message)
            self._show_message(
                "critical",
                f"{action_name} Unavailable",
                message,
            )
            return None

        from src.core.commands import AddPolygonCommand, CommandStatus

        command = AddPolygonCommand(list(polygon))
        try:
            result = manager.execute(command, model)
        except Exception as exc:
            logger.error(
                "%s command execution failed (%s)",
                action_name,
                type(exc).__name__,
                exc_info=True,
            )
            message = f"The creation request failed ({type(exc).__name__})."
            if hasattr(self, "_last_error"):
                setattr(self, "_last_error", message)
            self._show_message(
                "critical",
                f"{action_name} Failed",
                message,
            )
            return None

        self._last_command_result = result
        if result.status is CommandStatus.REJECTED:
            if hasattr(self, "_last_error"):
                setattr(self, "_last_error", result.message)
            self._show_message(
                "warning",
                f"{action_name} Rejected",
                result.message or "The polygon creation was rejected.",
            )
            return None
        if result.status is CommandStatus.FAILED:
            if hasattr(self, "_last_error"):
                setattr(self, "_last_error", result.message)
            self._show_message(
                "critical",
                f"{action_name} Failed",
                result.message or "The polygon creation failed.",
            )
            return None
        if not result.changed or command.object_id is None:
            message = result.message or "No polygon was created."
            if hasattr(self, "_last_error"):
                setattr(self, "_last_error", message)
            self._show_message(
                "warning",
                f"{action_name} Unchanged",
                message,
            )
            return None
        return str(command.object_id)

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
