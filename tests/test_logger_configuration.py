import logging

from src.core.app_identity import LOGGER_NAME
from src.core.logger import setup_logging


def test_setup_logging_is_idempotent_and_disables_app_propagation():
    root = logging.getLogger()
    app_logger = logging.getLogger(LOGGER_NAME)
    root_before = list(root.handlers)
    app_before = list(app_logger.handlers)
    root_level = root.level
    app_level = app_logger.level
    app_propagate = app_logger.propagate
    try:
        setup_logging("INFO")
        setup_logging("INFO")
        root_owned = [
            h for h in root.handlers if getattr(h, "_neoeng_d_trace_owned", False)
        ]
        app_owned = [
            h for h in app_logger.handlers if getattr(h, "_neoeng_d_trace_owned", False)
        ]
        assert len(root_owned) == 1
        assert len(app_owned) == 1
        assert app_logger.propagate is False
    finally:
        for handler in list(root.handlers):
            if handler not in root_before:
                root.removeHandler(handler)
                handler.close()
        for handler in list(app_logger.handlers):
            if handler not in app_before:
                app_logger.removeHandler(handler)
                handler.close()
        root.setLevel(root_level)
        app_logger.setLevel(app_level)
        app_logger.propagate = app_propagate


def test_exporters_do_not_configure_root_logging():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for relative in (
        "src/exporters/sprite_exporter.py",
        "src/exporters/atlas_exporter.py",
    ):
        content = (root / relative).read_text(encoding="utf-8")
        assert "basicConfig" not in content
        assert "from src.core.logger import logger" in content
