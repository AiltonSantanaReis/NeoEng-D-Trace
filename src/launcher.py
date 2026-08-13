"""Application launcher for the single-tree NeoEng-D-Trace source layout."""

import argparse
import base64
import os
import sys
import tempfile
from pathlib import Path

# Tenta importar dependências críticas para dar feedback amigável
try:
    import cv2 as _cv2
    import numpy as _numpy
    import pydantic as _pydantic
    from PIL import Image as PILImage

    _CRITICAL_DEPENDENCIES = (_cv2, _numpy, _pydantic, PILImage)
except ImportError as e:
    print(f"CRITICAL ERROR: Missing dependency: {e}")
    print("Install NeoEng-D-Trace with its declared dependencies.")
    print("For a source checkout, run: poetry install")
    sys.exit(1)

from src.core.app_identity import APP_DISPLAY_NAME, APP_VERSION
from src.core.app_paths import default_config_path
from src.core.commands import CommandManager
from src.core.config import ConfigManager
from src.core.image_input import inspect_image_file, validate_decoded_image
from src.core.logger import logger, setup_logging
from src.core.operational_limits import MAX_CONFIG_FILE_BYTES
from src.core.validation_events import (
    record_validation_event,
    record_validation_exception,
    start_validation_session,
    stop_validation_session,
    validation_enabled,
)
from src.models.scene import Scene

MANUAL_VALIDATION_EVENTS = (
    "application.opened",
    "language.changed",
    "image.opened",
    "polygon.created",
    "selection.synced",
    "export.dialog.opened",
    "export.sprite",
    "export.metadata",
    "export.atlas",
    "export.gltf.scene",
    "export.gltf.object",
)


def get_project_root() -> Path:
    """Return the source-checkout root."""
    return Path(__file__).resolve().parents[1]


def _migrate_legacy_config(legacy_path: Path, config_path: Path) -> None:
    if config_path.exists() or not legacy_path.is_file():
        return

    temporary_path: str | None = None
    try:
        with legacy_path.open("rb") as source:
            payload = source.read(MAX_CONFIG_FILE_BYTES + 1)
        if len(payload) > MAX_CONFIG_FILE_BYTES:
            logger.warning(
                "Legacy configuration exceeds %s bytes and was not migrated",
                MAX_CONFIG_FILE_BYTES,
            )
            return

        config_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_path = tempfile.mkstemp(
            suffix=".migrating", dir=config_path.parent
        )
        with os.fdopen(descriptor, "wb") as destination:
            destination.write(payload)
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary_path, config_path)
        temporary_path = None
        logger.info("Legacy configuration migrated to the user state directory")
    except OSError as exc:
        logger.warning("Legacy configuration migration failed: %s", exc)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            try:
                os.remove(temporary_path)
            except OSError:
                pass


def load_runtime_config(
    *,
    config_path: Path | None = None,
    legacy_path: Path | None = None,
    migrate_legacy: bool = True,
) -> ConfigManager:
    destination = default_config_path() if config_path is None else config_path
    legacy = get_project_root() / "config.json" if legacy_path is None else legacy_path
    if migrate_legacy:
        _migrate_legacy_config(legacy, destination)
    return ConfigManager(str(destination))


EXIT_SUCCESS = 0
EXIT_FAILURE = 1

_HEADLESS_FIELDS = (
    "image",
    "project",
    "export_scene_gltf",
    "export_object_gltf",
    "object_id",
    "export_json",
    "save_project",
)


def _headless_requested(args: argparse.Namespace) -> bool:
    return bool(
        args.headless
        or getattr(args, "export_profile", "default") != "default"
        or any(getattr(args, field, None) for field in _HEADLESS_FIELDS)
    )


def _headless_contract_error(args: argparse.Namespace) -> str | None:
    if getattr(args, "validation_log", None):
        return "--validation-log is available only in GUI mode"
    if args.image and args.project:
        return "--image and --project are mutually exclusive"
    if args.export_object_gltf and not args.object_id:
        return "--export-object-gltf requires --object-id"
    if args.object_id and not args.export_object_gltf:
        return "--object-id requires --export-object-gltf"
    if getattr(args, "export_profile", "default") != "default" and not args.export_json:
        return "--export-profile requires --export-json"
    if not any(
        getattr(args, field, None) for field in _HEADLESS_FIELDS if field != "object_id"
    ):
        return "headless mode requires an input or output operation"
    return None


def _cli_failure(message: str) -> int:
    logger.error(message)
    print(f"ERROR: {message}", file=sys.stderr)
    return EXIT_FAILURE


def run_headless(args: argparse.Namespace) -> int:
    """Run validated headless operations and return a process exit code."""
    contract_error = _headless_contract_error(args)
    if contract_error:
        return _cli_failure(contract_error)

    try:
        config = load_runtime_config(migrate_legacy=False)
        setup_logging(
            log_level=config.get("log_level", "INFO"),
            log_to_file=config.get("log_to_file", False),
            log_file_path=config.get("log_file_path"),
        )

        logger.info("Starting %s in headless mode", APP_DISPLAY_NAME)
        scene = Scene()
        scene.cmd = CommandManager()

        if args.image:
            if not os.path.isfile(args.image):
                return _cli_failure(f"Image file not found: {args.image}")
            try:
                image_info = inspect_image_file(args.image)
                with PILImage.open(args.image) as pil_image:
                    pil_image.load()
                    validate_decoded_image(pil_image, image_info)
                    scene.load_image(pil_image.copy(), args.image)
            except Exception as exc:
                return _cli_failure(f"Failed to load image: {exc}")

        if args.project:
            if not os.path.isfile(args.project):
                return _cli_failure(f"Project file not found: {args.project}")
            try:
                scene.load_project(args.project)
            except Exception as exc:
                return _cli_failure(f"Failed to load project: {exc}")

        if args.export_scene_gltf:
            try:
                from src.exporters.gltf_exporter import export_scene_to_gltf

                if not export_scene_to_gltf(scene, args.export_scene_gltf):
                    return _cli_failure("Failed to export scene to GLTF")
            except (ImportError, OSError, ValueError, RuntimeError) as exc:
                return _cli_failure(f"Failed to export scene to GLTF: {exc}")

        if args.export_object_gltf:
            try:
                from src.exporters.gltf_exporter import export_object_to_gltf

                if not export_object_to_gltf(
                    args.object_id, scene, args.export_object_gltf
                ):
                    return _cli_failure(
                        f"Failed to export object {args.object_id} to GLTF"
                    )
            except (ImportError, OSError, ValueError, RuntimeError) as exc:
                return _cli_failure(
                    f"Failed to export object {args.object_id} to GLTF: {exc}"
                )

        if args.export_json:
            try:
                from src.exporters.json_exporter import (
                    export_scene_metadata,
                    save_json_metadata,
                )

                save_json_metadata(
                    export_scene_metadata(scene, profile=args.export_profile),
                    args.export_json,
                )
            except (OSError, TypeError, ValueError) as exc:
                return _cli_failure(f"Failed to export JSON: {exc}")

        if args.save_project:
            try:
                scene.save_project(args.save_project)
            except (OSError, TypeError, ValueError) as exc:
                return _cli_failure(f"Failed to save project: {exc}")

        print("Headless processing completed successfully")
        return EXIT_SUCCESS
    except Exception as exc:
        return _cli_failure(f"Headless processing failed: {exc}")


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser using the centralized product identity."""

    parser = argparse.ArgumentParser(
        description=f"{APP_DISPLAY_NAME} - Game Asset Preparation Tool"
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run in headless mode (no GUI)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {APP_VERSION}",
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--image", type=str, help="Load image file")
    source_group.add_argument("--project", type=str, help="Load project file")
    parser.add_argument(
        "--export-scene-gltf",
        type=str,
        help="Export entire scene to GLTF file",
    )
    parser.add_argument(
        "--export-object-gltf",
        type=str,
        help="Export specific object to GLTF file",
    )
    parser.add_argument("--object-id", type=str, help="Object ID for export operations")
    parser.add_argument(
        "--export-json", type=str, help="Export scene metadata to JSON file"
    )
    parser.add_argument(
        "--export-profile",
        choices=("default", "generic", "godot", "unity", "phaser"),
        default="default",
        help="Select the JSON metadata profile used by --export-json",
    )
    parser.add_argument("--save-project", type=str, help="Save project to file")
    parser.add_argument(
        "--validation-log",
        type=str,
        help=("Write a structured JSONL log for a manual GUI validation session"),
    )
    parser.add_argument(
        "--smoke-test-gui",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.smoke_test_gui and not args.validation_log:
        parser.error("--smoke-test-gui requires --validation-log")

    if _headless_requested(args):
        return run_headless(args)

    try:
        config = load_runtime_config()
    except Exception as exc:
        print(f"Error loading config: {exc}")
        config = ConfigManager(None)  # type: ignore

    setup_logging(
        log_level=config.get("log_level", "INFO"),
        log_to_file=config.get("log_to_file", False),
        log_file_path=config.get("log_file_path"),
    )

    if args.validation_log:
        start_validation_session(args.validation_log)
        record_validation_event(
            "validation.mode",
            "SUCCESS",
            source_tree="src",
            config_location="user-state-directory",
        )

    exit_code = 1
    try:
        # GUI dependencies are deliberately loaded after CLI dispatch and
        # validation-recorder setup so import failures are captured.
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QFont
        from PySide6.QtWidgets import QApplication

        from src.core.app_paths import default_autosave_path
        from src.persistence.autosave import AutosaveStore
        from src.ui.main_window import MainWindow
        from src.ui.theme_qss import QSS

        app = QApplication(sys.argv)
        font = QFont("Segoe UI", 10)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        app.setFont(font)
        app.setStyleSheet(QSS)

        scene = Scene()
        scene.cmd = CommandManager()
        autosave_store = (
            AutosaveStore(default_autosave_path())
            if config.get("autosave_enabled", True)
            else None
        )
        win = MainWindow(scene, config)
        enable_autosave = getattr(win, "enable_autosave", None)
        if autosave_store is not None and enable_autosave is not None:
            enable_autosave(autosave_store)
        win.show()
        offer_autosave_recovery = getattr(win, "offer_autosave_recovery", None)
        if offer_autosave_recovery is not None:
            offer_autosave_recovery()
        record_validation_event(
            "application.opened",
            "SUCCESS",
            window_visible=bool(win.isVisible()),
            initial_language=getattr(win, "current_lang", None),
        )

        last_folder = config.get("last_folder")
        if last_folder and os.path.exists(last_folder):
            win.set_last_folder(last_folder)

        tool = config.get("tool", "polygonal_lasso")
        win.select_tool(tool)

        geometry = config.get("window_geometry")
        if geometry:
            try:
                geom_data = base64.b64decode(geometry)
                restored = win.restoreGeometry(geom_data)
                record_validation_event(
                    "window.geometry.restored",
                    "SUCCESS" if restored else "WARNING",
                    restored=bool(restored),
                )
            except Exception as exc:
                logger.error(
                    "Failed to restore window geometry: %s",
                    exc,
                    extra={"validation_event_recorded": True},
                )
                record_validation_exception("window.geometry.restored", exc)

        def on_close():
            try:
                config.set("last_folder", getattr(win, "_last_folder", None))
                config.set("tool", getattr(win, "_current_tool", "polygonal_lasso"))
                geom = win.saveGeometry()
                if geom:
                    config.set(
                        "window_geometry",
                        base64.b64encode(geom.data()).decode("ascii"),
                    )
                config.save()
                record_validation_event("application.state.saved", "SUCCESS")
            except Exception as exc:
                logger.error(
                    "Failed to save application state: %s",
                    exc,
                    extra={"validation_event_recorded": True},
                )
                record_validation_exception("application.state.saved", exc)

        app.aboutToQuit.connect(on_close)
        if args.smoke_test_gui:
            QTimer.singleShot(250, app.quit)
        exit_code = int(app.exec())
        record_validation_event(
            "application.closed",
            "SUCCESS" if exit_code == 0 else "FAILURE",
            exit_code=exit_code,
        )
        return exit_code
    except BaseException as exc:
        if validation_enabled():
            record_validation_exception("application.runtime", exc)
        raise
    finally:
        expected_events = (
            (
                "application.opened",
                "application.state.saved",
                "application.closed",
            )
            if args.smoke_test_gui
            else MANUAL_VALIDATION_EVENTS
        )
        stop_validation_session(
            exit_code=exit_code,
            expected_events=expected_events,
        )


if __name__ == "__main__":
    raise SystemExit(main())
