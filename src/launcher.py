"""Application launcher for the single-tree NeoEng-D-Trace source layout."""

import argparse
import base64
import os
import sys
from pathlib import Path

# Tenta importar dependências críticas para dar feedback amigável
try:
    import cv2
    import numpy
    import pydantic
    from PIL import Image
except ImportError as e:
    print(f"CRITICAL ERROR: Missing dependency: {e}")
    print("Please install required packages: pip install -r requirements.txt")
    print("Or manually: pip install pydantic opencv-python numpy pillow")
    sys.exit(1)

from src.core.app_identity import APP_DISPLAY_NAME
from src.core.commands import CommandManager
from src.core.config import ConfigManager
from src.core.logger import logger, setup_logging
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
    """Return the source-checkout root without changing the legacy config location."""
    return Path(__file__).resolve().parents[1]


def run_headless(args: argparse.Namespace) -> int:
    """
    Run NeoEng-D-Trace in headless mode for automated processing.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Setup logging
        config_path = str(get_project_root() / "config.json")
        config = ConfigManager(config_path)
        setup_logging(
            log_level=config.get("log_level", "INFO"),
            log_to_file=config.get("log_to_file", False),
            log_file_path=config.get("log_file_path"),
        )

        logger.info("Starting %s in headless mode", APP_DISPLAY_NAME)

        # Create scene
        scene = Scene()
        scene.cmd = CommandManager()

        # Load image if provided
        if args.image:
            if not os.path.exists(args.image):
                logger.error(f"Image file not found: {args.image}")
                return 1

            try:
                from PIL import Image

                pil_image = Image.open(args.image)
                scene.load_image(pil_image, args.image)
                logger.info(f"Loaded image: {args.image}")
            except Exception as e:
                logger.error(f"Failed to load image: {e}")
                return 1

        # Load project if provided
        if args.project:
            if not os.path.exists(args.project):
                logger.error(f"Project file not found: {args.project}")
                return 1

            try:
                scene.load_project(args.project)
                logger.info(f"Loaded project: {args.project}")
            except Exception as e:
                logger.error(f"Failed to load project: {e}")
                return 1

        # Process operations
        if args.export_scene_gltf:
            try:
                from src.exporters.gltf_exporter import export_scene_to_gltf

                success = export_scene_to_gltf(scene, args.export_scene_gltf)
                if success:
                    logger.info(f"Exported scene to GLTF: {args.export_scene_gltf}")
                else:
                    logger.error("Failed to export scene to GLTF")
                    return 1
            except ImportError:
                logger.error("GLTF exporter module not found")
                return 1

        if args.export_object_gltf and args.object_id:
            try:
                from src.exporters.gltf_exporter import export_object_to_gltf

                success = export_object_to_gltf(
                    args.object_id, scene, args.export_object_gltf
                )
                if success:
                    msg = "Exported object {} to GLTF: {}".format(
                        args.object_id, args.export_object_gltf
                    )
                    logger.info(msg)
                else:
                    msg = f"Failed to export object {args.object_id} to GLTF"
                    logger.error(msg)
                    return 1
            except ImportError:
                logger.error("GLTF exporter module not found")
                return 1

        if args.export_json:
            from src.exporters.json_exporter import export_scene_metadata

            metadata = export_scene_metadata(scene)
            try:
                import json

                with open(args.export_json, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)
                logger.info(f"Exported metadata to JSON: {args.export_json}")
            except Exception as e:
                logger.error(f"Failed to export JSON: {e}")
                return 1

        # Save project if requested
        if args.save_project:
            try:
                scene.save_project(args.save_project)
                logger.info(f"Saved project: {args.save_project}")
            except Exception as e:
                logger.error(f"Failed to save project: {e}")
                return 1

        logger.info("Headless processing completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Headless processing failed: {e}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser using the centralized product identity."""

    parser = argparse.ArgumentParser(
        description=f"{APP_DISPLAY_NAME} - Game Asset Preparation Tool"
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run in headless mode (no GUI)"
    )
    parser.add_argument("--image", type=str, help="Load image file")
    parser.add_argument("--project", type=str, help="Load project file")
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
    parser.add_argument("--save-project", type=str, help="Save project to file")
    parser.add_argument(
        "--validation-log",
        type=str,
        help=("Write a structured JSONL log for a manual GUI validation session"),
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.headless or any(
        [args.export_scene_gltf, args.export_object_gltf, args.export_json]
    ):
        return run_headless(args)

    config_path = str(get_project_root() / "config.json")
    try:
        config = ConfigManager(config_path)
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
            config_location="project-root",
        )

    exit_code = 1
    try:
        # GUI dependencies are deliberately loaded after CLI dispatch and
        # validation-recorder setup so import failures are captured.
        from PySide6.QtGui import QFont
        from PySide6.QtWidgets import QApplication

        from src.ui.main_window import MainWindow
        from src.ui.theme_qss import QSS

        app = QApplication(sys.argv)
        font = QFont("Segoe UI", 10)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        app.setFont(font)
        app.setStyleSheet(QSS)

        scene = Scene()
        scene.cmd = CommandManager()
        win = MainWindow(scene, config)
        win.show()
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
        stop_validation_session(
            exit_code=exit_code,
            expected_events=MANUAL_VALIDATION_EVENTS,
        )


if __name__ == "__main__":
    main()
