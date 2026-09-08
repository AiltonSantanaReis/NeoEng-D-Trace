from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.core.navmesh_2d import (
    NavMeshBake,
    NavMeshSource,
    NavObstacle,
    NavRegion,
    bake_navmesh,
    find_path,
)
from src.persistence.navmesh_io import load_navmesh, save_navmesh


class NavMeshPanel(QWidget):
    """Small, explicit E06 authoring surface for source/bake/path inspection."""

    status_message = Signal(str)

    def __init__(self, project_root: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project_root = project_root
        self.source = NavMeshSource()
        self.bake: NavMeshBake | None = None
        self.title_label = QLabel(self)
        self.summary_label = QLabel(self)
        self.status_label = QLabel(self)
        self.region_button = QPushButton(self)
        self.obstacle_button = QPushButton(self)
        self.bake_button = QPushButton(self)
        self.save_button = QPushButton(self)
        self.open_button = QPushButton(self)
        self.region_button.clicked.connect(self.add_region)
        self.obstacle_button.clicked.connect(self.add_obstacle)
        self.bake_button.clicked.connect(self.bake_source)
        self.save_button.clicked.connect(self.save_document)
        self.open_button.clicked.connect(self.open_document)
        actions = QHBoxLayout()
        for button in (
            self.region_button,
            self.obstacle_button,
            self.bake_button,
            self.save_button,
            self.open_button,
        ):
            actions.addWidget(button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.summary_label)
        layout.addLayout(actions)
        layout.addWidget(self.status_label)
        self.update_language("pt")

    @property
    def document_path(self) -> Path:
        return self.project_root / "assets" / "navmesh" / "scenario.navmesh.json"

    def _refresh(self) -> None:
        bake_state = (
            "bake obsoleto"
            if self.bake and self.bake.is_obsolete(self.source)
            else ("bake disponível" if self.bake else "sem bake")
        )
        self.summary_label.setText(
            f"Regiões: {len(self.source.regions)} · Obstáculos: {len(self.source.obstacles)} · {bake_state}"
        )

    def add_region(self) -> None:
        if not self.source.regions:
            self.source.regions.append(NavRegion("surface-1", (0, 0, 128, 64)))
            self.source.touch()
        self._refresh()
        self.status_message.emit("Região caminhável criada")

    def add_obstacle(self) -> None:
        if not self.source.regions:
            self.add_region()
        if not self.source.obstacles:
            self.source.obstacles.append(NavObstacle("obstacle-1", (48, 0, 16, 32)))
            self.source.touch()
        self._refresh()
        self.status_message.emit("Obstáculo criado")

    def bake_source(self) -> None:
        self.bake = bake_navmesh(self.source)
        path = find_path(self.source, self.bake, (8, 24), (112, 24))
        self._refresh()
        self.status_message.emit(f"Bake concluído · caminho: {len(path.points)} pontos")

    def save_document(self) -> None:
        save_navmesh(self.source, self.document_path)
        self.status_message.emit(f"NavMesh salva: {self.document_path.name}")

    def open_document(self) -> None:
        self.source = load_navmesh(self.document_path)
        self.bake = None
        self._refresh()
        self.status_message.emit("NavMesh reaberta; bake precisa ser reexecutado")

    def update_language(self, language: str) -> None:
        if language == "pt":
            self.title_label.setText("NavMesh 2D / Navegação")
            self.region_button.setText("Região")
            self.obstacle_button.setText("Obstáculo")
            self.bake_button.setText("Bake")
            self.save_button.setText("Salvar")
            self.open_button.setText("Reabrir")
        else:
            self.title_label.setText("2D NavMesh / Navigation")
            self.region_button.setText("Region")
            self.obstacle_button.setText("Obstacle")
            self.bake_button.setText("Bake")
            self.save_button.setText("Save")
            self.open_button.setText("Reopen")
        self._refresh()


__all__ = ["NavMeshPanel"]
