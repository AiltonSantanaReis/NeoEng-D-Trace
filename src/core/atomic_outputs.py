"""Transactional staging for commands that produce multiple output files."""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional


class AtomicOutputRollbackError(OSError):
    """Raised when an output commit fails and its rollback also fails."""


@dataclass
class _StagedOutput:
    temporary: str
    destination: str


class AtomicOutputTransaction:
    """Stage several outputs and commit them with rollback on commit failure.

    The guarantee covers failures raised during the current process. It does
    not claim crash-consistency across power loss or filesystem corruption.
    All temporary files and backups are created beside their destinations so
    ``os.replace`` remains on one filesystem.
    """

    def __init__(self) -> None:
        self._staged: List[_StagedOutput] = []
        self._destinations: Dict[str, str] = {}
        self._committed = False

    @staticmethod
    def _key(path: str) -> str:
        return os.path.normcase(os.path.abspath(path))

    def stage_path(self, destination: str) -> str:
        """Return a same-directory temporary path for ``destination``."""

        if not isinstance(destination, str) or not destination.strip():
            raise ValueError("output destination must be a non-empty path")
        normalized = os.path.abspath(destination)
        key = self._key(normalized)
        if key in self._destinations:
            raise ValueError("duplicate output destinations are not allowed")
        directory = os.path.dirname(normalized) or "."
        os.makedirs(directory, exist_ok=True)
        suffix = os.path.splitext(normalized)[1]
        descriptor, temporary = tempfile.mkstemp(
            prefix=".neoeng-stage-", suffix=suffix, dir=directory
        )
        os.close(descriptor)
        self._destinations[key] = normalized
        self._staged.append(_StagedOutput(temporary, normalized))
        return temporary

    def _replace(self, source: str, destination: str) -> None:
        os.replace(source, destination)

    def commit(self) -> None:
        """Replace every destination or restore the complete old set."""

        if self._committed:
            raise RuntimeError("output transaction was already committed")
        backups: Dict[str, Optional[str]] = {}
        committed: List[str] = []
        try:
            for staged in self._staged:
                destination = staged.destination
                if not os.path.exists(destination):
                    backups[destination] = None
                    continue
                directory = os.path.dirname(destination) or "."
                descriptor, backup = tempfile.mkstemp(
                    prefix=".neoeng-backup-", dir=directory
                )
                os.close(descriptor)
                try:
                    shutil.copy2(destination, backup)
                except Exception:
                    if os.path.exists(backup):
                        os.remove(backup)
                    raise
                backups[destination] = backup

            for staged in self._staged:
                self._replace(staged.temporary, staged.destination)
                committed.append(staged.destination)
        except Exception as error:
            try:
                for destination in reversed(committed):
                    stored_backup = backups[destination]
                    if stored_backup is None:
                        if os.path.exists(destination):
                            os.remove(destination)
                    else:
                        self._replace(stored_backup, destination)
                        backups[destination] = None
            except Exception as rollback_error:
                raise AtomicOutputRollbackError(
                    "output commit failed and rollback could not restore the set"
                ) from rollback_error
            raise error
        finally:
            self._cleanup(self._staged, backups)
            self._staged = []
            self._destinations = {}
        self._committed = True

    @staticmethod
    def _cleanup(
        staged: List[_StagedOutput], backups: Dict[str, Optional[str]]
    ) -> None:
        for item in staged:
            if os.path.exists(item.temporary):
                os.remove(item.temporary)
        for backup in backups.values():
            if backup and os.path.exists(backup):
                os.remove(backup)

    def abort(self) -> None:
        """Discard staged files without touching existing destinations."""

        self._cleanup(self._staged, {})
        self._staged = []
        self._destinations = {}

    def __enter__(self) -> "AtomicOutputTransaction":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> Literal[False]:
        if not self._committed:
            self.abort()
        return False
