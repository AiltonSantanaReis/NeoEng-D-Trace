"""Versioned project persistence for NeoEng-D-Trace."""

from .errors import (
    LegacyProjectMigrationError,
    ProjectFormatError,
    ProjectPersistenceError,
    ProjectReadError,
    ProjectValidationError,
    ProjectWriteError,
    UnsupportedProjectVersionError,
)
from .project_io import (
    LoadedProject,
    apply_project_document_to_scene,
    build_project_document,
    load_project_document,
    load_project_into_scene,
    save_scene_project,
)
from .project_schema import (
    MAX_PROJECT_FILE_BYTES,
    MAX_PROJECT_OBJECTS,
    MAX_PROJECT_POINTS,
    PROJECT_FILE_EXTENSION,
    ProjectDocumentV1,
)

__all__ = [
    "LegacyProjectMigrationError",
    "LoadedProject",
    "MAX_PROJECT_FILE_BYTES",
    "MAX_PROJECT_OBJECTS",
    "MAX_PROJECT_POINTS",
    "PROJECT_FILE_EXTENSION",
    "ProjectDocumentV1",
    "ProjectFormatError",
    "ProjectPersistenceError",
    "ProjectReadError",
    "ProjectValidationError",
    "ProjectWriteError",
    "UnsupportedProjectVersionError",
    "apply_project_document_to_scene",
    "build_project_document",
    "load_project_document",
    "load_project_into_scene",
    "save_scene_project",
]
