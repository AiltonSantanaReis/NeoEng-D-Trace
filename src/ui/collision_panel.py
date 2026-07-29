# src/ui/collision_panel.py
"""
Collision Panel for Physics Testing
"""

import json
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

        # Sincroniza Physics Manager com Scene shapes se necessário
        if not self.physics_manager.objects and self.scene.collision_shapes:
            self._on_auto_generate()

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

        try:
            export_data = {
                "collision_shapes": self.scene.collision_shapes,
                "collision_results": self.collision_results,
                "statistics": (
                    self.physics_manager.get_stats() if self.physics_manager else {}
                ),
            }

            json_str = json.dumps(export_data, indent=2)

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Collision Export")
            msg_box.setText("Collision data exported to JSON:")
            msg_box.setDetailedText(json_str)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()

            self.export_collisions_requested.emit()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

    def _on_auto_generate(self):
        try:
            collision_shapes = {}
            count = 0

            # Limpa o physics manager para evitar duplicatas
            if self.physics_manager:
                self.physics_manager.clear()

            for obj_id, obj in self.scene.objects.items():
                if obj.polygon and len(obj.polygon) >= 3:
                    # Converte para float para física
                    shape = [(float(x), float(y)) for x, y in obj.polygon]
                    collision_shapes[obj_id] = shape

                    # REGISTRA NO PHYSICS MANAGER (CRÍTICO)
                    if self.physics_manager:
                        self.physics_manager.register(obj_id, shape)

                    count += 1

            if count == 0:
                QMessageBox.information(
                    self,
                    "Info",
                    "No valid polygons found in scene to generate collision shapes.",
                )
                return

            # Atualiza o modelo de dados da cena
            self.scene.collision_shapes = collision_shapes

            QMessageBox.information(
                self,
                "Success",
                f"Generated and registered {count} collision shapes from scene objects.",
            )

            self.auto_generate_requested.emit()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Auto-generation failed: {str(e)}")
