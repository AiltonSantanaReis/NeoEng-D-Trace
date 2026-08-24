# src/ui/collision_panel.py
"""
Collision panel for static overlap testing.
"""

import copy
from typing import Dict, List

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.logger import logger
from src.core.polygon_validation import is_valid_polygon
from src.ui.icon_library import configure_widget


class CollisionPanel(QWidget):
    """
    Panel providing controls for static collision testing and management.
    """

    batch_test_requested = Signal()
    export_collisions_requested = Signal()
    auto_generate_requested = Signal()

    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.collision_results: List[Dict] = []
        self.collision_manager = None

        self._setup_ui()
        if hasattr(self.scene, "subscribe"):
            self.scene.subscribe(self._on_scene_changed)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Static Collision Testing")
        title.setObjectName("panel_section_title")
        layout.addWidget(title)

        button_layout = QVBoxLayout()

        self.batch_test_btn = QPushButton("Batch Test")
        configure_widget(self.batch_test_btn, "collision_test")
        self.batch_test_btn.setIconSize(QSize(20, 20))
        self.batch_test_btn.setToolTip(
            "Run collision detection on all collision shapes"
        )
        self.batch_test_btn.clicked.connect(self._on_batch_test)

        self.export_btn = QPushButton("Export Collisions")
        configure_widget(self.export_btn, "export")
        self.export_btn.setIconSize(QSize(20, 20))
        self.export_btn.setToolTip("Export collision results to JSON file")
        self.export_btn.clicked.connect(self._on_export_collisions)

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItem("Outline (legacy)", "outline")
        self.strategy_combo.addItem("Convex hull", "convex_hull")
        self.strategy_combo.addItem("Convex decomposition", "convex_decomposition")
        self.strategy_combo.setToolTip(
            "Choose the collider representation used by the physics manager"
        )

        self.auto_gen_btn = QPushButton("Auto-Generate from Scene Objects")
        configure_widget(self.auto_gen_btn, "collision_auto_generate")
        self.auto_gen_btn.setIconSize(QSize(20, 20))
        self.auto_gen_btn.setToolTip(
            "Generate collision shapes from current scene polygons"
        )
        self.auto_gen_btn.clicked.connect(self._on_auto_generate)

        self.action_toolbar = QToolBar()
        self.action_toolbar.setObjectName("collision_action_toolbar")
        self.action_toolbar.setMovable(False)
        self.action_toolbar.setFloatable(False)
        self.action_toolbar.setIconSize(QSize(16, 16))
        self.action_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        from src.ui.icon_library import configure_action

        for key, button, tooltip in (
            (
                "collision_test",
                self.batch_test_btn,
                "Run collision detection on all collision shapes",
            ),
            ("export", self.export_btn, "Export collision results to JSON file"),
            (
                "collision_auto_generate",
                self.auto_gen_btn,
                "Generate collision shapes from current scene polygons",
            ),
        ):
            action = self.action_toolbar.addAction(button.text())
            configure_action(
                action,
                key,
                text=button.text(),
                tooltip=tooltip,
                accessible_name=button.text(),
            )
            action.setProperty("commandKey", key)
            action.triggered.connect(button.click)

        for button in (self.batch_test_btn, self.export_btn, self.auto_gen_btn):
            button.setVisible(False)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        button_layout.addWidget(self.action_toolbar)
        button_layout.addWidget(self.strategy_combo)
        layout.addLayout(button_layout)

        self.validation_text = QLabel("Validation: no collision shapes")
        self.validation_text.setObjectName("collision_validation_summary")
        self.validation_text.setWordWrap(True)
        self.validation_text.setToolTip(
            "Vertex count, convexity and topology for every collider"
        )
        layout.addWidget(self.validation_text)

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

    def _update_validation_display(self) -> None:
        """Show deterministic collider diagnostics required by the inspector."""

        if not self.scene.collision_shapes:
            self.validation_text.setText("Validation: no collision shapes")
            return
        rows = []
        for object_id, shape in self.scene.collision_shapes.items():
            points = [tuple(point) for point in shape]
            convex = self._is_convex(points)
            topology = "simple" if is_valid_polygon(list(points)) else "invalid"
            rows.append(
                f"{object_id}: vertices={len(points)} | "
                f"convex={'yes' if convex else 'no'} | topology={topology}"
            )
        self.validation_text.setText("Validation: " + " ; ".join(rows))

    @staticmethod
    def _is_convex(points) -> bool:
        if len(points) < 3:
            return False
        signs = []
        for index, current in enumerate(points):
            previous = points[index - 1]
            following = points[(index + 1) % len(points)]
            cross = (current[0] - previous[0]) * (following[1] - current[1]) - (
                current[1] - previous[1]
            ) * (following[0] - current[0])
            if abs(cross) > 1e-9:
                signs.append(cross > 0)
        return bool(signs) and all(value == signs[0] for value in signs)

    def _build_context_menu(self) -> QMenu:
        menu = QMenu(self)
        for toolbar_action in self.action_toolbar.actions():
            action = menu.addAction(toolbar_action.icon(), toolbar_action.text())
            action.setToolTip(toolbar_action.toolTip())
            action.setProperty("commandKey", toolbar_action.property("commandKey"))
            action.setEnabled(toolbar_action.isEnabled())
            action.triggered.connect(toolbar_action.trigger)
        return menu

    def _show_context_menu(self, position) -> None:
        self._build_context_menu().exec(self.mapToGlobal(position))

    def set_collision_manager(self, collision_manager):
        self.collision_manager = collision_manager
        self._sync_collision_manager_from_scene()

    def set_physics_manager(self, physics_manager):
        """Compatibility adapter for historical callers."""
        self.set_collision_manager(physics_manager)

    def _on_scene_changed(self):
        self._sync_collision_manager_from_scene()
        self._update_validation_display()

    def _sync_collision_manager_from_scene(self) -> bool:
        if self.collision_manager is None:
            return True

        previous = {
            object_id: copy.deepcopy(collision_object.shape)
            for object_id, collision_object in self.collision_manager.objects.items()
        }
        try:
            self.collision_manager.clear()
            for object_id, shape in self.scene.collision_shapes.items():
                parts = getattr(self.scene, "collision_parts", {}).get(object_id, [])
                if parts:
                    for part_index, part in enumerate(parts):
                        self.collision_manager.register(
                            f"{object_id}#part{part_index}",
                            copy.deepcopy(part),
                            metadata={"parent_id": object_id, "part_index": part_index},
                        )
                else:
                    self.collision_manager.register(object_id, copy.deepcopy(shape))
            self._update_validation_display()
            return True
        except Exception as exc:
            logger.error(
                "Failed to synchronize physics collision cache (%s)",
                type(exc).__name__,
            )
            try:
                self.collision_manager.clear()
                for object_id, shape in previous.items():
                    self.collision_manager.register(object_id, shape)
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

        stats_text = f"""Static Collision Statistics:
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
        if not self.collision_manager:
            QMessageBox.warning(
                self, "Error", "Static collision manager not available."
            )
            return

        # Synchronize the derived physics cache without creating history.
        if not self.collision_manager.objects and self.scene.collision_shapes:
            if not self._sync_collision_manager_from_scene():
                QMessageBox.critical(
                    self,
                    "Error",
                    "Physics collision cache synchronization failed.",
                )
                return

        if not self.collision_manager.objects:
            QMessageBox.information(
                self,
                "Info",
                "No collision shapes registered. Use Auto-Generate first.",
            )
            return

        try:
            results = self.collision_manager.batch_test()

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

            stats = self.collision_manager.get_stats()
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

            strategy = self.strategy_combo.currentData() or "outline"
            command = AutoGenerateCollisionShapesCommand(strategy=strategy)
            result = manager.execute(command, self.scene)
            if not result.changed:
                message = result.message or "Collision generation was not applied."
                if result.status is CommandStatus.FAILED:
                    QMessageBox.critical(self, "Error", message)
                elif result.status is CommandStatus.REJECTED:
                    QMessageBox.warning(self, "Error", message)
                else:
                    self._sync_collision_manager_from_scene()
                    QMessageBox.information(self, "Info", message)
                return

            if not self._sync_collision_manager_from_scene():
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
