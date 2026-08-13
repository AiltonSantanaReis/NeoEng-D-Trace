"""Atomic autosave snapshots independent from the Qt user interface."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Final, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from src.core.operational_limits import MAX_PROJECT_FILE_BYTES
from src.persistence.project_io import (
    apply_project_document_to_scene,
    build_project_document,
)
from src.persistence.project_schema import ProjectDocumentV1

AUTOSAVE_FORMAT_ID: Final[Literal["neoeng-d-trace-autosave"]] = (
    "neoeng-d-trace-autosave"
)
AUTOSAVE_FORMAT_VERSION: Final[Literal[1]] = 1
MAX_AUTOSAVE_FILE_BYTES = MAX_PROJECT_FILE_BYTES + 64 * 1024
MAX_AUTOSAVE_PATH_LENGTH = 32_768
MAX_AUTOSAVE_NAME_LENGTH = 1_024


class AutosaveError(Exception):
    def __init__(self, message: str, *, quarantine_path: Path | None = None) -> None:
        super().__init__(message)
        self.quarantine_path = quarantine_path


class _AutosaveRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    format_id: Literal["neoeng-d-trace-autosave"] = AUTOSAVE_FORMAT_ID
    schema_version: Literal[1] = AUTOSAVE_FORMAT_VERSION
    saved_at_utc: datetime
    reference_project_path: str = Field(
        min_length=1,
        max_length=MAX_AUTOSAVE_PATH_LENGTH,
    )
    source_project_path: str | None = Field(
        default=None,
        max_length=MAX_AUTOSAVE_PATH_LENGTH,
    )
    source_project_sha256: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
    )
    document_name: str | None = Field(
        default=None,
        max_length=MAX_AUTOSAVE_NAME_LENGTH,
    )
    document: ProjectDocumentV1

    @field_validator("saved_at_utc", mode="before")
    @classmethod
    def parse_saved_at_utc(cls, value: Any) -> Any:
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value

    @field_validator("saved_at_utc")
    @classmethod
    def validate_saved_at_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("autosave timestamp must include a timezone")
        return value.astimezone(timezone.utc)

    @field_validator("reference_project_path", "source_project_path")
    @classmethod
    def validate_path(cls, value: str | None) -> str | None:
        if value is not None and ("\x00" in value or not value.strip()):
            raise ValueError("autosave paths must be non-blank and contain no NUL")
        if value is not None and not Path(value).is_absolute():
            raise ValueError("autosave paths must be absolute")
        return value

    @field_validator("document_name")
    @classmethod
    def validate_document_name(cls, value: str | None) -> str | None:
        if value is not None and ("\x00" in value or not value.strip()):
            raise ValueError("autosave document name must be non-blank")
        return value

    @model_validator(mode="after")
    def validate_source_fingerprint(self) -> "_AutosaveRecord":
        if (self.source_project_path is None) != (self.source_project_sha256 is None):
            raise ValueError(
                "autosave source path and SHA-256 must be present together"
            )
        return self


@dataclass(frozen=True)
class AutosaveSnapshot:
    saved_at_utc: datetime
    reference_project_path: Path
    source_project_path: Path | None
    source_project_sha256: str | None
    document_name: str | None
    document: ProjectDocumentV1

    def apply_to(self, scene: Any) -> None:
        apply_project_document_to_scene(scene, self.document)

    def source_project_changed(self) -> bool:
        if self.source_project_path is None or self.source_project_sha256 is None:
            return False
        return _hash_file(self.source_project_path) != self.source_project_sha256


def _reject_duplicate_object_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _serialize(record: _AutosaveRecord) -> bytes:
    try:
        text = json.dumps(
            record.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise AutosaveError(f"autosave cannot be serialized: {exc}") from exc
    payload = (text + "\n").encode("utf-8")
    if len(payload) > MAX_AUTOSAVE_FILE_BYTES:
        raise AutosaveError(f"autosave exceeds {MAX_AUTOSAVE_FILE_BYTES} bytes")
    return payload


def _hash_file(path: Path) -> str | None:
    try:
        before = path.stat()
        if not path.is_file() or before.st_size > MAX_PROJECT_FILE_BYTES:
            return None
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (
            after.st_size,
            after.st_mtime_ns,
        ):
            return None
        return digest.hexdigest()
    except OSError:
        return None


def _atomic_write(destination: Path, payload: bytes) -> None:
    temporary_path: Path | None = None
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
        temporary_path = None
    except OSError as exc:
        raise AutosaveError(f"failed to atomically write autosave: {exc}") from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


class AutosaveStore:
    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.path = Path(path)
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def exists(self) -> bool:
        return self.path.is_file()

    def save(
        self,
        scene: Any,
        *,
        reference_project_path: str | os.PathLike[str],
        source_project_path: str | os.PathLike[str] | None = None,
        document_name: str | None = None,
    ) -> None:
        reference = Path(reference_project_path).resolve(strict=False)
        source_candidate = (
            Path(source_project_path).resolve(strict=False)
            if source_project_path is not None
            else None
        )
        source_sha256 = (
            _hash_file(source_candidate) if source_candidate is not None else None
        )
        source = source_candidate if source_sha256 is not None else None
        record = _AutosaveRecord(
            saved_at_utc=self._clock(),
            reference_project_path=str(reference),
            source_project_path=str(source) if source is not None else None,
            source_project_sha256=source_sha256,
            document_name=document_name,
            document=build_project_document(scene, reference),
        )
        _atomic_write(self.path, _serialize(record))

    def load(self) -> AutosaveSnapshot:
        try:
            size = self.path.stat().st_size
            if size > MAX_AUTOSAVE_FILE_BYTES:
                raise ValueError(f"autosave exceeds {MAX_AUTOSAVE_FILE_BYTES} bytes")
            with self.path.open("rb") as handle:
                raw = handle.read(MAX_AUTOSAVE_FILE_BYTES + 1)
            if len(raw) > MAX_AUTOSAVE_FILE_BYTES:
                raise ValueError(f"autosave exceeds {MAX_AUTOSAVE_FILE_BYTES} bytes")
            value = json.loads(
                raw.decode("utf-8", errors="strict"),
                parse_constant=lambda item: (_ for _ in ()).throw(
                    ValueError(f"non-finite JSON number is not allowed: {item}")
                ),
                object_pairs_hook=_reject_duplicate_object_keys,
            )
            record = _AutosaveRecord.model_validate(value)
        except OSError as exc:
            raise AutosaveError(f"failed to read autosave: {exc}") from exc
        except (
            UnicodeDecodeError,
            ValueError,
            json.JSONDecodeError,
            ValidationError,
        ) as exc:
            quarantine = self._quarantine()
            raise AutosaveError(
                f"invalid autosave: {exc}",
                quarantine_path=quarantine,
            ) from exc

        return AutosaveSnapshot(
            saved_at_utc=record.saved_at_utc,
            reference_project_path=Path(record.reference_project_path),
            source_project_path=(
                Path(record.source_project_path)
                if record.source_project_path is not None
                else None
            ),
            source_project_sha256=record.source_project_sha256,
            document_name=record.document_name,
            document=record.document,
        )

    def discard(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError as exc:
            raise AutosaveError(f"failed to discard autosave: {exc}") from exc

    def _quarantine(self) -> Path | None:
        if not self.path.exists():
            return None
        base = self.path.with_name(f"{self.path.name}.corrupted")
        for suffix in range(1_000):
            candidate = base if suffix == 0 else base.with_name(f"{base.name}.{suffix}")
            try:
                descriptor = os.open(
                    candidate,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                )
            except FileExistsError:
                continue
            except OSError:
                return None
            try:
                os.close(descriptor)
                os.replace(self.path, candidate)
            except OSError:
                try:
                    candidate.unlink(missing_ok=True)
                except OSError:
                    pass
                return None
            return candidate
        return None
