"""Domain exceptions for NeoEng-D-Trace project persistence."""

from __future__ import annotations


class ProjectPersistenceError(Exception):
    """Base class for project persistence failures."""


class ProjectReadError(ProjectPersistenceError):
    """Raised when the project file cannot be read."""


class ProjectWriteError(ProjectPersistenceError):
    """Raised when the project file cannot be written safely."""


class ProjectFormatError(ProjectPersistenceError):
    """Raised when the document does not identify a supported project format."""


class UnsupportedProjectVersionError(ProjectFormatError):
    """Raised when the document uses an unsupported schema version."""


class ProjectValidationError(ProjectPersistenceError):
    """Raised when a project document violates the approved schema."""


class LegacyProjectMigrationError(ProjectValidationError):
    """Raised when an unversioned legacy project cannot be migrated safely."""
