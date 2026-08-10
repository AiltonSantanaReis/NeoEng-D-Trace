# src/ui/collision_panel.py
"""
Collision Panel for Physics Testing
"""

import copy
from typing import Dict, List

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.logger import logger


class CollisionPanel(QWidget):
    """
    Panel providing controls for physics collision testing and management.
    """

    batch_test_requested = Signal()
    export_collisions_requested = Signal()
    auto_generate_requested = Signal()

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.collision_results: List[Dict] = []
        self.physics_manager = None

        self._setup_ui()
        if hasattr(self.scene, "subscribe"):
            self.scene.subscribe(self._on_scene_changed)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Physics Collision Testing")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        button_layout = QVBoxLayout()

        self.batch_test_btn = QPushButton("🔍 Batch Test")
        self.batch_test_btn.setToolTip(
            "Run collision detection on all collision shapes"
        )
        self.batch_test_btn.clicked.connect(self._on_batch_test)
        button_layout.addWidget(self.batch_test_btn)

        self.export_btn = QPushButton("📤 Export Collisions")
        self.export_btn.setToolTip("Export collision results to JSON file")
        self.export_btn.clicked.connect(self._on_export_collisions)
        button_layout.addWidget(self.export_btn)

        self.auto_gen_btn = QPushButton("🤖 Auto-Generate from Scene Objects")
        self.auto_gen_btn.setToolTip(
            "Generate collision shapes from current scene polygons"
        )
        self.auto_gen_btn.clicked.connect(self._on_auto_generate)
        button_layout.addWidget(self.auto_gen_btn)

        layout.addLayout(button_layout)

        results_group = QGroupBox("Collision Results")
        results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        self.results_text.setPlainText("No collision tests run yet.")
        results_layout.addWidget(self.results_text)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout()

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        self.stats_text.setPlainText("No statistics available.")
        stats_layout.addWidget(self.stats_text)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        layout.addStretch()

    def set_physics_manager(self, physics_manager):
        self.physics_manager = physics_manager
        self._sync_physics_manager_from_scene()

    def _on_scene_changed(self):
        self._sync_physics_manager_from_scene()

    def _sync_physics_manager_from_scene(self) -> bool:
        if self.physics_manager is None:
            return True

        previous = {
            object_id: copy.deepcopy(physics_object.shape)
            for object_id, physics_object in self.physics_manager.objects.items()
        }
        try:
            self.physics_manager.clear()
            for object_id, shape in self.scene.collision_shapes.items():
                self.physics_manager.register(object_id, copy.deepcopy(shape))
            return True
        except Exception as exc:
            logger.error(
                "Failed to synchronize physics collision cache (%s)",
                type(exc).__name__,
            )
            try:
                self.physics_manager.clear()
                for object_id, shape in previous.items():
                    self.physics_manager.register(object_id, shape)
            except Exception as restore_exc:
                logger.error(
                    "Failed to restore physics collision cache (%s)",
                    type(restore_exc).__name__,
                )
            return False

    def update_collision_results(self, results: List[Dict]):
        self.collision_results = results
        self._update_results_display()

    def update_statistics(self, stats: Dict):
        if not stats:
            self.stats_text.setPlainText("No statistics available.")
            return

        stats_text = f"""Physics Statistics:
• Total Objects: {stats.get('total_objects', 0)}
• Grid Cell Size: {stats.get('grid_cell_size', 0)}
• Occupied Cells: {stats.get('occupied_cells', 0)}
• Avg Objects/Cell: {stats.get('avg_objects_per_cell', 0.0):.2f}
• Total Tests: {stats.get('total_collision_tests', 0)}
• Collisions Found: {stats.get('total_collisions_found', 0)}
• Collision Rate: {stats.get('collision_rate', 0.0):.1%}
"""
        self.stats_text.setPlainText(stats_text)

    def _update_results_display(self):
        if not self.collision_results:
            self.results_text.setPlainText("No collision results.")
            return

        results_text = (
            f"Collision Test Results " f"({len(self.collision_results)} tests):\n\n"
        )

        collision_count = 0
        for i, result in enumerate(self.collision_results):
            obj1 = result.get("obj1_id", "Unknown")
            obj2 = result.get("obj2_id", "Unknown")
            colliding = result.get("colliding", False)

            status = "COLLISION ⚠️" if colliding else "No Collision ✓"
            results_text += f"{i+1}. {obj1} ↔ {obj2}: {status}\n"

            if colliding:
                collision_count += 1
                mtv = result.get("mtv")
                if mtv:
                    results_text += f"   MTV: ({mtv[0]:.2f}, {mtv[1]:.2f})\n"

        results_text += (
            f"\nSummary: {collision_count} collisions detected "
            f"out of {len(self.collision_results)} tests."
        )
        self.results_text.setPlainText(results_text)

    def _on_batch_test(self):
        if not self.physics_manager:
            QMessageBox.warning(self, "Error", "Physics manager not available.")
            return

        # Synchronize the derived physics cache without creating history.
        if not self.physics_manager.objects and self.scene.collision_shapes:
            if not self._sync_physics_manager_from_scene():
                QMessageBox.critical(
                    self,
                    "Error",
                    "Physics collision cache synchronization failed.",
                )
                return

        if not self.physics_manager.objects:
            QMessageBox.information(
                self,
                "Info",
                "No physics objects registered. Use Auto-Generate first.",
            )
            return

        try:
            results = self.physics_manager.batch_test()

            self.update_collision_results(
                [
                    {
                        "obj1_id": r.obj1_id,
                        "obj2_id": r.obj2_id,
                        "colliding": r.colliding,
                        "mtv": r.mtv,
                    }
                    for r in results
                ]
            )

            stats = self.physics_manager.get_stats()
            self.update_statistics(stats)

            self.batch_test_requested.emit()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Batch test failed: {str(e)}")

    def _on_export_collisions(self):
        if not self.collision_results:
            QMessageBox.information(
                self,
                "Info",
                "No collision results to export. Run Batch Test first.",
            )
            return

        self.export_collisions_requested.emit()

    def _on_auto_generate(self):
        manager = getattr(self.scene, "cmd", None)
        if manager is None:
            QMessageBox.warning(
                self,
                "Error",
                "Undo/Redo command history is unavailable.",
            )
            return

        try:
            from src.core.commands import (
                AutoGenerateCollisionShapesCommand,
                CommandStatus,
            )

            command = AutoGenerateCollisionShapesCommand()
            result = manager.execute(command, self.scene)
            if not result.changed:
                message = result.message or "Collision generation was not applied."
                if result.status is CommandStatus.FAILED:
                    QMessageBox.critical(self, "Error", message)
                elif result.status is CommandStatus.REJECTED:
                    QMessageBox.warning(self, "Error", message)
                else:
                    self._sync_physics_manager_from_scene()
                    QMessageBox.information(self, "Info", message)
                return

            if not self._sync_physics_manager_from_scene():
                QMessageBox.critical(
                    self,
                    "Error",
                    "Collision shapes were updated, but the physics cache "
                    "could not be synchronized.",
                )
                return

            QMessageBox.information(
                self,
                "Success",
                "Generated and registered "
                f"{command.generated_count} collision shapes from scene objects.",
            )
            self.auto_generate_requested.emit()
        except Exception as exc:
            logger.error(
                "Collision auto-generation failed (%s)",
                type(exc).__name__,
            )
            QMessageBox.critical(
                self,
                "Error",
                f"Auto-generation failed: {str(exc)}",
            )
