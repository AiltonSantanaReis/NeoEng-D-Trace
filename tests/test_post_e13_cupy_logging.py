from __future__ import annotations

import logging

import src.core.view_processor as view_processor


def test_expected_optional_cupy_absence_is_informational(caplog):
    def missing_cupy(name):
        if name == "cupy":
            raise ImportError("optional accelerator unavailable")
        raise AssertionError(f"unexpected import: {name}")

    test_logger = logging.getLogger("post-e13.cupy")
    caplog.set_level(logging.INFO, logger=test_logger.name)
    original_logger = view_processor.logger
    view_processor.logger = test_logger
    try:
        cp_module, ndimage_module, has_gpu = view_processor._initialize_optional_cupy(
            missing_cupy
        )
    finally:
        view_processor.logger = original_logger

    assert cp_module is None
    assert ndimage_module is None
    assert has_gpu is False
    assert [record.levelno for record in caplog.records] == [logging.INFO]
    assert "CPU processing fallback is active" in caplog.records[0].message


def test_unexpected_optional_cupy_initialization_remains_warning(caplog):
    def broken_cupy(name):
        raise RuntimeError("driver unavailable")

    test_logger = logging.getLogger("post-e13.cupy.failure")
    caplog.set_level(logging.INFO, logger=test_logger.name)
    original_logger = view_processor.logger
    view_processor.logger = test_logger
    try:
        result = view_processor._initialize_optional_cupy(broken_cupy)
    finally:
        view_processor.logger = original_logger

    assert result == (None, None, False)
    assert [record.levelno for record in caplog.records] == [logging.WARNING]
    assert "driver unavailable" in caplog.records[0].message
