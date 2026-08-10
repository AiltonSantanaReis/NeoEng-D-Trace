"""Non-Qt identity contracts for Etapa 0.6N1."""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path

from src.core.app_identity import (
    APP_AUTHOR,
    APP_DISPLAY_NAME,
    APP_ID,
    APP_VERSION,
    CONFIG_DIR_NAME,
    GLTF_GENERATOR,
    LEGACY_APP_NAMES,
    LOGGER_NAME,
    PROJECT_FORMAT_ID,
    PROJECT_FORMAT_VERSION,
    build_window_title,
    normalize_language,
)
from src.core.logger import logger

ROOT = Path(__file__).resolve().parents[1]


def test_identity_constants_are_explicit_and_stable():
    assert APP_DISPLAY_NAME == "NeoEng-D-Trace"
    assert APP_ID == "neoeng_d_trace"
    assert APP_AUTHOR == "NeoEng-D-Trace Maintainer"
    assert CONFIG_DIR_NAME == "NeoEng-D-Trace"
    assert LOGGER_NAME == "NeoEng-D-Trace"
    assert GLTF_GENERATOR == "NeoEng-D-Trace GLTF Exporter"
    assert LEGACY_APP_NAMES == ("PolygonTool", "PolygonTool v2")


def test_project_format_identity_matches_the_approved_stage_3_adr():
    assert PROJECT_FORMAT_ID == "neoeng-d-trace-project"
    assert PROJECT_FORMAT_VERSION == 1


def test_window_title_is_available_in_both_supported_languages():
    assert build_window_title("en") == "NeoEng-D-Trace v2 - Engine Mode"
    assert build_window_title("pt") == "NeoEng-D-Trace v2 - Modo Engine"


def test_window_title_with_document_keeps_brand_and_filename():
    assert build_window_title("en", "asset.png") == "NeoEng-D-Trace - asset.png"
    assert build_window_title("pt", "asset.png") == "NeoEng-D-Trace - asset.png"


def test_unknown_language_falls_back_to_english_without_crashing():
    assert normalize_language("es") == "en"
    assert normalize_language(None) == "en"
    assert build_window_title("es") == "NeoEng-D-Trace v2 - Engine Mode"


def test_application_version_matches_pyproject():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == APP_VERSION


def test_global_logger_uses_new_identity():
    assert isinstance(logger, logging.Logger)
    assert logger.name == LOGGER_NAME


def test_runtime_identity_surfaces_do_not_embed_legacy_brand():
    runtime_files = [
        ROOT / "app.py",
        ROOT / "src/core/logger.py",
        ROOT / "src/ui/main_window.py",
        ROOT / "src/exporters/gltf_exporter.py",
        ROOT / "bench/benchmark_convex_decomp.py",
        ROOT / "bench/benchmark_gltf_export.py",
        ROOT / "bench/benchmark_triangulation.py",
        ROOT / "bench/run_benchmarks.py",
        ROOT / "tools/run_legacy_tests.py",
    ]
    for path in runtime_files:
        text = path.read_text(encoding="utf-8-sig")
        assert "PolygonTool" not in text, path
        assert "polygontool" not in text.lower(), path


def test_gltf_exporter_uses_central_generator_constant():
    source = (ROOT / "src/exporters/gltf_exporter.py").read_text(encoding="utf-8-sig")
    assert "generator=GLTF_GENERATOR" in source
    assert 'generator="NeoEng-D-Trace' not in source


def test_removed_namespace_tree_is_not_part_of_runtime():
    assert not (ROOT / "neoeng_d_trace").exists()
