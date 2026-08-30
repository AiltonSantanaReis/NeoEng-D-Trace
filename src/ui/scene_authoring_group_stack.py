"""Professional group hierarchy and isolation controls."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
    QVBoxLayout,
    QWidget,
)

from src.core.scene_authoring_groups import (
    child_group_ids,
    group_ancestry,
    group_parent_id,
    object_group_ids,
    object_ids_for_group,
)
from src.core.scene_authoring_session import SceneAuthoringSession
from src.persistence.scene_authoring_schema import (
    SceneAuthoringDocumentV2,
    SceneGroupAuthoringRecord,
    SceneGroupAuthoringRecordV2,
)


class SceneAuthoringGroupStack(QWidget):
    """Undoable group tree with explicit membership and transient isolation."""

    status_message = Signal(str)

    _KIND_ROLE = Qt.ItemDataRole.UserRole
    _ID_ROLE = Qt.ItemDataRole.UserRole + 1

    def __init__(self, session: SceneAuthoringSession, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        self.setObjectName("scenario_group_hierarchy")
        self._refreshing = False

        self.title = QLabel("Groups & Hierarchy", self)
        self.title.setObjectName("scenario_group_hierarchy_title")
        self.hint = QLabel(
            "Groups contain objects; nested groups inherit visibility and lock.",
            self,
        )
        self.hint.setWordWrap(True)
        self.hint.setObjectName("scenario_group_hierarchy_hint")
        self.tree = QTreeWidget(self)
        self.tree.setObjectName("scenario_group_hierarchy_tree")
        self.tree.setHeaderLabels(["Groups and objects"])
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree.currentItemChanged.connect(self._selection_changed)

        self.name_edit = QLineEdit(self)
        self.name_edit.setObjectName("scenario_group_name")
        self.name_edit.editingFinished.connect(self._rename_current)
        self.parent_combo = QComboBox(self)
        self.parent_combo.setObjectName("scenario_group_parent")
        self.parent_combo.currentIndexChanged.connect(self._set_parent)
        self.visible_box = QCheckBox("Visible", self)
        self.visible_box.setObjectName("scenario_group_visible")
        self.locked_box = QCheckBox("Locked", self)
        self.locked_box.setObjectName("scenario_group_locked")
        self.visible_box.toggled.connect(self._set_visible)
        self.locked_box.toggled.connect(self._set_locked)

        self.new_button = QPushButton("New Group", self)
        self.delete_button = QPushButton("Delete Group", self)
        self.add_selected_button = QPushButton("Add Selected", self)
        self.remove_selected_button = QPushButton("Remove Selected", self)
        self.up_button = QPushButton("Up", self)
        self.down_button = QPushButton("Down", self)
        self.isolate_button = QPushButton("Isolate", self)
        self.isolate_button.setCheckable(True)
        for button, name in (
            (self.new_button, "scenario_group_new"),
            (self.delete_button, "scenario_group_delete"),
            (self.add_selected_button, "scenario_group_add_selected"),
            (self.remove_selected_button, "scenario_group_remove_selected"),
            (self.up_button, "scenario_group_up"),
            (self.down_button, "scenario_group_down"),
            (self.isolate_button, "scenario_group_isolate"),
        ):
            button.setObjectName(name)
            button.setAutoDefault(False)
        self.new_button.clicked.connect(self._new_group)
        self.delete_button.clicked.connect(self._delete_group)
        self.add_selected_button.clicked.connect(self._add_selected)
        self.remove_selected_button.clicked.connect(self._remove_selected)
        self.up_button.clicked.connect(lambda: self._move(-1))
        self.down_button.clicked.connect(lambda: self._move(1))
        self.isolate_button.clicked.connect(self._toggle_isolation)

        fields = QHBoxLayout()
        fields.addWidget(QLabel("Name", self))
        fields.addWidget(self.name_edit, 1)
        parent_row = QHBoxLayout()
        parent_row.addWidget(QLabel("Parent", self))
        parent_row.addWidget(self.parent_combo, 1)
        toggles = QHBoxLayout()
        toggles.addWidget(self.visible_box)
        toggles.addWidget(self.locked_box)
        top_buttons = QHBoxLayout()
        top_buttons.addWidget(self.new_button)
        top_buttons.addWidget(self.delete_button)
        membership_buttons = QHBoxLayout()
        membership_buttons.addWidget(self.add_selected_button)
        membership_buttons.addWidget(self.remove_selected_button)
        order_buttons = QHBoxLayout()
        order_buttons.addWidget(self.up_button)
        order_buttons.addWidget(self.down_button)
        order_buttons.addWidget(self.isolate_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.hint)
        layout.addWidget(self.tree)
        layout.addLayout(fields)
        layout.addLayout(parent_row)
        layout.addLayout(toggles)
        layout.addLayout(top_buttons)
        layout.addLayout(membership_buttons)
        layout.addLayout(order_buttons)
        self.session.subscribe(self.refresh)
        self.refresh()

    def _run(self, operation) -> None:
        try:
            operation()
        except (KeyError, ValueError, PermissionError) as exc:
            self.status_message.emit(str(exc))

    def _current_ref(self) -> tuple[str, str] | None:
        item = self.tree.currentItem()
        if item is None:
            return None
        kind = item.data(0, self._KIND_ROLE)
        item_id = item.data(0, self._ID_ROLE)
        if kind not in {"group", "object"} or not item_id:
            return None
        return str(kind), str(item_id)

    def _current_group_id(self) -> str | None:
        current = self._current_ref()
        return current[1] if current is not None and current[0] == "group" else None

    def _set_ref(self, item: QTreeWidgetItem, kind: str, item_id: str) -> None:
        item.setData(0, self._KIND_ROLE, kind)
        item.setData(0, self._ID_ROLE, item_id)

    def _group_item(self, parent, group_id: str) -> QTreeWidgetItem:
        group = next(
            item for item in self.session.document.groups if item.id == group_id
        )
        flags = []
        if not group.visible:
            flags.append("hidden")
        if group.locked:
            flags.append("locked")
        suffix = f" [{', '.join(flags)}]" if flags else ""
        item = QTreeWidgetItem(parent, [f"Group: {group.name}{suffix}"])
        self._set_ref(item, "group", group.id)
        for child_id in child_group_ids(self.session.document, group.id):
            self._group_item(item, child_id)
        objects = {value.id: value for value in self.session.document.objects}
        layers = {value.id: value.name for value in self.session.document.layers}
        for object_id in group.members:
            object_record = objects.get(object_id)
            if object_record is None:
                continue
            layer_name = layers.get(object_record.layer_id, object_record.layer_id)
            child = QTreeWidgetItem(item, [f"Object: {object_id} ({layer_name})"])
            self._set_ref(child, "object", object_id)
        return item

    def _find_item(self, kind: str, item_id: str) -> QTreeWidgetItem | None:
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value() is not None:
            item = iterator.value()
            if (
                item.data(0, self._KIND_ROLE) == kind
                and item.data(0, self._ID_ROLE) == item_id
            ):
                return item
            iterator += 1
        return None

    def _selection_changed(self, current, _previous) -> None:
        if self._refreshing or current is None:
            return
        reference = self._current_ref()
        if reference is None:
            return
        kind, item_id = reference
        if kind == "group":
            ids = list(object_ids_for_group(self.session.document, item_id))
            self.session.set_selection(ids, ids[0] if ids else None)
        else:
            self.session.set_selection([item_id], item_id)

    def _rename_current(self) -> None:
        group_id = self._current_group_id()
        name = self.name_edit.text().strip()
        if group_id is not None and name:
            self._run(lambda: self.session.rename_group(group_id, name))

    def _set_parent(self, _index: int) -> None:
        if self._refreshing:
            return
        group_id = self._current_group_id()
        parent_id = self.parent_combo.currentData()
        if group_id is not None:
            self._run(lambda: self.session.set_group_parent(group_id, parent_id))

    def _set_visible(self, visible: bool) -> None:
        group_id = self._current_group_id()
        if group_id is not None and not self._refreshing:
            self._run(lambda: self.session.set_group_visibility(group_id, visible))

    def _set_locked(self, locked: bool) -> None:
        group_id = self._current_group_id()
        if group_id is not None and not self._refreshing:
            self._run(lambda: self.session.set_group_locked(group_id, locked))

    def _new_group(self) -> None:
        existing = {item.id for item in self.session.document.groups}
        index = 1
        group_id = "scenario_group"
        while group_id in existing:
            index += 1
            group_id = f"scenario_group_{index}"
        parent_id = self._current_group_id()
        members = list(self.session.selection.ids)
        if isinstance(self.session.document, SceneAuthoringDocumentV2):
            group = SceneGroupAuthoringRecordV2(
                id=group_id,
                name=f"Group {index}",
                members=members,
                parent_group_id=parent_id,
            )
        else:
            if parent_id is not None:
                self.status_message.emit("Nested groups require schema V2")
                return
            group = SceneGroupAuthoringRecord(
                id=group_id,
                name=f"Group {index}",
                members=members,
            )
        self._run(lambda: self.session.add_group(group))

    def _delete_group(self) -> None:
        group_id = self._current_group_id()
        if group_id is not None:
            self._run(lambda: self.session.remove_group(group_id))

    def _add_selected(self) -> None:
        group_id = self._current_group_id()
        if group_id is not None:
            self._run(
                lambda: self.session.add_objects_to_group(
                    group_id, self.session.selection.ids
                )
            )

    def _remove_selected(self) -> None:
        group_id = self._current_group_id()
        if group_id is not None:
            self._run(
                lambda: self.session.remove_objects_from_group(
                    group_id, self.session.selection.ids
                )
            )

    def _move(self, delta: int) -> None:
        group_id = self._current_group_id()
        if group_id is None:
            return
        group = next(
            item for item in self.session.document.groups if item.id == group_id
        )
        siblings = list(child_group_ids(self.session.document, group_parent_id(group)))
        index = siblings.index(group_id)
        self._run(lambda: self.session.reorder_group(group_id, index + delta))

    def _toggle_isolation(self) -> None:
        group_id = self._current_group_id()
        if group_id is None:
            return
        if self.session.isolated_group_id == group_id:
            self._run(self.session.clear_isolation)
            self.status_message.emit("Group isolation cleared")
        else:
            self._run(lambda: self.session.set_isolated_group(group_id))
            self.status_message.emit("Group isolated in viewport")

    def _refresh_parent_combo(self, group_id: str) -> None:
        current_parent = group_parent_id(
            next(item for item in self.session.document.groups if item.id == group_id)
        )
        excluded = {
            candidate.id
            for candidate in self.session.document.groups
            if group_id in group_ancestry(self.session.document, candidate.id)
        }
        self.parent_combo.blockSignals(True)
        self.parent_combo.clear()
        self.parent_combo.addItem("(Root)", None)
        for group in self.session.document.groups:
            if group.id in excluded:
                continue
            self.parent_combo.addItem(group.name, group.id)
        index = self.parent_combo.findData(current_parent)
        self.parent_combo.setCurrentIndex(max(0, index))
        self.parent_combo.blockSignals(False)

    def refresh(self) -> None:
        if self._refreshing:
            return
        self._refreshing = True
        try:
            selected = self._current_ref()
            self.tree.blockSignals(True)
            while self.tree.topLevelItemCount():
                self.tree.takeTopLevelItem(0)
            for group_id in child_group_ids(self.session.document, None):
                self._group_item(self.tree, group_id)
            grouped = {
                object_record.id
                for object_record in self.session.document.objects
                if object_group_ids(self.session.document, object_record.id)
            }
            ungrouped = QTreeWidgetItem(self.tree, ["Ungrouped Objects"])
            for object_record in self.session.document.objects:
                if object_record.id in grouped:
                    continue
                child = QTreeWidgetItem(
                    ungrouped,
                    [f"Object: {object_record.id} ({object_record.layer_id})"],
                )
                self._set_ref(child, "object", object_record.id)
            self.tree.expandAll()
            self.tree.blockSignals(False)
            if selected is not None:
                restored = self._find_item(*selected)
                if restored is not None:
                    self.tree.setCurrentItem(restored)
            group_id = self._current_group_id()
            enabled = group_id is not None
            for widget in (
                self.name_edit,
                self.parent_combo,
                self.visible_box,
                self.locked_box,
                self.delete_button,
                self.add_selected_button,
                self.remove_selected_button,
                self.up_button,
                self.down_button,
                self.isolate_button,
            ):
                widget.setEnabled(enabled)
            self.add_selected_button.setEnabled(
                enabled and bool(self.session.selection.ids)
            )
            self.remove_selected_button.setEnabled(
                enabled and bool(self.session.selection.ids)
            )
            if enabled:
                group = next(
                    item for item in self.session.document.groups if item.id == group_id
                )
                self.name_edit.blockSignals(True)
                self.name_edit.setText(group.name)
                self.name_edit.blockSignals(False)
                self.visible_box.blockSignals(True)
                self.visible_box.setChecked(group.visible)
                self.visible_box.blockSignals(False)
                self.locked_box.blockSignals(True)
                self.locked_box.setChecked(group.locked)
                self.locked_box.blockSignals(False)
                self._refresh_parent_combo(group_id)
                isolated = self.session.isolated_group_id == group_id
                self.isolate_button.blockSignals(True)
                self.isolate_button.setChecked(isolated)
                self.isolate_button.setText("Exit Isolation" if isolated else "Isolate")
                self.isolate_button.blockSignals(False)
            else:
                self.name_edit.clear()
                self.parent_combo.clear()
                self.isolate_button.setChecked(False)
                self.isolate_button.setText("Isolate")
        finally:
            self._refreshing = False
