"""Versioned shader contract and real Qt Shader Tools compilation.

The shader sidecar is bound to the exact lighting sidecar bytes and does not
reinterpret the approved lighting or scenario schemas. Compilation uses the
real Qt ``qsb`` tool when the declared ``qt-qsb`` backend is selected. A
failed compilation never replaces previously committed binaries.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from pydantic import Field, field_validator, model_validator

from src.core.atomic_outputs import AtomicOutputTransaction
from src.core.operational_limits import MAX_PROJECT_FILE_BYTES
from src.persistence.project_schema import StrictProjectModel

SHADER_FORMAT_ID = "neoeng-d-trace-runtime-shader"
SHADER_SCHEMA_VERSION = 1
SHADER_API_VERSION = 1
SHADER_SOURCE_FORMAT_ID = "neoeng-d-trace-runtime-lighting"
SHADER_SOURCE_SCHEMA_VERSION = 1
SHADER_BACKEND_QT_QSB = "qt-qsb"
MAX_SHADER_ID_LENGTH = 128
MAX_SHADER_SOURCE_BYTES = 256 * 1024
MAX_SHADER_PROGRAMS = 512
MAX_SHADER_MATERIALS = 4096
MAX_SHADER_UNIFORMS = 128
MAX_SHADER_COMPILATION_SECONDS = 120.0


class ShaderRuntimeError(ValueError):
    """Base class for controlled shader contract failures."""


class ShaderFormatError(ShaderRuntimeError):
    """Raised when shader manifest bytes are not canonical JSON."""


class ShaderValidationError(ShaderRuntimeError):
    """Raised when a shader manifest violates its versioned contract."""


class ShaderBackendUnavailableError(ShaderRuntimeError):
    """Raised when the declared real compiler cannot be found."""


class ShaderCompilationError(ShaderRuntimeError):
    """Raised when a real backend rejects shader source."""


def _finite(value: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


class ShaderSourceBindingRecord(StrictProjectModel):
    """Exact lighting sidecar bytes consumed by this shader document."""

    format_id: Literal["neoeng-d-trace-runtime-lighting"] = (
        "neoeng-d-trace-runtime-lighting"
    )
    schema_version: Literal[1] = 1
    sha256: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


class ShaderStageRecord(StrictProjectModel):
    """One GLSL stage compiled by the declared backend."""

    stage: Literal["vertex", "fragment"]
    source: str = Field(min_length=1, max_length=MAX_SHADER_SOURCE_BYTES)

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("shader source cannot contain NUL")
        if len(value.encode("utf-8")) > MAX_SHADER_SOURCE_BYTES:
            raise ValueError("shader source exceeds the size limit")
        return value


class ShaderUniformRecord(StrictProjectModel):
    """Bounded numeric uniform declaration owned by a shader material."""

    name: str = Field(
        min_length=1,
        max_length=MAX_SHADER_ID_LENGTH,
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*$",
    )
    kind: Literal["float", "vec2", "vec3", "vec4"]
    default: list[float] = Field(min_length=1, max_length=4)

    @field_validator("default")
    @classmethod
    def validate_default(cls, value: list[float]) -> list[float]:
        return [_finite(item, "uniform.default") for item in value]

    @model_validator(mode="after")
    def validate_component_count(self) -> "ShaderUniformRecord":
        expected = {"float": 1, "vec2": 2, "vec3": 3, "vec4": 4}[self.kind]
        if len(self.default) != expected:
            raise ValueError(f"{self.name} requires {expected} default component(s)")
        return self


class ShaderProgramRecord(StrictProjectModel):
    """A complete vertex/fragment program and its declared backend."""

    id: str = Field(min_length=1, max_length=MAX_SHADER_ID_LENGTH)
    backend: Literal["qt-qsb"] = "qt-qsb"
    stages: list[ShaderStageRecord] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def validate_stages(self) -> "ShaderProgramRecord":
        names = [stage.stage for stage in self.stages]
        if set(names) != {"vertex", "fragment"} or len(names) != len(set(names)):
            raise ValueError(
                "a shader program requires one vertex and one fragment stage"
            )
        return self


class ShaderMaterialRecord(StrictProjectModel):
    """Material binding that explicitly selects one shader program."""

    id: str = Field(min_length=1, max_length=MAX_SHADER_ID_LENGTH)
    program_id: str = Field(min_length=1, max_length=MAX_SHADER_ID_LENGTH)
    uniforms: list[ShaderUniformRecord] = Field(max_length=MAX_SHADER_UNIFORMS)

    @model_validator(mode="after")
    def validate_uniforms(self) -> "ShaderMaterialRecord":
        names = [uniform.name for uniform in self.uniforms]
        if len(names) != len(set(names)):
            raise ValueError("shader uniform names must be unique")
        return self


class ShaderDocumentV1(StrictProjectModel):
    """Complete version 1 shader/material sidecar contract."""

    format_id: Literal["neoeng-d-trace-runtime-shader"] = (
        "neoeng-d-trace-runtime-shader"
    )
    schema_version: Literal[1] = 1
    api_version: Literal[1] = 1
    source: ShaderSourceBindingRecord
    programs: list[ShaderProgramRecord] = Field(
        min_length=1, max_length=MAX_SHADER_PROGRAMS
    )
    materials: list[ShaderMaterialRecord] = Field(
        min_length=1, max_length=MAX_SHADER_MATERIALS
    )

    @model_validator(mode="after")
    def validate_references(self) -> "ShaderDocumentV1":
        return _validate_document_references(self)


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        return (
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ShaderValidationError(
            f"shader document is not serializable: {exc}"
        ) from exc


def _validate_document_references(
    document: ShaderDocumentV1,
) -> ShaderDocumentV1:
    program_ids = [program.id for program in document.programs]
    material_ids = [material.id for material in document.materials]
    if len(program_ids) != len(set(program_ids)):
        raise ValueError("shader program IDs must be unique")
    if len(material_ids) != len(set(material_ids)):
        raise ValueError("shader material IDs must be unique")
    if any(material.program_id not in program_ids for material in document.materials):
        raise ValueError("shader material references an unknown program")
    return document


def _validated_document(payload: object) -> ShaderDocumentV1:
    if isinstance(payload, ShaderDocumentV1):
        return _validate_document_references(payload)
    if not isinstance(payload, Mapping):
        raise ShaderValidationError("shader document root must be an object")
    try:
        return ShaderDocumentV1.model_validate(payload, strict=True)
    except Exception as exc:
        raise ShaderValidationError(str(exc)) from exc


def build_shader_runtime_export(document: ShaderDocumentV1) -> dict[str, Any]:
    """Validate and copy a shader document for export."""

    return _validated_document(document).model_dump(mode="json")


def serialize_shader_runtime_export(document: ShaderDocumentV1) -> bytes:
    """Serialize the shader sidecar as canonical UTF-8 JSON."""

    payload = build_shader_runtime_export(document)
    encoded = _canonical_json_bytes(payload)
    if len(encoded) > MAX_PROJECT_FILE_BYTES:
        raise ShaderValidationError("shader document exceeds the project file limit")
    return encoded


def shader_runtime_export_sha256(document: ShaderDocumentV1) -> str:
    """Hash the exact canonical shader sidecar bytes."""

    return hashlib.sha256(serialize_shader_runtime_export(document)).hexdigest()


def validate_shader_runtime_export(payload: Mapping[str, Any]) -> ShaderDocumentV1:
    """Strictly validate a decoded shader payload."""

    return _validated_document(payload)


def load_shader_runtime_export_bytes(raw: bytes) -> ShaderDocumentV1:
    """Load canonical shader bytes with duplicate-key and BOM rejection."""

    if not isinstance(raw, bytes):
        raise ShaderFormatError("shader manifest bytes must be bytes")
    if len(raw) > MAX_PROJECT_FILE_BYTES:
        raise ShaderFormatError("shader manifest exceeds the file limit")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ShaderFormatError("UTF-8 BOM is not allowed")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ShaderFormatError(f"invalid shader JSON: {exc}") from exc
    document = _validated_document(payload)
    if raw != serialize_shader_runtime_export(document):
        raise ShaderFormatError("shader manifest bytes are not canonical")
    return document


def load_shader_runtime_export(path: str | os.PathLike[str]) -> ShaderDocumentV1:
    """Load a canonical shader sidecar from disk."""

    candidate = Path(path)
    try:
        raw = candidate.read_bytes()
    except OSError as exc:
        raise ShaderFormatError(f"shader manifest cannot be read: {exc}") from exc
    return load_shader_runtime_export_bytes(raw)


def save_shader_runtime_export(
    document: ShaderDocumentV1, destination: str | os.PathLike[str]
) -> None:
    """Atomically replace one shader sidecar."""

    path = Path(destination)
    if path.exists() and path.is_dir():
        raise ShaderValidationError("shader export destination is a directory")
    if not path.parent.exists() or not path.parent.is_dir():
        raise ShaderValidationError("shader export parent directory does not exist")
    payload = serialize_shader_runtime_export(document)
    transaction = AtomicOutputTransaction()
    try:
        with transaction as active:
            temporary = active.stage_path(str(path))
            Path(temporary).write_bytes(payload)
            active.commit()
    except (OSError, ValueError) as exc:
        raise ShaderValidationError(f"failed to save shader export: {exc}") from exc


def _candidate_compilers() -> list[Path]:
    candidates: list[Path] = []
    for name in ("qsb", "qsb.exe", "pyside6-qsb", "pyside6-qsb.exe"):
        located = shutil.which(name)
        if located:
            candidates.append(Path(located))
    prefix = Path(sys.prefix)
    for relative in (
        Path("Lib/site-packages/PySide6/qsb.exe"),
        Path("Lib/site-packages/PySide6/qsb"),
        Path("lib/python3.11/site-packages/PySide6/qsb"),
    ):
        candidates.append(prefix / relative)
    return candidates


def resolve_qt_qsb(compiler_path: str | os.PathLike[str] | None = None) -> Path:
    """Resolve the real Qt Shader Tools executable without guessing a backend."""

    if compiler_path is not None:
        candidate = Path(compiler_path)
        if not candidate.is_file():
            raise ShaderBackendUnavailableError("declared qsb compiler does not exist")
        return candidate
    for candidate in _candidate_compilers():
        if candidate.is_file():
            return candidate
    raise ShaderBackendUnavailableError(
        "qt-qsb backend is unavailable; install PySide6 Qt Shader Tools"
    )


@dataclass(frozen=True)
class ShaderCompilationStage:
    """Hash and size of one compiled shader stage."""

    stage: str
    sha256: str
    bytes: int


@dataclass(frozen=True)
class ShaderCompilationReport:
    """Auditable result of one real program compilation."""

    status: Literal["PASS"]
    backend: str
    program_id: str
    compiler: str
    stages: tuple[ShaderCompilationStage, ...]


def compile_shader_program(
    document: ShaderDocumentV1,
    program_id: str,
    output_directory: str | os.PathLike[str],
    *,
    compiler_path: str | os.PathLike[str] | None = None,
    timeout_seconds: float = 15.0,
) -> ShaderCompilationReport:
    """Compile both stages with qsb and atomically publish all binaries.

    Compilation happens in a temporary directory. Existing output files remain
    untouched when either stage fails or times out.
    """

    document = _validated_document(document)
    timeout = _finite(timeout_seconds, "shader compilation timeout")
    if timeout <= 0.0 or timeout > MAX_SHADER_COMPILATION_SECONDS:
        raise ShaderValidationError("shader compilation timeout is outside the limit")
    program = next((item for item in document.programs if item.id == program_id), None)
    if program is None:
        raise ShaderValidationError("unknown shader program")
    compiler = resolve_qt_qsb(compiler_path)
    output = Path(output_directory)
    if output.exists() and not output.is_dir():
        raise ShaderValidationError("shader output path is not a directory")
    parent = output.parent
    if not parent.exists() or not parent.is_dir():
        raise ShaderValidationError("shader output parent directory does not exist")

    temporary_directory = Path(tempfile.mkdtemp(prefix=".neoeng-qsb-", dir=parent))
    compiled: list[ShaderCompilationStage] = []
    try:
        for stage in program.stages:
            suffix = ".vert" if stage.stage == "vertex" else ".frag"
            source_path = temporary_directory / f"{program.id}.{stage.stage}{suffix}"
            binary_path = temporary_directory / f"{program.id}.{stage.stage}.qsb"
            source_path.write_text(stage.source, encoding="utf-8", newline="\n")
            try:
                result = subprocess.run(
                    [str(compiler), "-b", "-o", str(binary_path), str(source_path)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise ShaderCompilationError(
                    f"qsb timed out compiling {stage.stage} stage"
                ) from exc
            if result.returncode != 0 or not binary_path.is_file():
                diagnostics = (result.stderr or result.stdout).strip()
                raise ShaderCompilationError(
                    f"qsb rejected {stage.stage} stage: {diagnostics[:2000]}"
                )
            content = binary_path.read_bytes()
            if not content:
                raise ShaderCompilationError(
                    f"qsb produced an empty {stage.stage} binary"
                )
            compiled.append(
                ShaderCompilationStage(
                    stage=stage.stage,
                    sha256=hashlib.sha256(content).hexdigest(),
                    bytes=len(content),
                )
            )

        transaction = AtomicOutputTransaction()
        with transaction as active:
            for item in compiled:
                source = temporary_directory / f"{program.id}.{item.stage}.qsb"
                destination = output / source.name
                staged = active.stage_path(str(destination))
                shutil.copyfile(source, staged)
            active.commit()
    except (OSError, ValueError) as exc:
        if isinstance(exc, ShaderRuntimeError):
            raise
        raise ShaderCompilationError(
            f"shader output transaction failed: {exc}"
        ) from exc
    finally:
        shutil.rmtree(temporary_directory, ignore_errors=True)

    return ShaderCompilationReport(
        status="PASS",
        backend=program.backend,
        program_id=program.id,
        compiler=compiler.name,
        stages=tuple(compiled),
    )
