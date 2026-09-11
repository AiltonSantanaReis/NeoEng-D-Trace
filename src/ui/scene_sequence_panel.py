"""Integrated timeline, real preview and media lifecycle for scene authoring."""

from pathlib import Path
import time
from uuid import uuid4

from PySide6.QtCore import Qt, QTimer, Signal, QUrl, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel,
    QCheckBox, QFormLayout, QLineEdit, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QFileDialog, QScrollArea,
)

from src.core.scene_sequence import set_sequence, evaluate_sequence, active_clips, particles_at
from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.core.scene_asset_library import resolve_scene_asset, prepare_scene_asset
from src.persistence.scene_authoring_schema import AssetReferenceRecord
from src.persistence.scene_sequence_schema import SceneClip, SceneSequence
from src.ui.numeric_controls import ProtectedDoubleSpinBox
from src.ui.scene_authoring_viewport import SceneAuthoringViewport


KINDS = ("camera", "motion", "light", "rain", "snow", "dust", "fire", "audio", "text")
NAMES_PT = ("Câmera", "Animação", "Luz", "Chuva", "Neve", "Poeira", "Fogo", "Áudio", "Texto / cutscene")
NAMES_EN = ("Camera", "Animation", "Light", "Rain", "Snow", "Dust", "Fire", "Audio", "Text / cutscene")
COLORS = ("#668fae", "#817ab5", "#b28e53", "#508d9e", "#92a9b5", "#9b8970", "#b26a51", "#5c956b", "#ac7795")


def spin(name, minimum, maximum, value=0):
    field = ProtectedDoubleSpinBox()
    field.setObjectName(name)
    field.setRange(minimum, maximum)
    field.setDecimals(2)
    field.setValue(value)
    return field


class ClipBlock(QGraphicsRectItem):
    def __init__(self, panel, clip, row):
        super().__init__(0, 0, max(6, clip.duration * panel.pixels_per_second), 24)
        self.panel, self.clip = panel, clip
        self.setPos(150 + clip.start * panel.pixels_per_second, 28 + row * 31)
        self.setBrush(QBrush(QColor(COLORS[KINDS.index(clip.kind)])))
        self.setPen(QPen(QColor("#53d4e8" if panel.selected_id == clip.id else "#b6c2ce")))
        self.setToolTip(f"{clip.name} · {clip.start:.2f}s — {clip.start + clip.duration:.2f}s")

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.save()
        painter.setClipRect(self.rect().adjusted(4, 0, -4, 0))
        painter.setPen(QColor("#ffffff"))
        painter.drawText(self.rect().adjusted(6, 0, -6, 0), Qt.AlignmentFlag.AlignVCenter, self.clip.name)
        painter.restore()

    def mousePressEvent(self, event):
        self.origin = event.scenePos().x()
        self.resizing = event.pos().x() >= self.rect().width() - 8
        self.panel.select_clip(self.clip.id, redraw=False)
        self.setPen(QPen(QColor("#53d4e8"), 2))
        event.accept()

    def mouseMoveEvent(self, event):
        delta = (event.scenePos().x() - self.origin) / self.panel.pixels_per_second
        if self.resizing:
            duration = max(0.05, min(self.panel.sequence.duration - self.clip.start, self.clip.duration + delta))
            self.setRect(0, 0, duration * self.panel.pixels_per_second, 24)
        else:
            start = max(0, min(self.panel.sequence.duration - self.clip.duration, self.clip.start + delta))
            self.setX(150 + start * self.panel.pixels_per_second)
        event.accept()

    def mouseReleaseEvent(self, event):
        # Deferred: rebuilding a QGraphicsScene while its item handles an event
        # destroys the native receiver and can crash Qt.
        patch = {"duration": self.rect().width() / self.panel.pixels_per_second} if self.resizing else {"start": (self.x() - 150) / self.panel.pixels_per_second}
        clip_id = self.clip.id
        QTimer.singleShot(0, lambda: self.panel.change_clip(clip_id, patch))
        event.accept()


class TimelineView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self._scrubbing = False
        self.setMouseTracking(True)

    def _seek_from_event(self, event) -> bool:
        position = self.mapToScene(event.position().toPoint())
        if position.x() < 150 or position.y() >= 26:
            return False
        self.parent_panel.seek(
            (position.x() - 150) / self.parent_panel.pixels_per_second
        )
        return True

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._seek_from_event(event):
            self._scrubbing = True
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._scrubbing and event.buttons() & Qt.MouseButton.LeftButton:
            self._seek_from_event(event)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._scrubbing and event.button() == Qt.MouseButton.LeftButton:
            self._seek_from_event(event)
            self._scrubbing = False
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class SequenceViewport(SceneAuthoringViewport):
    def __init__(self, session, project_root, parent=None):
        self.sequence_clips = ()
        self.sequence_position = 0.0
        super().__init__(session, project_root=project_root, parent=parent)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        document = self.session.document
        for clip in self.sequence_clips:
            if clip.layer_id and not next((layer.visible for layer in document.layers if layer.id == clip.layer_id), False):
                continue
            color = QColor(clip.color)
            if clip.kind == "text":
                box = QRectF(24, self.viewport().height() - 112, self.viewport().width() - 48, 88)
                painter.fillRect(box, QColor(12, 17, 22, 205))
                painter.setPen(color)
                painter.drawText(box.adjusted(12, 8, -12, -8), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, clip.text)
            for particle in particles_at(clip, self.sequence_position):
                from src.persistence.project_schema import Point3Record
                point = self.mapFromScene(self._project_position(Point3Record(x=particle.x, y=particle.y, z=0), clip.layer_id or document.layers[0].id))
                color.setAlphaF(particle.opacity * clip.opacity)
                painter.setPen(QPen(color, 1.5))
                painter.setBrush(color)
                if clip.kind == "rain":
                    painter.drawLine(point.x(), point.y(), point.x() - 2, point.y() + int(particle.size))
                else:
                    painter.drawEllipse(point, max(1, int(particle.size)), max(1, int(particle.size)))
        painter.end()


class SceneSequencePanel(QWidget):
    status_message = Signal(str)
    editor_requested = Signal()

    def __init__(self, session, viewport, pages, project_root, language="en", parent=None):
        super().__init__(parent)
        self.setObjectName("scene_studio_timeline")
        self.session, self.viewport, self.pages = session, viewport, pages
        self.project_root = Path(project_root)
        self.language = language
        self.selected_id = None
        self.position = 0.0
        self.pixels_per_second = 28.0
        self.preview = None
        self.players = {}
        self._audio_failures = set()
        self._last_sequence = None
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._tick)
        self.play = QPushButton()
        self.play.setObjectName("scene_sequence_play")
        self.stop_button = QPushButton()
        self.stop_button.setObjectName("scene_sequence_stop")
        self.time_label = QLabel()
        self.duration = spin("scene_sequence_duration", 0.05, 86400, 30)
        self.loop = QCheckBox()
        self.speed = spin("scene_sequence_speed", 0.1, 4, 1)
        self.kind = QComboBox()
        self.add_button = QPushButton()
        self.add_button.setObjectName("scene_sequence_add")
        self.delete_button = QPushButton()
        self.undo_button = QPushButton()
        self.redo_button = QPushButton()
        transport = QHBoxLayout()
        for widget in (self.play, self.stop_button, self.time_label, self.duration, self.loop, self.speed, self.kind, self.add_button, self.delete_button, self.undo_button, self.redo_button):
            transport.addWidget(widget)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addLayout(transport)
        self.scene = QGraphicsScene(self)
        self.view = TimelineView(self.scene)
        self.view.parent_panel = self
        self.view.setObjectName("scene_sequence_tracks")
        self.view.setMinimumHeight(135)
        layout.addWidget(self.view)
        self.editor = QScrollArea()
        self.editor.setWidgetResizable(True)
        self.editor.setObjectName("scene_clip_inspector")
        editor_body = QWidget()
        self.form = QFormLayout(editor_body)
        self.fields = {}
        self.field_labels = {}
        self.name = QLineEdit()
        self.text = QLineEdit()
        self.target = QComboBox()
        self.layer = QComboBox()
        self.color = QLineEdit("#ffffff")
        self.repeat = QCheckBox()
        self.enabled = QCheckBox()
        for key, widget in (("name", self.name), ("target", self.target), ("layer", self.layer), ("text", self.text), ("color", self.color), ("loop", self.repeat), ("enabled", self.enabled)):
            self.field_labels[key] = QLabel()
            self.form.addRow(self.field_labels[key], widget)
        for key, lower, upper in (("start", 0, 86400), ("duration", 0.05, 86400), ("x", -1e6, 1e6), ("y", -1e6, 1e6), ("end_x", -1e6, 1e6), ("end_y", -1e6, 1e6), ("zoom", .001, 1000), ("end_zoom", .001, 1000), ("rotation", -36000, 36000), ("end_rotation", -36000, 36000), ("opacity", 0, 1), ("end_opacity", 0, 1), ("intensity", 0, 10)):
            field = spin("scene_clip_" + key, lower, upper)
            self.fields[key] = field
            self.field_labels[key] = QLabel()
            self.form.addRow(self.field_labels[key], field)
        self.apply_button = QPushButton()
        self.apply_button.setObjectName("scene_clip_apply")
        self.form.addRow(self.apply_button)
        self.editor.setWidget(editor_body)
        self.play.clicked.connect(self.toggle_play)
        self.stop_button.clicked.connect(self.stop_at_start)
        self.add_button.clicked.connect(lambda: self.add_clip(self.kind.currentData()))
        self.delete_button.clicked.connect(self.remove_selected)
        self.undo_button.clicked.connect(self.session.undo)
        self.redo_button.clicked.connect(self.session.redo)
        self.apply_button.clicked.connect(self.apply_clip)
        self.duration.editingFinished.connect(self.change_sequence)
        self.loop.toggled.connect(self.change_sequence)
        self.session.subscribe(self.refresh)
        self.update_language(language)
        self.refresh()

    @property
    def sequence(self):
        return self.session.document.sequence or SceneSequence()

    def update_language(self, language):
        self.language = language
        pt = language == "pt"
        for widget, label in ((self.play, "Pausar" if self.timer.isActive() else "Reproduzir"), (self.stop_button, "Parar"), (self.add_button, "Adicionar"), (self.delete_button, "Excluir clipe"), (self.apply_button, "Aplicar clipe"), (self.loop, "Repetir"), (self.undo_button, "Desfazer"), (self.redo_button, "Refazer")) if pt else ((self.play, "Pause" if self.timer.isActive() else "Play"), (self.stop_button, "Stop"), (self.add_button, "Add"), (self.delete_button, "Delete clip"), (self.apply_button, "Apply clip"), (self.loop, "Loop"), (self.undo_button, "Undo"), (self.redo_button, "Redo")):
            widget.setText(label)
            widget.setToolTip(label)
        self.duration.setToolTip("Duração da cena (segundos)" if pt else "Scene duration (seconds)")
        self.speed.setToolTip("Velocidade de reprodução" if pt else "Playback speed")
        current = self.kind.currentData()
        self.kind.clear()
        for name, kind in zip(NAMES_PT if pt else NAMES_EN, KINDS):
            self.kind.addItem(name, kind)
        self.kind.setCurrentIndex(max(0, self.kind.findData(current)))
        labels = ("Nome", "Objeto", "Moldura", "Texto", "Cor", "Repetição do efeito", "Ativo", "Início (s)", "Duração (s)", "X inicial", "Y inicial", "X final", "Y final", "Zoom / escala inicial", "Zoom / escala final", "Rotação inicial", "Rotação final", "Opacidade / volume", "Opacidade final", "Intensidade") if pt else ("Name", "Object", "Frame", "Text", "Color", "Effect loop", "Enabled", "Start (s)", "Duration (s)", "Start X", "Start Y", "End X", "End Y", "Start zoom / scale", "End zoom / scale", "Start rotation", "End rotation", "Opacity / volume", "End opacity", "Intensity")
        for widget, label in zip(self.field_labels.values(), labels):
            widget.setText(label)

    def _error(self, exc):
        self.status_message.emit(("Sequência não alterada. Verifique duração, referências e sobreposição de clipes: " if self.language == "pt" else "Sequence unchanged. Check duration, references and overlapping clips: ") + str(exc))

    def change_sequence(self):
        try:
            data = self.sequence.model_dump()
            data.update(duration=self.duration.value(), loop=self.loop.isChecked())
            set_sequence(self.session, SceneSequence.model_validate(data))
        except (ValueError, OSError) as exc:
            self._error(exc)
            self.refresh()

    def add_clip(self, kind):
        self.stop()
        try:
            values = dict(id=uuid4().hex, name=(NAMES_PT if self.language == "pt" else NAMES_EN)[KINDS.index(kind)], kind=kind, start=min(self.position, max(0, self.sequence.duration - .05)), duration=min(5, self.sequence.duration - self.position), loop=kind in {"rain", "snow", "dust", "fire", "audio"}, layer_id=self.viewport._destination_layer())
            if kind == "camera":
                camera = self.session.document.camera
                values.update(x=camera.position.x, y=camera.position.y, end_x=camera.position.x + 200, end_y=camera.position.y, zoom=camera.zoom, end_zoom=camera.zoom, rotation=camera.rotation, end_rotation=camera.rotation)
            if kind == "motion":
                obj = next((o for o in self.session.document.objects if o.id == self.session.selection.primary), None)
                if obj is None:
                    raise ValueError("Selecione o objeto a animar" if self.language == "pt" else "Select an object to animate")
                values.update(target_id=obj.id, x=obj.transform.position.x, y=obj.transform.position.y, end_x=obj.transform.position.x + 100, end_y=obj.transform.position.y, zoom=obj.transform.scale.x, end_zoom=obj.transform.scale.x, rotation=obj.transform.rotation.z, end_rotation=obj.transform.rotation.z)
            if kind == "text":
                values["text"] = "Sua história começa aqui" if self.language == "pt" else "Your story starts here"
            if kind == "fire":
                values["color"] = "#ff9c40"
            if kind == "audio":
                path, _ = QFileDialog.getOpenFileName(self, "Adicionar áudio" if self.language == "pt" else "Add audio", "", "Audio (*.wav *.mp3 *.ogg *.flac)")
                if not path:
                    return
                prepared = prepare_scene_asset(path, self.project_root, allow_audio=True)
                asset = AssetReferenceRecord(id="audio_" + prepared.sha256[:20], path=prepared.path, sha256=prepared.sha256, source_path=prepared.source_path)
                values["asset_id"] = asset.id
            clip = SceneClip(**values)
            sequence = SceneSequence.model_validate({**self.sequence.model_dump(), "clips": [c.model_dump() for c in self.sequence.clips] + [clip.model_dump()]})
            if kind == "audio":
                def operation():
                    if asset.id not in {a.id for a in self.session.document.assets}:
                        self.session.model.add_asset(asset)
                    self.session.model._replace(sequence=sequence)
                self.session.apply(operation, "Add audio clip")
            else:
                set_sequence(self.session, sequence)
            self.select_clip(clip.id)
        except (ValueError, OSError) as exc:
            self._error(exc)

    def select_clip(self, clip_id, *, redraw=True):
        self.selected_id = clip_id
        clip = next((c for c in self.sequence.clips if c.id == clip_id), None)
        if clip:
            relevant = {"name", "enabled", "start", "duration"}
            if clip.kind in {"camera", "motion"}:
                relevant.update({"x", "y", "end_x", "end_y", "zoom", "end_zoom"})
            if clip.kind == "camera":
                relevant.update({"rotation", "end_rotation"})
            if clip.kind == "motion":
                relevant.update({"target", "rotation", "end_rotation", "opacity", "end_opacity"})
            if clip.kind in {"light", "rain", "snow", "dust", "fire"}:
                relevant.update({"layer", "x", "y", "zoom", "color", "intensity", "loop", "opacity"})
            if clip.kind == "audio":
                relevant.update({"loop", "opacity"})
            if clip.kind == "text":
                relevant.update({"text", "color"})
            for key, label in self.field_labels.items():
                self.form.setRowVisible(label, key in relevant)
            self.name.setText(clip.name)
            self.text.setText(clip.text)
            self.color.setText(clip.color)
            self.repeat.setChecked(clip.loop)
            self.enabled.setChecked(clip.enabled)
            self.target.clear()
            self.target.addItem("—", None)
            for obj in self.session.document.objects:
                self.target.addItem(obj.id, obj.id)
            self.target.setCurrentIndex(max(0, self.target.findData(clip.target_id)))
            self.layer.clear()
            self.layer.addItem("—", None)
            for layer in self.session.document.layers:
                self.layer.addItem(layer.name, layer.id)
            self.layer.setCurrentIndex(max(0, self.layer.findData(clip.layer_id)))
            for key, field in self.fields.items():
                field.setValue(getattr(clip, key))
            self.editor_requested.emit()
        self.editor.setEnabled(clip is not None)
        if redraw:
            self.draw_timeline()

    def apply_clip(self):
        values = {key: field.value() for key, field in self.fields.items()}
        values.update(name=self.name.text(), text=self.text.text(), color=self.color.text(), loop=self.repeat.isChecked(), enabled=self.enabled.isChecked(), target_id=self.target.currentData(), layer_id=self.layer.currentData())
        self.change_clip(self.selected_id, values)

    def change_clip(self, clip_id, changes):
        self.stop()
        try:
            data = self.sequence.model_dump()
            data["clips"] = [{**c.model_dump(), **changes} if c.id == clip_id else c.model_dump() for c in self.sequence.clips]
            set_sequence(self.session, SceneSequence.model_validate(data))
        except ValueError as exc:
            self._error(exc)
            self.draw_timeline()

    def remove_selected(self):
        self.stop()
        sequence = self.sequence.model_copy(update={"clips": [c for c in self.sequence.clips if c.id != self.selected_id]})
        set_sequence(self.session, sequence)

    def refresh(self):
        sequence = self.sequence
        if sequence != self._last_sequence:
            self.stop()
            self._last_sequence = sequence.model_copy(deep=True)
        self.duration.setValue(sequence.duration)
        self.loop.blockSignals(True)
        self.loop.setChecked(sequence.loop)
        self.loop.blockSignals(False)
        self.undo_button.setEnabled(self.session.can_undo)
        self.redo_button.setEnabled(self.session.can_redo)
        self.select_clip(self.selected_id)

    def draw_timeline(self):
        self.scene.clear()
        width = max(720, 150 + self.sequence.duration * self.pixels_per_second)
        used = list(dict.fromkeys(c.kind for c in self.sequence.clips)) or ["camera", "audio", "text"]
        for row, kind in enumerate(used):
            self.scene.addRect(0, 26 + row * 31, width, 31, QPen(QColor("#394552")), QBrush(QColor("#1d252e")))
            label = self.scene.addText((NAMES_PT if self.language == "pt" else NAMES_EN)[KINDS.index(kind)])
            label.setDefaultTextColor(QColor("#e0e8ef"))
            label.setPos(4, 26 + row * 31)
            for clip in self.sequence.clips:
                if clip.kind == kind:
                    self.scene.addItem(ClipBlock(self, clip, row))
        step = max(1, int(self.sequence.duration / 20))
        for second in range(0, int(self.sequence.duration) + 1, step):
            x = 150 + second * self.pixels_per_second
            label = self.scene.addText(f"{second // 60}:{second % 60:02d}")
            label.setDefaultTextColor(QColor("#bdcad8"))
            label.setPos(x, 0)
        self.scene.setSceneRect(0, 0, width, 28 + len(used) * 31)
        self.playhead = self.scene.addLine(0, 0, 0, self.scene.height(), QPen(QColor("#55d5e8"), 2))
        self._display_time()

    def _display_time(self):
        self.time_label.setText(f"{self.position:06.2f} / {self.sequence.duration:.2f} s")
        if hasattr(self, "playhead"):
            self.playhead.setX(150 + self.position * self.pixels_per_second)

    def toggle_play(self):
        if self.timer.isActive():
            self.timer.stop()
            self._pause_audio()
        else:
            if self.position >= self.sequence.duration:
                self.position = 0
            self.last_tick = time.monotonic()
            self.timer.start()
            self.seek(self.position)
        self.update_language(self.language)

    def _tick(self):
        now = time.monotonic()
        position = self.position + (now - self.last_tick) * self.speed.value()
        self.last_tick = now
        if position >= self.sequence.duration:
            if self.sequence.loop:
                position %= self.sequence.duration
            else:
                position = self.sequence.duration
                self.timer.stop()
                self._pause_audio()
                self.update_language(self.language)
        self.seek(position)

    def seek(self, position):
        self.position = min(max(0, position), self.sequence.duration)
        if self.preview is None:
            preview_session = SceneAuthoringSession(SceneAuthoringModel(self.session.document.model_copy(deep=True)))
            self.preview = SequenceViewport(preview_session, self.project_root, self.pages)
            self.preview.update_language(self.language)
            self.preview._geometry = dict(self.viewport._geometry)
            self.preview.set_preview_enabled(True)
            self.preview.set_authoring_enabled(False)
            self.preview.set_overlay_visible(False)
            self.pages.addWidget(self.preview)
        self.preview.session.model.document = evaluate_sequence(self.session.document, self.position)
        self.preview.sequence_clips = active_clips(self.sequence, self.position)
        self.preview.sequence_position = self.position
        self.preview.session._notify()
        self.pages.setCurrentWidget(self.preview)
        self.preview.viewport().update()
        self._sync_audio()
        self._display_time()

    def _pause_audio(self):
        for player, _output in self.players.values():
            player.pause()

    def _sync_audio(self):
        active = {c.id: c for c in active_clips(self.sequence, self.position) if c.kind == "audio"}
        for clip_id in list(self.players):
            if clip_id not in active:
                self.players[clip_id][0].stop()
        for clip_id, clip in active.items():
            if clip_id in self._audio_failures:
                continue
            if clip_id not in self.players:
                asset = next((a for a in self.session.document.assets if a.id == clip.asset_id), None)
                if asset is None:
                    self._audio_failures.add(clip_id)
                    self.status_message.emit(
                        (
                            "Áudio ausente/alterado; revincule na Biblioteca: asset não encontrado"
                            if self.language == "pt"
                            else "Missing/changed audio; relink in Library: asset not found"
                        )
                    )
                    continue
                path, issue = resolve_scene_asset(asset, self.project_root)
                if path is None:
                    self._audio_failures.add(clip_id)
                    self.status_message.emit(("Áudio ausente/alterado; revincule na Biblioteca: " if self.language == "pt" else "Missing/changed audio; relink in Library: ") + str(issue))
                    continue
                from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
                output = QAudioOutput(self)
                player = QMediaPlayer(self)
                player.setAudioOutput(output)
                player.errorOccurred.connect(lambda _error, message: self.status_message.emit(("Falha no áudio; verifique o arquivo: " if self.language == "pt" else "Audio failed; check the file: ") + message))
                player.setSource(QUrl.fromLocalFile(str(path)))
                self.players[clip_id] = (player, output)
            player, output = self.players[clip_id]
            elapsed_ms = int((self.position - clip.start) * 1000)
            if clip.loop and player.duration() > 0:
                elapsed_ms %= player.duration()
            output.setVolume(clip.opacity)
            player.setPlaybackRate(self.speed.value())
            if abs(player.position() - elapsed_ms) > 100 or not self.timer.isActive():
                player.setPosition(elapsed_ms)
            if self.timer.isActive():
                player.play()
            else:
                player.pause()

    def stop(self):
        self.timer.stop()
        for player, output in self.players.values():
            player.stop()
            player.deleteLater()
            output.deleteLater()
        self.players.clear()
        self._audio_failures.clear()
        if self.preview is not None:
            self.pages.setCurrentWidget(self.viewport)
            self.pages.removeWidget(self.preview)
            self.preview.deleteLater()
            self.preview = None
        self.update_language(self.language)

    def stop_at_start(self):
        self.stop()
        self.position = 0
        self._display_time()
