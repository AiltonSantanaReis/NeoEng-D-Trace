from __future__ import annotations

import hashlib
import math
import subprocess
from pathlib import Path

import pytest

from src.core.operational_limits import MAX_PROJECT_FILE_BYTES
from src.runtime import shaders as shader_module
from src.runtime.scene_runtime import RuntimeHost
from src.runtime.shaders import (
    ShaderBackendUnavailableError,
    ShaderCompilationError,
    ShaderDocumentV1,
    ShaderFormatError,
    ShaderMaterialRecord,
    ShaderProgramRecord,
    ShaderSourceBindingRecord,
    ShaderStageRecord,
    ShaderUniformRecord,
    ShaderValidationError,
    compile_shader_program,
    load_shader_runtime_export_bytes,
    save_shader_runtime_export,
    serialize_shader_runtime_export,
    shader_runtime_export_sha256,
)

VERTEX_SOURCE = """#version 440
layout(location = 0) in vec4 vertex;
void main() { gl_Position = vertex; }
"""
FRAGMENT_SOURCE = """#version 440
layout(location = 0) out vec4 fragColor;
void main() { fragColor = vec4(1.0); }
"""


def _document(fragment: str = FRAGMENT_SOURCE) -> ShaderDocumentV1:
    return ShaderDocumentV1(
        source=ShaderSourceBindingRecord(
            sha256="a" * 64,
        ),
        programs=[
            ShaderProgramRecord(
                id="basic",
                stages=[
                    ShaderStageRecord(stage="vertex", source=VERTEX_SOURCE),
                    ShaderStageRecord(stage="fragment", source=fragment),
                ],
            )
        ],
        materials=[
            ShaderMaterialRecord(
                id="material-basic",
                program_id="basic",
                uniforms=[
                    ShaderUniformRecord(
                        name="tint",
                        kind="vec4",
                        default=[1.0, 1.0, 1.0, 1.0],
                    )
                ],
            )
        ],
    )


def test_shader_contract_roundtrip_is_canonical_and_hash_bound() -> None:
    document = _document()
    raw = serialize_shader_runtime_export(document)
    assert raw.endswith(b"\n")
    assert load_shader_runtime_export_bytes(raw) == document
    assert shader_runtime_export_sha256(document) == hashlib.sha256(raw).hexdigest()


def test_shader_loader_rejects_bom_duplicate_and_noncanonical_bytes() -> None:
    raw = serialize_shader_runtime_export(_document())
    with pytest.raises(ShaderFormatError, match="BOM"):
        load_shader_runtime_export_bytes(b"\xef\xbb\xbf" + raw)

    duplicate = b'{"format_id":"neoeng-d-trace-runtime-shader","format_id":"x"}'
    with pytest.raises(ShaderFormatError, match="duplicate"):
        load_shader_runtime_export_bytes(duplicate)

    with pytest.raises(ShaderFormatError, match="canonical"):
        load_shader_runtime_export_bytes(raw.replace(b"\n", b"", 1))


def test_shader_contract_rejects_invalid_references_and_uniform_shape() -> None:
    with pytest.raises(ValueError, match="unknown program"):
        ShaderDocumentV1(
            source=ShaderSourceBindingRecord(sha256="a" * 64),
            programs=[
                ShaderProgramRecord(
                    id="basic",
                    stages=[
                        ShaderStageRecord(stage="vertex", source=VERTEX_SOURCE),
                        ShaderStageRecord(stage="fragment", source=FRAGMENT_SOURCE),
                    ],
                )
            ],
            materials=[ShaderMaterialRecord(id="m", program_id="missing", uniforms=[])],
        )

    with pytest.raises(ValueError, match="requires 4"):
        ShaderUniformRecord(name="tint", kind="vec4", default=[1.0])

    with pytest.raises(ValueError, match="one vertex"):
        ShaderProgramRecord(
            id="broken",
            stages=[
                ShaderStageRecord(stage="vertex", source=VERTEX_SOURCE),
                ShaderStageRecord(stage="vertex", source=VERTEX_SOURCE),
            ],
        )


def test_shader_export_is_atomic_and_rejects_invalid_destination(
    tmp_path: Path,
) -> None:
    document = _document()
    destination = tmp_path / "shader.json"
    save_shader_runtime_export(document, destination)
    assert destination.read_bytes() == serialize_shader_runtime_export(document)

    with pytest.raises(ShaderValidationError, match="directory"):
        save_shader_runtime_export(document, tmp_path)

    with pytest.raises(ShaderValidationError, match="parent"):
        save_shader_runtime_export(document, tmp_path / "missing" / "shader.json")


def test_qt_qsb_compiles_both_stages_and_publishes_hashable_outputs(
    tmp_path: Path,
) -> None:
    output = tmp_path / "compiled"
    report = compile_shader_program(_document(), "basic", output)
    assert report.status == "PASS"
    assert report.backend == "qt-qsb"
    assert {stage.stage for stage in report.stages} == {"vertex", "fragment"}
    for stage in report.stages:
        path = output / f"basic.{stage.stage}.qsb"
        assert path.is_file()
        assert path.stat().st_size == stage.bytes
        assert hashlib.sha256(path.read_bytes()).hexdigest() == stage.sha256


def test_qt_qsb_failure_preserves_previous_outputs(tmp_path: Path) -> None:
    output = tmp_path / "compiled"
    compile_shader_program(_document(), "basic", output)
    previous = (output / "basic.fragment.qsb").read_bytes()
    broken = _document("#version 440\nvoid main( {")

    with pytest.raises(ShaderCompilationError, match="fragment"):
        compile_shader_program(broken, "basic", output)

    assert (output / "basic.fragment.qsb").read_bytes() == previous
    assert (output / "basic.vertex.qsb").is_file()


def test_qt_qsb_missing_compiler_is_not_degraded_to_pass(tmp_path: Path) -> None:
    with pytest.raises(ShaderBackendUnavailableError, match="does not exist"):
        compile_shader_program(
            _document(),
            "basic",
            tmp_path / "compiled",
            compiler_path=tmp_path / "missing-qsb.exe",
        )


def test_runtime_host_advertises_only_the_integrated_shader_capability() -> None:
    host = RuntimeHost()
    assert "runtime.shaders" in host.supported_capabilities
    assert "runtime.particles" not in host.supported_capabilities


def test_shader_contract_rejects_non_finite_nul_and_wrong_uniform_values() -> None:
    with pytest.raises(ValueError, match="finite"):
        ShaderUniformRecord(name="alpha", kind="float", default=[math.nan])
    with pytest.raises(ValueError, match="finite"):
        shader_module._finite(True, "uniform.default")
    with pytest.raises(ValueError, match="NUL"):
        ShaderStageRecord(stage="vertex", source="void\x00main()")


def test_shader_contract_rejects_duplicate_program_material_and_uniform_ids() -> None:
    base_program = ShaderProgramRecord(
        id="basic",
        stages=[
            ShaderStageRecord(stage="vertex", source=VERTEX_SOURCE),
            ShaderStageRecord(stage="fragment", source=FRAGMENT_SOURCE),
        ],
    )
    with pytest.raises(ValueError, match="program IDs"):
        ShaderDocumentV1(
            source=ShaderSourceBindingRecord(sha256="a" * 64),
            programs=[base_program, base_program.model_copy(deep=True)],
            materials=[ShaderMaterialRecord(id="m", program_id="basic", uniforms=[])],
        )
    with pytest.raises(ValueError, match="material IDs"):
        ShaderDocumentV1(
            source=ShaderSourceBindingRecord(sha256="a" * 64),
            programs=[base_program],
            materials=[
                ShaderMaterialRecord(id="m", program_id="basic", uniforms=[]),
                ShaderMaterialRecord(id="m", program_id="basic", uniforms=[]),
            ],
        )
    with pytest.raises(ValueError, match="uniform names"):
        ShaderMaterialRecord(
            id="m",
            program_id="basic",
            uniforms=[
                ShaderUniformRecord(name="tint", kind="vec4", default=[1, 1, 1, 1]),
                ShaderUniformRecord(name="tint", kind="vec4", default=[1, 1, 1, 1]),
            ],
        )


def test_shader_loader_rejects_invalid_bytes_and_non_object_payloads() -> None:
    for raw in (b"not-json", b"\xff"):
        with pytest.raises(ShaderFormatError):
            load_shader_runtime_export_bytes(raw)
    with pytest.raises(ShaderValidationError, match="root"):
        load_shader_runtime_export_bytes(b"null")
    oversized = b" " * (MAX_PROJECT_FILE_BYTES + 1)
    with pytest.raises(ShaderFormatError, match="file limit"):
        load_shader_runtime_export_bytes(oversized)


def test_shader_validation_and_loader_cover_path_failures(tmp_path: Path) -> None:
    with pytest.raises(ShaderValidationError, match="root"):
        shader_module.validate_shader_runtime_export([])  # type: ignore[arg-type]
    missing = tmp_path / "missing.json"
    with pytest.raises(ShaderFormatError, match="cannot be read"):
        shader_module.load_shader_runtime_export(missing)


def test_qt_qsb_validation_rejects_unknown_program_timeout_and_bad_output(
    tmp_path: Path,
) -> None:
    document = _document()
    with pytest.raises(ShaderValidationError, match="timeout"):
        compile_shader_program(
            document, "basic", tmp_path / "compiled", timeout_seconds=0
        )
    with pytest.raises(ShaderValidationError, match="unknown"):
        compile_shader_program(document, "missing", tmp_path / "compiled")
    bad_output = tmp_path / "output.bin"
    bad_output.write_bytes(b"existing")
    with pytest.raises(ShaderValidationError, match="not a directory"):
        compile_shader_program(document, "basic", bad_output)


def test_qt_qsb_timeout_is_a_compilation_error_and_preserves_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "compiled"
    output.mkdir()
    previous = output / "basic.vertex.qsb"
    previous.write_bytes(b"previous")

    def timeout(*args: object, **kwargs: object) -> object:
        raise subprocess.TimeoutExpired("qsb", 1)

    monkeypatch.setattr(shader_module.subprocess, "run", timeout)
    with pytest.raises(ShaderCompilationError, match="timed out"):
        compile_shader_program(_document(), "basic", output)
    assert previous.read_bytes() == b"previous"
