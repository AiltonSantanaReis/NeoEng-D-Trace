"""Stable command identifiers backed by the existing Qt actions."""

from __future__ import annotations

import re
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction

_COMMAND_ID = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z0-9_]+)+$")


class CommandRegistrationError(ValueError):
    """Raised when a command cannot be registered without ambiguity."""


@dataclass(frozen=True)
class CommandState:
    """Observable state exposed to future command-palette consumers."""

    command_id: str
    label: str
    enabled: bool
    visible: bool
    shortcut: str


class CommandRegistry(QObject):
    """Register stable IDs while keeping ``QAction`` as the source of truth."""

    state_changed = Signal(str, bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._actions: dict[str, QAction] = {}
        self._action_ids: dict[int, str] = {}
        self._recent_ids: list[str] = []

    def register(self, command_id: str, action: QAction) -> None:
        """Register one action under a validated, globally unique ID."""

        if not _COMMAND_ID.fullmatch(command_id):
            raise CommandRegistrationError(f"invalid command ID: {command_id!r}")
        if not isinstance(action, QAction):
            raise CommandRegistrationError("command registry requires a QAction")
        if command_id in self._actions:
            raise CommandRegistrationError(
                f"command ID already registered: {command_id!r}"
            )
        action_key = id(action)
        if action_key in self._action_ids:
            previous = self._action_ids[action_key]
            raise CommandRegistrationError(
                f"QAction already registered as {previous!r}"
            )

        self._actions[command_id] = action
        self._action_ids[action_key] = command_id
        action.changed.connect(
            lambda command_id=command_id, action=action: self.state_changed.emit(
                command_id, action.isEnabled()
            )
        )

    def register_many(self, commands: list[tuple[str, QAction]]) -> None:
        """Register a batch atomically with respect to registry state."""

        ids = [command_id for command_id, _ in commands]
        if len(ids) != len(set(ids)):
            raise CommandRegistrationError("command IDs in a batch must be unique")
        actions = [action for _, action in commands]
        if len(actions) != len({id(action) for action in actions}):
            raise CommandRegistrationError("QActions in a batch must be unique")

        for command_id, action in commands:
            if command_id in self._actions or id(action) in self._action_ids:
                raise CommandRegistrationError(
                    "batch registration would duplicate an existing command"
                )
            if not _COMMAND_ID.fullmatch(command_id):
                raise CommandRegistrationError(f"invalid command ID: {command_id!r}")
            if not isinstance(action, QAction):
                raise CommandRegistrationError("command registry requires a QAction")

        for command_id, action in commands:
            self.register(command_id, action)

    def command_ids(self) -> tuple[str, ...]:
        """Return IDs in registration order for deterministic consumers."""

        return tuple(self._actions)

    def recent_ids(self) -> tuple[str, ...]:
        """Return successfully triggered commands, newest first."""

        return tuple(self._recent_ids)
    def action(self, command_id: str) -> QAction:
        """Return the source QAction for a registered ID."""

        try:
            return self._actions[command_id]
        except KeyError as exc:
            raise KeyError(f"unknown command ID: {command_id!r}") from exc

    def state(self, command_id: str) -> CommandState:
        """Read the current QAction state without copying it into a second model."""

        action = self.action(command_id)
        return CommandState(
            command_id=command_id,
            label=action.text(),
            enabled=action.isEnabled(),
            visible=action.isVisible(),
            shortcut=action.shortcut().toString(),
        )

    def states(self) -> tuple[CommandState, ...]:
        """Return deterministic snapshots for all registered commands."""

        return tuple(self.state(command_id) for command_id in self._actions)

    def is_enabled(self, command_id: str) -> bool:
        """Read the live enabled state of one command."""

        return self.action(command_id).isEnabled()

    def trigger(self, command_id: str) -> bool:
        """Trigger a command only when its source QAction is enabled."""

        action = self.action(command_id)
        if not action.isEnabled():
            return False
        action.trigger()
        self._recent_ids = [command_id] + [
            item for item in self._recent_ids if item != command_id
        ]
        return True
