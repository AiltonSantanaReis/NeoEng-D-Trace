# src/ui/export_preview.py
"""
Export Preview Dialog for NeoEng-D-Trace.
"""

from typing import Any, Dict, Optional

from PIL import Image, ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
)


class ExportPreviewDialog(QDialog):
    """
    Dialog for previewing exported sprites.
    """

    TRANSLATIONS = {
        "en": {
            "window_title": "Export Preview",
            "preview_controls": "Preview Controls",
            "zoom": "Zoom:",
            "scale_to_fit": "Scale to fit",
            "antialias": "Antialias",
            "metadata": "Metadata",
            "no_metadata": "No metadata available",
            "export": "Export",
            "close": "Close",
            "save_sprite": "Save Sprite",
            "png_filter": "PNG Files (*.png);;All Files (*)",
            "export_title": "Export",
            "saved": "Sprite saved to {path}",
            "export_error": "Export Error",
            "save_failed": "Failed to save sprite: {error}",
            "rect": "Rect",
            "pivot": "Pivot",
        },
        "pt": {
            "window_title": "Pré-visualização da Exportação",
            "preview_controls": "Controles da Pré-visualização",
            "zoom": "Zoom:",
            "scale_to_fit": "Ajustar ao espaço",
            "antialias": "Suavização",
            "metadata": "Metadados",
            "no_metadata": "Nenhum metadado disponível",
            "export": "Exportar",
            "close": "Fechar",
            "save_sprite": "Salvar Sprite",
            "png_filter": "Arquivos PNG (*.png);;Todos os Arquivos (*)",
            "export_title": "Exportação",
            "saved": "Sprite salvo em {path}",
            "export_error": "Erro de Exportação",
            "save_failed": "Falha ao salvar o sprite: {error}",
            "rect": "Retângulo",
            "pivot": "Pivô",
        },
    }

    def __init__(
        self,
        sprite: Image.Image,
        metadata: Dict[str, Any],
        parent=None,
        lang: Optional[str] = None,
    ):
        super().__init__(parent)
        self.sprite = sprite
        self.metadata = metadata
        self.zoom_factor = 1.0
        self.scale_preview = True
        self.antialias = True
        inherited_lang = getattr(parent, "current_lang", "en")
        self.current_lang = lang if lang in self.TRANSLATIONS else inherited_lang
        if self.current_lang not in self.TRANSLATIONS:
            self.current_lang = "en"

        self.setWindowTitle(self.TRANSLATIONS[self.current_lang]["window_title"])
        self.setModal(True)
        self.resize(800, 600)

        self._setup_ui()
        self._update_preview()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Preview area
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFrameStyle(QFrame.Shape.Box)
        self.preview_label.setMinimumSize(400, 300)

        scroll_area = QScrollArea()
        scroll_area.setWidget(self.preview_label)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Controls
        self.controls_group = QGroupBox()
        controls_layout = QHBoxLayout(self.controls_group)

        # Zoom slider
        self.zoom_text_label = QLabel()
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 500)  # 0.1x to 5x
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)

        # Scale preview checkbox
        self.scale_checkbox = QCheckBox()
        self.scale_checkbox.setChecked(True)
        self.scale_checkbox.stateChanged.connect(self._on_scale_changed)

        # Antialias checkbox
        self.antialias_checkbox = QCheckBox()
        self.antialias_checkbox.setChecked(True)
        self.antialias_checkbox.stateChanged.connect(self._on_antialias_changed)

        controls_layout.addWidget(self.zoom_text_label)
        controls_layout.addWidget(self.zoom_slider)
        controls_layout.addWidget(self.scale_checkbox)
        controls_layout.addWidget(self.antialias_checkbox)
        layout.addWidget(self.controls_group)

        # Metadata display
        self.metadata_group = QGroupBox()
        metadata_layout = QVBoxLayout(self.metadata_group)

        self.metadata_label = QLabel()
        self._update_metadata_display()
        metadata_layout.addWidget(self.metadata_label)

        layout.addWidget(self.metadata_group)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.export_button = QPushButton()
        self.export_button.clicked.connect(self._on_export)
        buttons_layout.addWidget(self.export_button)

        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_button)

        layout.addLayout(buttons_layout)
        self.update_language(self.current_lang)

    def update_language(self, lang: str):
        self.current_lang = lang if lang in self.TRANSLATIONS else "en"
        t = self.TRANSLATIONS[self.current_lang]
        self.setWindowTitle(t["window_title"])
        self.controls_group.setTitle(t["preview_controls"])
        self.zoom_text_label.setText(t["zoom"])
        self.scale_checkbox.setText(t["scale_to_fit"])
        self.antialias_checkbox.setText(t["antialias"])
        self.metadata_group.setTitle(t["metadata"])
        self.export_button.setText(t["export"])
        self.close_button.setText(t["close"])
        self._update_metadata_display()

    def _update_preview(self):
        """Update the preview image based on current settings."""
        if self.sprite is None:
            return

        # Apply zoom
        if self.scale_preview:
            # Scale to fit the label size
            label_size = self.preview_label.size()
            if label_size.width() > 0 and label_size.height() > 0:
                scaled = self.sprite.resize(
                    (
                        int(label_size.width() * self.zoom_factor),
                        int(label_size.height() * self.zoom_factor),
                    ),
                    (
                        Image.Resampling.LANCZOS
                        if self.antialias
                        else Image.Resampling.NEAREST
                    ),
                )
            else:
                scaled = self.sprite
        else:
            scaled = self.sprite.resize(
                (
                    int(self.sprite.width * self.zoom_factor),
                    int(self.sprite.height * self.zoom_factor),
                ),
                (
                    Image.Resampling.LANCZOS
                    if self.antialias
                    else Image.Resampling.NEAREST
                ),
            )

        # Convert to QPixmap
        qt_image = ImageQt.ImageQt(scaled)

        pixmap = QPixmap.fromImage(qt_image)
        self.preview_label.setPixmap(pixmap)

    def _update_metadata_display(self):
        """Update the metadata display label."""
        if not self.metadata:
            self.metadata_label.setText(
                self.TRANSLATIONS[self.current_lang]["no_metadata"]
            )
            return

        lines = []
        if "rect" in self.metadata:
            rect = self.metadata["rect"]
            lines.append(
                f"{self.TRANSLATIONS[self.current_lang]['rect']}: x={rect.get('x', '?')}, y={rect.get('y', '?')}, "
                f"w={rect.get('w', '?')}, h={rect.get('h', '?')}"
            )
        if "pivot" in self.metadata:
            pivot = self.metadata["pivot"]
            if isinstance(pivot, list):
                lines.append(f"Pivot: ({pivot[0]:.1f}, {pivot[1]:.1f})")
            elif isinstance(pivot, dict):
                pivot_x = pivot.get("x")
                pivot_y = pivot.get("y")
                if isinstance(pivot_x, (int, float)) and isinstance(
                    pivot_y, (int, float)
                ):
                    lines.append(
                        f"{self.TRANSLATIONS[self.current_lang]['pivot']}: "
                        f"x={pivot_x:.3f}, y={pivot_y:.3f}"
                    )
                else:
                    lines.append(
                        f"{self.TRANSLATIONS[self.current_lang]['pivot']}: "
                        f"x={pivot_x if pivot_x is not None else '?'}, "
                        f"y={pivot_y if pivot_y is not None else '?'}"
                    )
        if "id" in self.metadata:
            lines.append(f"ID: {self.metadata['id']}")

        self.metadata_label.setText("\n".join(lines))

    def _on_zoom_changed(self, value):
        self.zoom_factor = value / 100.0
        self._update_preview()

    def _on_scale_changed(self, state):
        self.scale_preview = state == Qt.CheckState.Checked.value
        self._update_preview()

    def _on_antialias_changed(self, state):
        self.antialias = state == Qt.CheckState.Checked.value
        self._update_preview()

    def _on_export(self):
        """Handle export button click."""
        from src.exporters.sprite_exporter import save_sprite

        # Save the current sprite
        t = self.TRANSLATIONS[self.current_lang]
        file_path, _ = QFileDialog.getSaveFileName(
            self, t["save_sprite"], "", t["png_filter"]
        )
        if file_path:
            try:
                save_sprite(self.sprite, file_path)
                QMessageBox.information(
                    self, t["export_title"], t["saved"].format(path=file_path)
                )
            except Exception as e:
                QMessageBox.critical(
                    self, t["export_error"], t["save_failed"].format(error=e)
                )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.scale_preview:
            self._update_preview()


def export_preview_headless(
    image: Image.Image,
    metadata: Dict[str, Any],
    output_path: str = "preview.png",
):
    """
    Headless fallback: save a sample preview PNG.
    """
    # Create a simple preview with metadata overlay
    preview = image.copy()
    if metadata:
        from PIL import ImageDraw, ImageFont

        draw = ImageDraw.Draw(preview)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            font = ImageFont.load_default()  # type: ignore

        lines = []
        if "id" in metadata:
            lines.append(f"ID: {metadata['id']}")
        if "rect" in metadata:
            rect = metadata["rect"]
            lines.append(f"Rect: {rect.get('w', '?')}x{rect.get('h', '?')}")
        if "pivot" in metadata:
            pivot = metadata["pivot"]
            if isinstance(pivot, list):
                lines.append(f"Pivot: ({pivot[0]:.1f}, {pivot[1]:.1f})")
            elif isinstance(pivot, dict):
                lines.append(
                    f"Pivot: ({pivot.get('x', 0):.3f}, " f"{pivot.get('y', 0):.3f})"
                )

        y = 10
        for line in lines:
            draw.text(
                (10, y),
                line,
                fill="white",
                font=font,
                stroke_fill="black",
                stroke_width=2,
            )
            y += 25

    preview.save(output_path)
    print(f"Preview saved to {output_path}")
