# src/ui/side_panel.py
from PySide6.QtCore import QSignalBlocker, QSize, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QInputDialog,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.commands import (
    CommandStatus,
    DeleteObjectCommand,
    RenameObjectCommand,
    ToggleCollisionCommand,
    UpdatePolygonCommand,
)
from src.core.logger import logger
from src.core.transform_gesture import (
    TransformObjectsCommand,
    capture_transform_state,
    transformed_snapshot,
)
from src.core.validation_events import object_token, record_validation_event
from src.ui.error_presentation import show_p2d05_error
from src.utils.selection_tools import (
    expand_contract_polygon,
    invert_selection,
    polygon_to_mask,
)


class SidePanel(QWidget):
    def __init__(self, scene, canvas, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.canvas = canvas
        self._last_validation_selection_marker = None

        self.list = QListWidget()
        self.list.setObjectName("scene_objects_list")
        self.list.setAccessibleName("Scene objects list")
        self.list.setAccessibleDescription("Select an object to inspect or edit it")
        self.search_input = QLineEdit()
        self.search_input.setObjectName("objects_search")
        self.search_input.setPlaceholderText("Search objects")
        self.search_input.setAccessibleName("Search scene objects")
        self.search_input.setAccessibleDescription("Filter scene objects by name or ID")
        self.search_input.setToolTip("Filter objects by name or ID")
        self.search_input.textChanged.connect(self.refresh)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_context_menu)

        # --- Botões ---
        self.btn_rename = QPushButton("Rename")
        self.btn_delete = QPushButton("Delete")

        self.btn_expand = QPushButton("Expand")
        self.btn_contract = QPushButton("Contract")
        self.btn_invert = QPushButton("Invert")

        # Botão de forma de colisão
        self.btn_collision = QPushButton("Collision: OFF")

        self.transform_group = QGroupBox("Transform")
        self.position_x = self._transform_spin(-1_000_000.0, 1_000_000.0)
        self.position_y = self._transform_spin(-1_000_000.0, 1_000_000.0)
        self.position_z = self._transform_spin(-1_000_000.0, 1_000_000.0)
        self.rotation_x = self._transform_spin(-360_000.0, 360_000.0)
        self.rotation_y = self._transform_spin(-360_000.0, 360_000.0)
        self.rotation_z = self._transform_spin(-360_000.0, 360_000.0)
        self.scale_x = self._transform_spin(0.001, 1000.0, 0.1)
        self.scale_y = self._transform_spin(0.001, 1000.0, 0.1)
        self.scale_z = self._transform_spin(0.001, 1000.0, 0.1)
        self.pivot_x = self._transform_spin(0.0, 1.0, 0.01)
        self.pivot_y = self._transform_spin(0.0, 1.0, 0.01)
        self.snap_enabled = QCheckBox("Snap vertices to grid")
        self.snap_enabled.setObjectName("objects_snap_enabled")
        self.snap_enabled.toggled.connect(
            lambda enabled: self.canvas.set_vertex_snapping(enabled, grid_size=16)
        )
        self.metadata_label = QLabel("No object selected")
        self.metadata_label.setObjectName("objects_metadata")
        transform_form = QFormLayout(self.transform_group)
        transform_form.addRow("Position X", self.position_x)
        transform_form.addRow("Position Y", self.position_y)
        transform_form.addRow("Position Z", self.position_z)
        transform_form.addRow("Rotation X", self.rotation_x)
        transform_form.addRow("Rotation Y", self.rotation_y)
        transform_form.addRow("Rotation Z", self.rotation_z)
        transform_form.addRow("Scale X", self.scale_x)
        transform_form.addRow("Scale Y", self.scale_y)
        transform_form.addRow("Scale Z", self.scale_z)
        transform_form.addRow("Pivot X", self.pivot_x)
        transform_form.addRow("Pivot Y", self.pivot_y)
        transform_form.addRow(self.snap_enabled)
        self.btn_apply_transform = QPushButton("Apply Transform")
        self.btn_apply_transform.setObjectName("apply_transform")
        transform_form.addRow(self.btn_apply_transform)
        self.btn_collision.setCheckable(True)
        self.btn_collision.setObjectName("collision_toggle")

        self.slider_label = QLabel("Expand/Contract: 0 px")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(-50)
        self.slider.setMaximum(50)
        self.slider.setValue(0)
        self.btn_apply = QPushButton("Apply")
        self.btn_cancel = QPushButton("Cancel")

        self.btn_export = QPushButton("Export Mask")
        self.btn_export_now = QPushButton("Export Sprite")

        # Keep legacy QPushButtons as stable command handles. The visible
        # presentation uses compact toolbars so the inspector remains usable
        # at compact resolutions without removing any command.
        from src.ui.icon_library import configure_action

        self.properties_action_toolbar = self._build_action_toolbar(
            "objects_properties_action_toolbar",
            (
                ("polygon_edit", self.btn_rename),
                ("clean", self.btn_delete),
                ("collision", self.btn_collision),
            ),
            configure_action,
        )
        self.modify_action_toolbar = self._build_action_toolbar(
            "objects_modify_action_toolbar",
            (
                ("add", self.btn_expand),
                ("remove", self.btn_contract),
                ("xray_3", self.btn_invert),
                ("visible", self.btn_apply),
                ("clean", self.btn_cancel),
            ),
            configure_action,
        )
        self.export_action_toolbar = self._build_action_toolbar(
            "objects_export_action_toolbar",
            (("export", self.btn_export), ("open_image", self.btn_export_now)),
            configure_action,
        )
        self._toolbar_bindings = (
            (
                self.properties_action_toolbar,
                (self.btn_rename, self.btn_delete, self.btn_collision),
            ),
            (
                self.modify_action_toolbar,
                (
                    self.btn_expand,
                    self.btn_contract,
                    self.btn_invert,
                    self.btn_apply,
                    self.btn_cancel,
                ),
            ),
            (self.export_action_toolbar, (self.btn_export, self.btn_export_now)),
        )

        self._configure_accessibility_controls()

        # Layout
        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.scene_objects_label = QLabel("Scene Objects:")
        layout.addWidget(self.scene_objects_label)
        layout.addWidget(self.search_input)
        layout.addWidget(self.list)

        # Grupo 1: edição e colisão
        self.properties_group = QGroupBox("Properties")
        l_edit = QVBoxLayout()
        l_edit.addWidget(self.properties_action_toolbar)
        self.properties_group.setLayout(l_edit)
        layout.addWidget(self.properties_group)
        layout.addWidget(self.transform_group)
        metadata_group = QGroupBox("Metadata / Scenario")
        metadata_layout = QVBoxLayout(metadata_group)
        metadata_layout.addWidget(self.metadata_label)
        scenario_button = QPushButton("Open Scenario Editor")
        scenario_button.setObjectName("open_scenario_editor_from_inspector")
        self.open_scenario_editor_button = scenario_button
        scenario_button.setAccessibleName("Open Scenario Editor")
        scenario_button.setAccessibleDescription(
            "Open the separate scenario authoring editor"
        )
        scenario_button.setToolTip("Open the scenario editor")
        scenario_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        scenario_button.clicked.connect(
            lambda: getattr(self.window(), "open_scenario_editor", lambda: None)()
        )
        metadata_layout.addWidget(scenario_button)
        layout.addWidget(metadata_group)

        # Grupo 2: Modificadores
        self.modify_shape_group = QGroupBox("Modify Shape")
        l_tools = QVBoxLayout()
        l_tools.addWidget(self.modify_action_toolbar)
        l_tools.addWidget(self.slider_label)
        l_tools.addWidget(self.slider)
        self.modify_shape_group.setLayout(l_tools)
        layout.addWidget(self.modify_shape_group)

        # Grupo 3: Exportação
        self.export_group = QGroupBox("Export")
        l_export = QVBoxLayout()
        l_export.addWidget(self.export_action_toolbar)
        self.export_group.setLayout(l_export)
        layout.addWidget(self.export_group)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName("side_panel_scroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_area.setWidget(content)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.scroll_area)

        # Conexões
        self.list.itemSelectionChanged.connect(self._on_select)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_rename.clicked.connect(self._on_rename)
        self.btn_collision.clicked.connect(self._on_toggle_collision)
        self.btn_apply_transform.clicked.connect(self._on_apply_transform)
        self.btn_export.clicked.connect(self._on_export)
        self.btn_expand.clicked.connect(self._on_expand)
        self.btn_contract.clicked.connect(self._on_contract)
        self.btn_invert.clicked.connect(self._on_invert)
        self.slider.valueChanged.connect(self._on_slider_change)
        self.btn_apply.clicked.connect(self._on_apply)
        self.btn_cancel.clicked.connect(self._on_cancel_preview)
        self.btn_export_now.clicked.connect(self._on_export_now)

        for button in (
            self.btn_rename,
            self.btn_delete,
            self.btn_expand,
            self.btn_contract,
            self.btn_invert,
            self.btn_collision,
            self.btn_apply,
            self.btn_cancel,
            self.btn_export,
            self.btn_export_now,
        ):
            button.setVisible(False)

        self.current_lang = "en"
        self.translations = {
            "en": {
                "scene_objects": "Scene Objects:",
                "rename": "Rename",
                "delete": "Delete",
                "expand": "Expand",
                "contract": "Contract",
                "invert": "Invert",
                "collision_off": "Collision: OFF",
                "collision_on": "Collision: ON",
                "collision_dash": "Collision: --",
                "apply": "Apply",
                "cancel": "Cancel",
                "export_mask": "Export Mask",
                "export_sprite": "Export Sprite",
                "properties": "Properties",
                "modify_shape": "Modify Shape",
                "export": "Export",
                "expand_contract": "Expand/Contract: 0 px",
                "preview": "Preview: ",
                "delete_title": "Delete",
                "delete_object": "Delete object ",
                "rename_title": "Rename",
                "new_id": "New id:",
                "error": "Error",
                "collision_toggle_error": "Collision Toggle Error: ",
                "expand_title": "Expand",
                "pixels": "Pixels:",
                "contract_title": "Contract",
                "save_mask": "Save mask",
                "png_image": "PNG Image (*.png)",
                "save_sprite": "Save sprite",
            },
            "pt": {
                "scene_objects": "Objetos da Cena:",
                "rename": "Renomear",
                "delete": "Excluir",
                "expand": "Expandir",
                "contract": "Contrair",
                "invert": "Inverter",
                "collision_off": "Colisão: DESLIGADA",
                "collision_on": "Colisão: LIGADA",
                "collision_dash": "Colisão: --",
                "apply": "Aplicar",
                "cancel": "Cancelar",
                "export_mask": "Exportar Máscara",
                "export_sprite": "Exportar Sprite",
                "properties": "Propriedades",
                "modify_shape": "Modificar Forma",
                "export": "Exportar",
                "expand_contract": "Expandir/Contrair: 0 px",
                "preview": "Prévia: ",
                "delete_title": "Excluir",
                "delete_object": "Excluir objeto ",
                "rename_title": "Renomear",
                "new_id": "Novo id:",
                "error": "Erro",
                "collision_toggle_error": "Erro ao Alternar Colisão: ",
                "expand_title": "Expandir",
                "pixels": "Pixels:",
                "contract_title": "Contrair",
                "save_mask": "Salvar máscara",
                "png_image": "Imagem PNG (*.png)",
                "save_sprite": "Salvar sprite",
            },
        }

        if hasattr(self.scene, "subscribe"):
            self.scene.subscribe(self.refresh)
        self.refresh()
        self._last_preview_poly = None

    def _build_action_toolbar(self, name, bindings, configure_action):
        toolbar = QToolBar()
        toolbar.setObjectName(name)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        for key, button in bindings:
            action = toolbar.addAction(button.text())
            configure_action(
                action,
                key,
                text=button.text(),
                tooltip=button.text(),
                accessible_name=button.text(),
            )
            action.setProperty("commandKey", key)
            action.triggered.connect(button.click)
            action.setCheckable(button.isCheckable())
            button.toggled.connect(action.setChecked)
            toolbar_button = toolbar.widgetForAction(action)
            if toolbar_button is not None:
                toolbar_button.setObjectName(f"{name}_{key}_button")
                toolbar_button.setAccessibleName(button.text())
                toolbar_button.setAccessibleDescription(f"Activate {button.text()}")
                toolbar_button.setToolTip(button.text())
                toolbar_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        return toolbar

    def _configure_accessibility_controls(self) -> None:
        """Keep every inspector control usable by name and keyboard focus."""

        labels = {
            "rename": "Rename selected object",
            "delete": "Delete selected object",
            "expand": "Expand selected shape",
            "contract": "Contract selected shape",
            "invert": "Invert selected shape",
            "collision": "Toggle collision for selected object",
            "apply_transform": "Apply transform to selected object",
            "apply": "Apply shape preview",
            "cancel": "Cancel shape preview",
            "export_mask": "Export selected mask",
            "export_sprite": "Export selected sprite",
            "slider": "Adjust shape expansion or contraction preview",
        }
        buttons = (
            (self.btn_rename, labels["rename"]),
            (self.btn_delete, labels["delete"]),
            (self.btn_expand, labels["expand"]),
            (self.btn_contract, labels["contract"]),
            (self.btn_invert, labels["invert"]),
            (self.btn_collision, labels["collision"]),
            (self.btn_apply_transform, labels["apply_transform"]),
            (self.btn_apply, labels["apply"]),
            (self.btn_cancel, labels["cancel"]),
            (self.btn_export, labels["export_mask"]),
            (self.btn_export_now, labels["export_sprite"]),
        )
        for button, description in buttons:
            button.setAccessibleName(button.text())
            button.setAccessibleDescription(description)
            button.setToolTip(description)
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        fields = (
            (self.position_x, "Position X", "Edit the selected object's X position"),
            (self.position_y, "Position Y", "Edit the selected object's Y position"),
            (self.position_z, "Position Z", "Edit the selected object's Z position"),
            (self.rotation_x, "Rotation X", "Edit the selected object's X rotation"),
            (self.rotation_y, "Rotation Y", "Edit the selected object's Y rotation"),
            (self.rotation_z, "Rotation Z", "Edit the selected object's Z rotation"),
            (self.scale_x, "Scale X", "Edit the selected object's X scale"),
            (self.scale_y, "Scale Y", "Edit the selected object's Y scale"),
            (self.scale_z, "Scale Z", "Edit the selected object's Z scale"),
            (self.pivot_x, "Pivot X", "Edit the selected object's X pivot"),
            (self.pivot_y, "Pivot Y", "Edit the selected object's Y pivot"),
        )
        for field, name, description in fields:
            field.setObjectName(f"inspector_{name.lower().replace(' ', '_')}")
            field.setAccessibleName(name)
            field.setAccessibleDescription(description)
            field.setToolTip(description)
            field.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            line_edit = field.lineEdit()
            line_edit.setAccessibleName(name)
            line_edit.setAccessibleDescription(description)
            line_edit.setToolTip(description)
            line_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.snap_enabled.setAccessibleName("Snap vertices to grid")
        self.snap_enabled.setAccessibleDescription(
            "Toggle snapping of edited vertices to the 16 pixel grid"
        )
        self.snap_enabled.setToolTip("Snap edited vertices to the 16 pixel grid")
        self.slider.setObjectName("shape_expand_contract_slider")
        self.slider.setAccessibleName("Shape expansion slider")
        self.slider.setAccessibleDescription(labels["slider"])
        self.slider.setToolTip(labels["slider"])
        self.slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _sync_action_toolbar_texts(self) -> None:
        for toolbar, buttons in self._toolbar_bindings:
            for action, button in zip(toolbar.actions(), buttons):
                action.setText(button.text())
                action.setToolTip(button.text())
                action.setStatusTip(button.text())
                action.setEnabled(button.isEnabled())
                action.setProperty("accessibleName", button.text())
                toolbar_button = toolbar.widgetForAction(action)
                if toolbar_button is not None:
                    toolbar_button.setAccessibleName(button.text())
                    toolbar_button.setToolTip(button.text())
                if button.isCheckable():
                    action.setChecked(button.isChecked())

    def _build_context_menu(self) -> QMenu:
        menu = QMenu(self.list)
        sections = (
            ("Properties", self.properties_action_toolbar),
            ("Modify Shape", self.modify_action_toolbar),
            ("Export", self.export_action_toolbar),
        )
        for title, toolbar in sections:
            submenu = menu.addMenu(title)
            for toolbar_action in toolbar.actions():
                action = submenu.addAction(toolbar_action.icon(), toolbar_action.text())
                action.setToolTip(toolbar_action.toolTip())
                action.setProperty("commandKey", toolbar_action.property("commandKey"))
                action.setEnabled(toolbar_action.isEnabled())
                action.setCheckable(toolbar_action.isCheckable())
                action.setChecked(toolbar_action.isChecked())
                action.triggered.connect(toolbar_action.trigger)
        return menu

    def _show_context_menu(self, position) -> None:
        item = self.list.itemAt(position)
        if item is None:
            return
        self.list.setCurrentRow(self.list.row(item))
        self._build_context_menu().exec(self.list.mapToGlobal(position))

    @staticmethod
    def _transform_spin(
        minimum: float, maximum: float, step: float = 1.0
    ) -> QDoubleSpinBox:
        widget = QDoubleSpinBox()
        widget.setRange(minimum, maximum)
        widget.setSingleStep(step)
        widget.setDecimals(4)
        widget.setKeyboardTracking(False)
        return widget

    def refresh(self):
        """Rebuild the object list and mirror the scene selection exactly."""
        selected_id = getattr(self.scene, "selected_id", None)

        self.list.blockSignals(True)
        try:
            self.list.clear()
            selected_item = None

            query = self.search_input.text().strip().casefold()
            for oid, obj in sorted(self.scene.objects.items()):
                suffix = " [P]" if oid in self.scene.collision_shapes else ""
                label = f"{oid}{suffix}"
                searchable = f"{oid} {getattr(obj, 'name', '')}".casefold()
                if query and query not in searchable:
                    continue
                self.list.addItem(label)
                if oid == selected_id:
                    selected_item = self.list.item(self.list.count() - 1)

            if selected_item is not None:
                self.list.setCurrentItem(selected_item)
            else:
                self.list.clearSelection()
                self.list.setCurrentRow(-1)
        finally:
            self.list.blockSignals(False)

        actual_id, _ = self._get_selected_obj()
        marker = (selected_id, actual_id)
        if selected_id is not None and marker != self._last_validation_selection_marker:
            synchronized = selected_id == actual_id
            record_validation_event(
                "selection.synced",
                "SUCCESS" if synchronized else "FAILURE",
                scene_object_token=object_token(selected_id),
                list_object_token=object_token(actual_id),
                synchronized=synchronized,
                list_count=self.list.count(),
            )
        self._last_validation_selection_marker = marker
        self._update_button_states()
        self._refresh_transform_fields()

    def _get_selected_obj(self):
        items = self.list.selectedItems()
        if not items:
            return None, None
        full_text = items[0].text()
        oid = full_text.replace(" [P]", "")
        obj = self.scene.objects.get(oid)
        return oid, obj

    def _refresh_transform_fields(self) -> None:
        oid, obj = self._get_selected_obj()
        widgets = (
            self.position_x,
            self.position_y,
            self.position_z,
            self.rotation_x,
            self.rotation_y,
            self.rotation_z,
            self.scale_x,
            self.scale_y,
            self.scale_z,
            self.pivot_x,
            self.pivot_y,
        )
        enabled = obj is not None
        self.transform_group.setEnabled(enabled)
        self.btn_apply_transform.setEnabled(enabled)
        if obj is None:
            self.metadata_label.setText("No object selected")
            return
        self.metadata_label.setText(
            f"ID: {obj.id} | Vertices: {len(obj.polygon)} | "
            f"Collision: {'yes' if oid in self.scene.collision_shapes else 'no'}"
        )
        values = (
            *tuple(obj.position),
            *tuple(obj.rotation),
            *tuple(obj.scale),
            *tuple(getattr(obj, "pivot", (0.5, 0.5))),
        )
        for widget, value in zip(widgets, values):
            with QSignalBlocker(widget):
                widget.setValue(float(value))

    def _update_button_states(self):
        oid, obj = self._get_selected_obj()
        if obj:
            has_collision = oid in self.scene.collision_shapes
            self.btn_collision.setChecked(has_collision)
            self.btn_collision.setText(
                self.translations[self.current_lang][
                    "collision_on" if has_collision else "collision_off"
                ]
            )
            self.btn_collision.setEnabled(True)
        else:
            self.btn_collision.setChecked(False)
            self.btn_collision.setText(
                self.translations[self.current_lang]["collision_dash"]
            )
            self.btn_collision.setEnabled(False)
        self._sync_action_toolbar_texts()

    def _on_select(self):
        self._update_button_states()
        oid, obj = self._get_selected_obj()
        # Avisa a cena (opcional, se a cena tiver conceito de seleção)
        if oid and hasattr(self.scene, "select_object"):
            try:
                self.scene.select_object(oid)
            except Exception:
                pass
        self._refresh_transform_fields()

    def _present_transform_error(
        self,
        exc: BaseException,
        *,
        severity: str,
        channel: str,
    ):
        return show_p2d05_error(
            self,
            exc,
            operation="transform",
            language=self.current_lang,
            severity=severity,
            channel=channel,
        )

    def _execute_edit_command(self, command, *, p2d05_operation=None):
        manager = getattr(self.scene, "cmd", None)
        if manager is None:
            raise RuntimeError("Undo/Redo command history is unavailable.")

        result = manager.execute(command, self.scene)
        if result.status is CommandStatus.REJECTED:
            if p2d05_operation == "transform":
                self._present_transform_error(
                    RuntimeError(result.message or "The edit operation was rejected."),
                    severity="warning",
                    channel="status",
                )
            else:
                QMessageBox.warning(
                    self,
                    self.translations[self.current_lang]["error"],
                    result.message or "The edit operation was rejected.",
                )
        elif result.status is CommandStatus.FAILED:
            if p2d05_operation == "transform":
                self._present_transform_error(
                    RuntimeError(result.message or "The edit operation failed."),
                    severity="critical",
                    channel="modal",
                )
            else:
                QMessageBox.critical(
                    self,
                    self.translations[self.current_lang]["error"],
                    result.message or "The edit operation failed.",
                )
        return result

    def _on_apply_transform(self) -> None:
        oid, obj = self._get_selected_obj()
        if oid is None or obj is None:
            return
        try:
            before = capture_transform_state(self.scene, [oid])
            origin = before[oid]
            target_position = (
                self.position_x.value(),
                self.position_y.value(),
                self.position_z.value(),
            )
            target_rotation = (
                self.rotation_x.value(),
                self.rotation_y.value(),
                self.rotation_z.value(),
            )
            target_scale = (
                self.scale_x.value(),
                self.scale_y.value(),
                self.scale_z.value(),
            )
            if abs(origin.scale[0]) < 1e-12 or abs(origin.scale[1]) < 1e-12:
                raise ValueError("Current object scale cannot be zero.")
            after = transformed_snapshot(
                self.scene,
                [oid],
                translation=(
                    target_position[0] - origin.position[0],
                    target_position[1] - origin.position[1],
                ),
                rotation_degrees=target_rotation[2] - origin.rotation[2],
                scale=(
                    target_scale[0] / origin.scale[0],
                    target_scale[1] / origin.scale[1],
                ),
                anchor_override=origin.position[:2],
                base_snapshot=before,
            )
            state = after[oid]
            state.position = target_position
            state.pivot = (self.pivot_x.value(), self.pivot_y.value())
            state.rotation = target_rotation
            state.scale = target_scale
            result = self._execute_edit_command(
                TransformObjectsCommand(before, after),
                p2d05_operation="transform",
            )
            if result.changed:
                self.canvas.update()
        except ValueError as exc:
            self._present_transform_error(
                exc,
                severity="warning",
                channel="status",
            )
        except (KeyError, RuntimeError) as exc:
            self._present_transform_error(
                exc,
                severity="critical",
                channel="modal",
            )
        except Exception as exc:
            self._present_transform_error(
                exc,
                severity="critical",
                channel="modal",
            )

    def _on_toggle_collision(self):
        oid, _ = self._get_selected_obj()
        if not oid:
            return

        try:
            result = self._execute_edit_command(ToggleCollisionCommand(oid))
            if result.changed:
                self.canvas.update()
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                self.translations[self.current_lang]["collision_toggle_error"]
                + str(exc),
            )

    def _on_toggle_physics(self):
        """Compatibility adapter for historical callers."""
        self._on_toggle_collision()

    def _on_delete(self):
        oid, _ = self._get_selected_obj()
        if oid is None:
            return
        response = QMessageBox.question(
            self,
            self.translations[self.current_lang]["delete_title"],
            self.translations[self.current_lang]["delete_object"] + oid + "?",
        )
        if response != QMessageBox.StandardButton.Yes:
            return

        try:
            self._execute_edit_command(DeleteObjectCommand(oid))
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                str(exc),
            )

    def _on_rename(self):
        oid, _ = self._get_selected_obj()
        if oid is None:
            return
        new_id, accepted = QInputDialog.getText(
            self,
            self.translations[self.current_lang]["rename_title"],
            self.translations[self.current_lang]["new_id"],
            text=oid,
        )
        if not accepted or not new_id:
            return

        try:
            self._execute_edit_command(RenameObjectCommand(oid, new_id))
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                str(exc),
            )

    def _on_export(self):
        import cv2
        import numpy as np
        from PIL import Image

        oid, obj = self._get_selected_obj()
        if obj is None:
            logger.info("Export mask: No object selected")
            return
        logger.info(f"Export mask: Starting for object {oid}")
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.translations[self.current_lang]["save_mask"],
            oid + ".png",
            self.translations[self.current_lang]["png_image"],
        )
        if not path:
            logger.info("Export mask: User canceled save dialog")
            return
        if self.scene.image is None:
            logger.error("Export mask: No image loaded in scene")
            return
        logger.info("Export mask: Creating mask")
        h, w = self.scene.image.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        pts = np.array(obj.polygon, dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
        pil = Image.fromarray(mask, "L")
        try:
            pil.save(path)
            logger.info(f"Export mask: Mask saved successfully to {path}")
        except Exception as e:
            logger.error(f"Export mask: Failed to save mask to {path}: {e}")

    def _on_expand(self):
        oid, obj = self._get_selected_obj()
        if not obj:
            return
        val, ok = QInputDialog.getInt(
            self,
            self.translations[self.current_lang]["expand_title"],
            self.translations[self.current_lang]["pixels"],
            value=4,
            minValue=1,
        )
        if ok:
            self._modify_poly(oid, obj, val)

    def _on_contract(self):
        oid, obj = self._get_selected_obj()
        if not obj:
            return
        val, ok = QInputDialog.getInt(
            self,
            self.translations[self.current_lang]["contract_title"],
            self.translations[self.current_lang]["pixels"],
            value=4,
            minValue=1,
        )
        if ok:
            self._modify_poly(oid, obj, -val)

    def _modify_poly(self, oid, obj, delta):
        try:
            height, width = self.scene.image.shape[:2]
            new_polygon = expand_contract_polygon(
                obj.polygon,
                (height, width),
                delta,
            )
            if new_polygon:
                self._execute_edit_command(
                    UpdatePolygonCommand(
                        oid,
                        list(obj.polygon),
                        list(new_polygon),
                    )
                )
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                str(exc),
            )

    def _on_invert(self):
        oid, obj = self._get_selected_obj()
        if not obj:
            return
        try:
            height, width = self.scene.image.shape[:2]
            new_polygon = invert_selection(
                obj.polygon,
                (height, width),
            )
            if new_polygon:
                self._execute_edit_command(
                    UpdatePolygonCommand(
                        oid,
                        list(obj.polygon),
                        list(new_polygon),
                    )
                )
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                str(exc),
            )

    def _on_slider_change(self, value):
        self.slider_label.setText(
            self.translations[self.current_lang]["preview"] + f"{value} px"
        )
        oid, obj = self._get_selected_obj()
        if not obj:
            self.canvas.clear_temp_mask()
            return
        try:
            h, w = self.scene.image.shape[:2]
            poly = expand_contract_polygon(obj.polygon, (h, w), int(value))
            if poly:
                mask = polygon_to_mask(poly, (h, w))
                self.canvas.show_temp_mask(mask)
                self._last_preview_poly = poly
            else:
                self.canvas.clear_temp_mask()
                self._last_preview_poly = None
        except Exception:
            self.canvas.clear_temp_mask()

    def _reset_shape_preview(self):
        self._last_preview_poly = None
        self.slider.blockSignals(True)
        try:
            self.slider.setValue(0)
        finally:
            self.slider.blockSignals(False)
        self.slider_label.setText(
            self.translations[self.current_lang]["expand_contract"]
        )
        self.canvas.clear_temp_mask()

    def _on_apply(self):
        if not self._last_preview_poly:
            return
        oid, obj = self._get_selected_obj()
        if not obj:
            return
        try:
            result = self._execute_edit_command(
                UpdatePolygonCommand(
                    oid,
                    list(obj.polygon),
                    list(self._last_preview_poly),
                )
            )
            if result.ok:
                self._reset_shape_preview()
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.translations[self.current_lang]["error"],
                str(exc),
            )

    def _on_cancel_preview(self):
        self._reset_shape_preview()

    def _on_export_now(self):
        from src.exporters.sprite_exporter import (
            extract_masked_sprite,
            save_sprite,
        )

        oid, obj = self._get_selected_obj()
        if not obj:
            logger.info("Export sprite: No object selected")
            return
        logger.info(f"Export sprite: Starting for object {oid}")
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.translations[self.current_lang]["save_sprite"],
            oid + ".png",
            self.translations[self.current_lang]["png_image"],
        )
        if path:
            logger.info("Export sprite: Extracting masked sprite")
            try:
                img = extract_masked_sprite(self.scene.image, obj.polygon, padding=4)
                logger.info("Export sprite: Sprite extracted, saving")
                save_sprite(img, path)
                logger.info(f"Export sprite: Sprite saved successfully to {path}")
            except Exception as e:
                logger.error(f"Export sprite: Failed to export sprite for {oid}: {e}")
                QMessageBox.critical(
                    self, self.translations[self.current_lang]["error"], str(e)
                )

    def update_language(self, lang):
        self.current_lang = lang
        t = self.translations[self.current_lang]
        # Update labels
        self.scene_objects_label.setText(t["scene_objects"])
        # Buttons
        self.btn_rename.setText(t["rename"])
        self.btn_delete.setText(t["delete"])
        self.btn_expand.setText(t["expand"])
        self.btn_contract.setText(t["contract"])
        self.btn_invert.setText(t["invert"])
        # Groups
        self.properties_group.setTitle(t["properties"])
        self.modify_shape_group.setTitle(t["modify_shape"])
        self.export_group.setTitle(t["export"])
        self.slider_label.setText(t["expand_contract"])
        self.btn_apply.setText(t["apply"])
        self.btn_cancel.setText(t["cancel"])
        self.btn_export.setText(t["export_mask"])
        self.btn_export_now.setText(t["export_sprite"])
        self.open_scenario_editor_button.setAccessibleName(
            self.open_scenario_editor_button.text()
        )
        self.open_scenario_editor_button.setToolTip("Open the scenario editor")
        self._configure_accessibility_controls()
        # Update collision button state
        self._update_button_states()
