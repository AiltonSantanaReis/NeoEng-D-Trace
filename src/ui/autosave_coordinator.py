"""Focused Qt coordination for autosave and explicit recovery decisions."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping

from PySide6.QtWidgets import QMessageBox

from src.core.document_session import DocumentSession
from src.core.logger import logger
from src.core.validation_events import (
    elapsed_ms,
    record_validation_event,
    record_validation_exception,
)
from src.persistence.autosave import (
    AutosaveError,
    AutosaveSnapshot,
    AutosaveStore,
)
from src.ui.autosave_controller import AutosaveController


class AutosaveCoordinator:
    def __init__(
        self,
        parent,
        *,
        scene,
        session: DocumentSession,
        store: AutosaveStore,
        interval_seconds: int,
        translations: Callable[[], Mapping[str, str]],
        recover: Callable[[AutosaveSnapshot], None],
        show_status: Callable[[str, int], None],
    ) -> None:
        self.parent = parent
        self.scene = scene
        self.session = session
        self.store = store
        self.translations = translations
        self.recover = recover
        self.show_status = show_status
        self._last_written_signature: str | None = None
        self._recovery_deferred = store.exists()
        self.controller = AutosaveController(
            parent,
            self.perform,
            interval_seconds=interval_seconds,
        )

    @property
    def timer(self):
        return self.controller.timer

    def stop(self) -> None:
        self.controller.stop()

    def discard(self) -> bool:
        self._last_written_signature = None
        if not self.store.exists():
            return True
        try:
            self.store.discard()
        except AutosaveError as exc:
            logger.error("Failed to discard autosave: %s", exc, exc_info=True)
            record_validation_exception("autosave.discarded", exc)
            return False
        record_validation_event("autosave.discarded", "SUCCESS")
        return True

    def discard_current_session(self) -> bool:
        if self._recovery_deferred:
            return True
        return self.discard()

    def perform(self) -> bool:
        if self._recovery_deferred or not self.session.is_modified():
            return False
        started_at = time.perf_counter()
        try:
            signature = self.session.compute_signature()
            if signature == self._last_written_signature:
                return False
            self.store.save(
                self.scene,
                reference_project_path=self.session.signature_path_hint(),
                source_project_path=self.session.project_path,
                document_name=self.session.document_name,
            )
        except Exception as exc:
            logger.error("Autosave failed: %s", exc, exc_info=True)
            record_validation_exception(
                "autosave.written",
                exc,
                duration_ms=elapsed_ms(started_at),
            )
            self.show_status(self.translations()["autosave_failed"], 5000)
            return False
        self._last_written_signature = signature
        record_validation_event(
            "autosave.written",
            "SUCCESS",
            duration_ms=elapsed_ms(started_at),
            object_count=len(self.scene.objects),
        )
        self.show_status(self.translations()["autosave_saved"], 3000)
        return True

    def offer_recovery(self) -> bool:
        if not self.store.exists():
            return False
        translations = self.translations()
        try:
            snapshot = self.store.load()
        except AutosaveError as exc:
            logger.error("Autosave recovery validation failed: %s", exc, exc_info=True)
            record_validation_exception("autosave.recovery", exc)
            detail = translations["autosave_invalid"]
            if exc.quarantine_path is not None:
                detail += translations["autosave_quarantined"].format(
                    path=exc.quarantine_path
                )
            QMessageBox.critical(
                self.parent,
                translations["autosave_recovery_title"],
                detail,
            )
            return False

        choice = QMessageBox.warning(
            self.parent,
            translations["autosave_recovery_title"],
            translations["autosave_recovery_message"].format(
                timestamp=snapshot.saved_at_utc.astimezone().isoformat(
                    timespec="seconds"
                )
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes,
        )
        if choice == QMessageBox.StandardButton.Discard:
            self._recovery_deferred = False
            self.discard()
            record_validation_event("autosave.recovery", "DISCARDED")
            return False
        if choice != QMessageBox.StandardButton.Yes:
            self._recovery_deferred = True
            record_validation_event("autosave.recovery", "DEFERRED")
            return False

        self._recovery_deferred = False
        try:
            self.recover(snapshot)
            self._last_written_signature = self.session.compute_signature()
        except Exception as exc:
            logger.error("Autosave recovery failed: %s", exc, exc_info=True)
            record_validation_exception("autosave.recovery", exc)
            QMessageBox.critical(
                self.parent,
                translations["autosave_recovery_title"],
                translations["autosave_recovery_failed"] + str(exc),
            )
            return False

        record_validation_event(
            "autosave.recovery",
            "SUCCESS",
            object_count=len(self.scene.objects),
            image_loaded=self.scene.image is not None,
        )
        return True
