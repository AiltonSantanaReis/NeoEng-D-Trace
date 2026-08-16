"""Generate reproducible, inspectable artifacts from the active pipeline."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtWidgets import QApplication

from src.core.commands import AutoGenerateCollisionShapesCommand, CommandManager
from src.exporters.collision_exporter import export_collision_document
from src.models.scene import Scene
from src.persistence.project_io import save_scene_project
from src.tools.auto_detect import detect_polygons
from src.tools.segmentation import segment_grabcut
from src.ui.mask_viewer import MaskViewer

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "evidence" / "artifacts" / "roi-grabcut-collision"


def _digest(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _source_image() -> np.ndarray:
    image = np.zeros((240, 320, 3), dtype=np.uint8)
    for y in range(image.shape[0]):
        image[y, :, :] = np.array([18 + y // 8, 22 + y // 8, 28 + y // 8])
    polygon = np.array(
        [[65, 50], [250, 50], [250, 105], [185, 105], [185, 190], [65, 190]],
        dtype=np.int32,
    )
    cv2.fillPoly(image, [polygon], (205, 225, 235))
    cv2.circle(image, (125, 105), 20, (80, 90, 95), thickness=-1)
    cv2.GaussianBlur(image, (0, 0), 0.7, dst=image)
    return image


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    source = _source_image()
    source_path = OUTPUT / "source.png"
    cv2.imwrite(str(source_path), source)

    grabcut = segment_grabcut(source, (50, 35, 215, 170), iterations=5)
    mask_path = OUTPUT / "grabcut-mask.png"
    cv2.imwrite(str(mask_path), grabcut.mask)
    detections = detect_polygons(
        source,
        mode="grabcut",
        roi=(50, 35, 215, 170),
        grabcut_iterations=5,
        min_area=100,
        rdp_epsilon=1.5,
    )

    scene = Scene()
    scene.cmd = CommandManager()
    scene.add_object("detected-object", detections[0]["polygon"], select=False)
    scene.cmd.execute(AutoGenerateCollisionShapesCommand("convex_decomposition"), scene)
    collision_document = export_collision_document(
        scene,
        coordinate_space="normalized",
        image_size=(source.shape[1], source.shape[0]),
    )
    collision_path = OUTPUT / "collision-compound-normalized.json"
    collision_path.write_text(
        json.dumps(collision_document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    project_path = OUTPUT / "detected-compound.ndtproj"
    save_scene_project(scene, project_path)

    app = QApplication.instance() or QApplication([])
    viewer = MaskViewer()
    viewer.resize(800, 600)
    viewer.set_numpy_image(source)
    viewer.set_layer_overlays({"Canny": True, "Threshold": True}, 0.5)
    viewer._roi_rect = (50.0, 35.0, 215.0, 170.0)
    viewer.show()
    app.processEvents()
    visual_path = OUTPUT / "mask-viewer-roi-xray.png"
    viewer.grab().save(str(visual_path))
    viewer.close()

    files = [source_path, mask_path, collision_path, project_path, visual_path]
    manifest = {
        "schema_version": 1,
        "generator": "tools/generate_roi_collision_artifacts.py",
        "python": sys.version,
        "platform": platform.platform(),
        "source_shape": list(source.shape),
        "roi": [50, 35, 215, 170],
        "grabcut": {
            "foreground_pixels": grabcut.foreground_pixels,
            "foreground_ratio": grabcut.foreground_ratio,
            "components": grabcut.components,
            "iterations": grabcut.iterations,
        },
        "detection_feedback": detections.feedback,
        "collision_parts": len(scene.collision_parts["detected-object"]),
        "files": {path.name: _digest(path) for path in files},
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
