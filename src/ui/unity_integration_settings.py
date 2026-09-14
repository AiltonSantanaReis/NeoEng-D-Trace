"""User-facing, non-secret integration flow for Unity Hub and Editor."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QProcess, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from src.core.unity_integration import (
    UNITY_HUB_DOCS_URL,
    UNITY_ID_URL,
    ExecutableKind,
    UnityIntegrationSnapshot,
    build_unity_integration_snapshot,
    is_expected_executable,
    normalize_external_path,
)


class UnityIntegrationDialog(QDialog):
    """Configure executable locations while keeping licensing in Unity Hub."""

    def __init__(self, window: Any):
        super().__init__(window)
        self.window_ref = window
        self.config = window.config
        self.current_lang = getattr(window, "current_lang", "en")
        self._snapshot: UnityIntegrationSnapshot | None = None
        self._committed = False
        self._setup_ui()
        self._load_configured_paths()
        self.update_language(self.current_lang)

    def _setup_ui(self) -> None:
        self.setObjectName("unity_integration_dialog")
        self.setModal(True)
        self.setMinimumWidth(680)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.intro_label = QLabel(self)
        self.intro_label.setObjectName("unity_integration_intro")
        self.intro_label.setWordWrap(True)
        layout.addWidget(self.intro_label)

        self.prerequisites_group = QGroupBox(self)
        self.prerequisites_group.setObjectName("unity_prerequisites_group")
        prerequisite_layout = QGridLayout(self.prerequisites_group)
        prerequisite_layout.setContentsMargins(12, 18, 12, 12)
        prerequisite_layout.setHorizontalSpacing(12)
        prerequisite_layout.setVerticalSpacing(8)

        self.hub_caption = QLabel(self.prerequisites_group)
        self.hub_status = QLabel(self.prerequisites_group)
        self.editor_caption = QLabel(self.prerequisites_group)
        self.editor_status = QLabel(self.prerequisites_group)
        self.license_caption = QLabel(self.prerequisites_group)
        self.license_status = QLabel(self.prerequisites_group)
        for status in (self.hub_status, self.editor_status, self.license_status):
            status.setWordWrap(True)
            status.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )

        prerequisite_layout.addWidget(self.hub_caption, 0, 0)
        prerequisite_layout.addWidget(self.hub_status, 0, 1)
        prerequisite_layout.addWidget(self.editor_caption, 1, 0)
        prerequisite_layout.addWidget(self.editor_status, 1, 1)
        prerequisite_layout.addWidget(self.license_caption, 2, 0)
        prerequisite_layout.addWidget(self.license_status, 2, 1)
        layout.addWidget(self.prerequisites_group)

        self.paths_group = QGroupBox(self)
        self.paths_group.setObjectName("unity_paths_group")
        paths_layout = QGridLayout(self.paths_group)
        paths_layout.setContentsMargins(12, 18, 12, 12)
        paths_layout.setHorizontalSpacing(8)
        paths_layout.setVerticalSpacing(8)

        self.hub_path_caption = QLabel(self.paths_group)
        self.hub_path = QLineEdit(self.paths_group)
        self.hub_path.setObjectName("unity_hub_path")
        self.hub_path.setReadOnly(True)
        self.hub_path.setClearButtonEnabled(False)
        self.hub_browse = QPushButton(self.paths_group)
        self.hub_browse.setObjectName("unity_hub_browse")
        self.hub_clear = QPushButton(self.paths_group)
        self.hub_clear.setObjectName("unity_hub_clear")

        self.editor_path_caption = QLabel(self.paths_group)
        self.editor_path = QLineEdit(self.paths_group)
        self.editor_path.setObjectName("unity_editor_path")
        self.editor_path.setReadOnly(True)
        self.editor_path.setClearButtonEnabled(False)
        self.editor_browse = QPushButton(self.paths_group)
        self.editor_browse.setObjectName("unity_editor_browse")
        self.editor_clear = QPushButton(self.paths_group)
        self.editor_clear.setObjectName("unity_editor_clear")

        paths_layout.addWidget(self.hub_path_caption, 0, 0)
        paths_layout.addWidget(self.hub_path, 0, 1)
        paths_layout.addWidget(self.hub_browse, 0, 2)
        paths_layout.addWidget(self.hub_clear, 0, 3)
        paths_layout.addWidget(self.editor_path_caption, 1, 0)
        paths_layout.addWidget(self.editor_path, 1, 1)
        paths_layout.addWidget(self.editor_browse, 1, 2)
        paths_layout.addWidget(self.editor_clear, 1, 3)
        paths_layout.setColumnStretch(1, 1)
        layout.addWidget(self.paths_group)

        self.personal_flow_label = QLabel(self)
        self.personal_flow_label.setObjectName("unity_personal_flow")
        self.personal_flow_label.setWordWrap(True)
        layout.addWidget(self.personal_flow_label)

        self.paid_flow_label = QLabel(self)
        self.paid_flow_label.setObjectName("unity_paid_flow")
        self.paid_flow_label.setWordWrap(True)
        layout.addWidget(self.paid_flow_label)

        self.security_label = QLabel(self)
        self.security_label.setObjectName("unity_integration_security")
        self.security_label.setWordWrap(True)
        layout.addWidget(self.security_label)

        self.actions_group = QGroupBox(self)
        self.actions_group.setObjectName("unity_actions_group")
        actions_layout = QHBoxLayout(self.actions_group)
        actions_layout.setContentsMargins(12, 18, 12, 12)
        actions_layout.setSpacing(8)
        self.refresh_button = QPushButton(self.actions_group)
        self.refresh_button.setObjectName("unity_refresh")
        self.open_hub_button = QPushButton(self.actions_group)
        self.open_hub_button.setObjectName("unity_hub_open")
        self.open_id_button = QPushButton(self.actions_group)
        self.open_id_button.setObjectName("unity_id_open")
        self.license_help_button = QPushButton(self.actions_group)
        self.license_help_button.setObjectName("unity_license_help")
        for button in (
            self.refresh_button,
            self.open_hub_button,
            self.open_id_button,
            self.license_help_button,
        ):
            button.setMinimumHeight(34)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            actions_layout.addWidget(button)
        layout.addWidget(self.actions_group)

        self.status_label = QLabel(self)
        self.status_label.setObjectName("unity_integration_status")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        self.buttons.setObjectName("unity_integration_buttons")
        self.buttons.accepted.connect(self._accept_dialog)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.hub_browse.clicked.connect(lambda: self._select_executable("hub"))
        self.editor_browse.clicked.connect(lambda: self._select_executable("editor"))
        self.hub_clear.clicked.connect(self.hub_path.clear)
        self.editor_clear.clicked.connect(self.editor_path.clear)
        self.hub_path.textChanged.connect(self._refresh_status)
        self.editor_path.textChanged.connect(self._refresh_status)
        self.refresh_button.clicked.connect(self._refresh_status)
        self.open_hub_button.clicked.connect(self._open_hub)
        self.open_id_button.clicked.connect(lambda: self._open_url(UNITY_ID_URL))
        self.license_help_button.clicked.connect(
            lambda: self._open_url(UNITY_HUB_DOCS_URL)
        )

    def _load_configured_paths(self) -> None:
        get_value = getattr(self.config, "get", None)
        if not callable(get_value):
            return
        for widget, key in (
            (self.hub_path, "unity_hub_path"),
            (self.editor_path, "unity_editor_path"),
        ):
            value = get_value(key)
            if value:
                widget.setText(str(value))

    @property
    def _translations(self) -> dict[str, Any]:
        translations = getattr(self.window_ref, "translations", {})
        return translations.get(self.current_lang, translations.get("en", {}))

    def update_language(self, lang: str) -> None:
        self.current_lang = lang if lang in {"en", "pt"} else "en"
        t = self._translations
        self.setWindowTitle(t["unity_integration_dialog"])
        self.intro_label.setText(t["unity_integration_intro"])
        self.prerequisites_group.setTitle(t["unity_prerequisites"])
        self.hub_caption.setText(t["unity_hub"])
        self.editor_caption.setText(t["unity_editor"])
        self.license_caption.setText(t["unity_login_license"])
        self.hub_path_caption.setText(t["unity_hub_path"])
        self.editor_path_caption.setText(t["unity_editor_path"])
        self.paths_group.setTitle(t["unity_paths"])
        self.hub_browse.setText(t["unity_browse"])
        self.editor_browse.setText(t["unity_browse"])
        self.hub_clear.setText(t["unity_clear"])
        self.editor_clear.setText(t["unity_clear"])
        self.personal_flow_label.setText(t["unity_personal_flow"])
        self.paid_flow_label.setText(t["unity_paid_flow"])
        self.security_label.setText(t["unity_config_no_secret"])
        self.actions_group.setTitle(t["unity_actions"])
        self.refresh_button.setText(t["unity_refresh"])
        self.open_hub_button.setText(t["unity_open_hub"])
        self.open_id_button.setText(t["unity_open_id"])
        self.license_help_button.setText(t["unity_license_help"])
        self.hub_path.setPlaceholderText(t["unity_not_configured"])
        self.editor_path.setPlaceholderText(t["unity_not_configured"])
        self.hub_path.setAccessibleName(t["unity_hub_path"])
        self.editor_path.setAccessibleName(t["unity_editor_path"])
        self.hub_browse.setAccessibleName(t["unity_select_hub"])
        self.editor_browse.setAccessibleName(t["unity_select_editor"])
        self.hub_clear.setAccessibleName(f"{t['unity_clear']} {t['unity_hub']}")
        self.editor_clear.setAccessibleName(f"{t['unity_clear']} {t['unity_editor']}")
        self.refresh_button.setAccessibleName(t["unity_refresh"])
        self.open_hub_button.setAccessibleName(t["unity_open_hub"])
        self.open_id_button.setAccessibleName(t["unity_open_id"])
        self.license_help_button.setAccessibleName(t["unity_license_help"])
        ok_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button is not None:
            ok_button.setText(t["ok"])
        if cancel_button is not None:
            cancel_button.setText(t["cancel"])
        self._refresh_status()

    def _refresh_status(self) -> None:
        try:
            self._snapshot = build_unity_integration_snapshot(
                self.hub_path.text() or None,
                self.editor_path.text() or None,
            )
        except ValueError as exc:
            self._snapshot = None
            message = str(exc)
            self.hub_status.setText(message)
            self.editor_status.setText(message)
            self.license_status.setText(self._translations["unity_external_management"])
            self.status_label.setText(message)
            return

        snapshot = self._snapshot
        self.hub_status.setText(
            self._format_state(snapshot.hub_state, snapshot.hub_path)
        )
        self.editor_status.setText(
            self._format_state(snapshot.editor_state, snapshot.editor_path)
        )
        self.license_status.setText(self._translations["unity_external_management"])
        self.status_label.setText(
            f"{self._translations['unity_hub']}: {self.hub_status.text()}\n"
            f"{self._translations['unity_editor']}: {self.editor_status.text()}\n"
            f"{self._translations['unity_login_license']}: "
            f"{self._translations['unity_external_management']}"
        )

    def _format_state(self, state: str, path) -> str:
        t = self._translations
        if state == "available":
            return t["unity_available"].format(path=path)
        if state == "missing":
            return t["unity_missing"].format(path=path)
        if state == "invalid":
            return t["unity_invalid"].format(path=path)
        return t["unity_not_configured"]

    def _select_executable(self, kind: ExecutableKind) -> None:
        t = self._translations
        title = t["unity_select_hub"] if kind == "hub" else t["unity_select_editor"]
        current = self.hub_path.text() if kind == "hub" else self.editor_path.text()
        selected, _ = QFileDialog.getOpenFileName(
            self,
            title,
            current,
            t["unity_executable_filter"],
        )
        if not selected:
            return
        try:
            path = normalize_external_path(selected)
        except ValueError as exc:
            QMessageBox.warning(self, t["unity_invalid_executable_title"], str(exc))
            return
        if path is None or not path.is_file() or not is_expected_executable(path, kind):
            detail_key = (
                "unity_invalid_hub_message"
                if kind == "hub"
                else "unity_invalid_editor_message"
            )
            QMessageBox.warning(
                self,
                t["unity_invalid_executable_title"],
                t[detail_key],
            )
            return
        (self.hub_path if kind == "hub" else self.editor_path).setText(str(path))

    def _validated_config_path(
        self, widget: QLineEdit, kind: ExecutableKind
    ) -> str | None:
        path = normalize_external_path(widget.text() or None)
        if path is None:
            return None
        if not is_expected_executable(path, kind):
            raise ValueError(
                self._translations[
                    (
                        "unity_invalid_hub_message"
                        if kind == "hub"
                        else "unity_invalid_editor_message"
                    )
                ]
            )
        return str(path)

    def commit(self) -> bool:
        """Persist only executable locations in the user configuration."""

        if self._committed:
            return True
        try:
            values = {
                "unity_hub_path": self._validated_config_path(self.hub_path, "hub"),
                "unity_editor_path": self._validated_config_path(
                    self.editor_path, "editor"
                ),
            }
        except ValueError as exc:
            QMessageBox.warning(
                self,
                self._translations["unity_invalid_executable_title"],
                str(exc),
            )
            return False

        set_value = getattr(self.config, "set", None)
        if callable(set_value):
            for key, value in values.items():
                set_value(key, value)
            save_value = getattr(self.config, "save", None)
            if callable(save_value):
                save_value()
        self._committed = True
        self.status_label.setText(self._translations["unity_saved"])
        return True

    def _accept_dialog(self) -> None:
        if self.commit():
            self.accept()

    def _open_hub(self) -> None:
        self._refresh_status()
        snapshot = self._snapshot
        t = self._translations
        if snapshot is None or snapshot.hub_state != "available":
            QMessageBox.warning(
                self,
                t["unity_hub_not_found_title"],
                t["unity_hub_not_found_message"],
            )
            return
        try:
            result = QProcess.startDetached(str(snapshot.hub_path), [])
            started = bool(result[0]) if isinstance(result, tuple) else bool(result)
        except (OSError, RuntimeError):
            started = False
        if started:
            self.status_label.setText(t["unity_hub_opened"])
        else:
            QMessageBox.warning(
                self,
                t["unity_open_failed_title"],
                t["unity_open_failed_message"],
            )

    def _open_url(self, url: str) -> None:
        if QDesktopServices.openUrl(QUrl(url)):
            return
        t = self._translations
        QMessageBox.warning(
            self,
            t["unity_url_failed_title"],
            t["unity_url_failed_message"],
        )


def open_unity_integration_settings(window: Any) -> None:
    """Open the Unity preflight dialog from a canonical MainWindow action."""

    previous = getattr(window, "unity_integration_dialog", None)
    if previous is not None:
        previous.close()
        previous.deleteLater()
    dialog = UnityIntegrationDialog(window)
    window.unity_integration_dialog = dialog
    if dialog.exec() == QDialog.DialogCode.Accepted:
        dialog.commit()


__all__ = ["UnityIntegrationDialog", "open_unity_integration_settings"]
