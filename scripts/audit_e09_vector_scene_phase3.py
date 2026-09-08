"""Official E09-C audit for collision/resource integration and persistence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.core.vectorization import vectorize_image_file
from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scenario_schema import ProjectReferenceRecord
from src.persistence.scene_authoring_io import (
    SceneAuthoringAssetError,
    load_scene_authoring,
    save_scene_authoring,
)
from src.persistence.scene_authoring_schema import (
    AssetReferenceRecord,
    SceneAuthoringDocumentV1,
    SceneAuthoringMetadataRecord,
    SceneLayerAuthoringRecord,
    SceneTransformRecord,
)


def _source_tree_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--short"],
        check=True,
        capture_output=True,
        text=True,
    )
    return not result.stdout.strip()


def _write_image(path: Path) -> None:
    image = np.zeros((96, 128, 4), dtype=np.uint8)
    image[18:78, 24:104, 3] = 255
    ok, encoded = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA))
    if not ok:
        raise RuntimeError("cannot encode E09-C source")
    path.write_bytes(encoded.tobytes())


def _document(project: Path, asset: Path) -> SceneAuthoringDocumentV1:
    return SceneAuthoringDocumentV1(
        metadata=SceneAuthoringMetadataRecord(
            name="E09-C audit", generator="NeoEng-D-Trace", app_version="0.3.0"
        ),
        project=ProjectReferenceRecord(sha256="a" * 64),
        assets=[
            AssetReferenceRecord(
                id="subject",
                path=asset.relative_to(project).as_posix(),
                sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),
            )
        ],
        layers=[SceneLayerAuthoringRecord(id="foreground", name="Foreground")],
        objects=[],
        groups=[],
    )


def run(output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    project = output / "project"
    asset = project / "assets" / "scene" / "subject.png"
    asset.parent.mkdir(parents=True, exist_ok=True)
    _write_image(asset)
    result = vectorize_image_file(asset)
    transform = SceneTransformRecord(
        position=Point3Record(x=20.0, y=30.0, z=0.0),
        rotation=Point3Record(x=0.0, y=0.0, z=0.0),
        scale=Point3Record(x=1.0, y=1.0, z=1.0),
        pivot=PointRecord(x=0.5, y=0.5),
    )
    session = SceneAuthoringSession(SceneAuthoringModel(_document(project, asset)))
    session.add_vector_object(
        result,
        object_id="subject-object",
        asset_id="subject",
        layer_id="foreground",
        transform=transform,
        edited_polygon=[(24, 18), (110, 20), (103, 77), (24, 77)],
        collision_strategy="convex_hull",
    )
    first = session.document.objects[0]
    if first.vector_geometry is None or not first.vector_geometry.collision_polygon:
        raise AssertionError("vector object did not receive collision geometry")
    session.set_selection(["subject-object"])
    copies = session.duplicate_selected()
    if copies != ("subject-object__copy",) or len(session.document.objects) != 2:
        raise AssertionError("vector object duplication was not deterministic")
    scene_path = project / "scene.ndtscene.json"
    save_scene_authoring(session.document, scene_path)
    restored = load_scene_authoring(scene_path)
    if len(restored.objects) != 2 or restored.objects[1].vector_geometry is None:
        raise AssertionError("vector geometry was not preserved by save/reopen")

    asset.write_bytes(b"tampered")
    try:
        load_scene_authoring(scene_path)
    except SceneAuthoringAssetError as exc:
        tamper_code = str(exc)
    else:
        raise AssertionError("tampered source asset was accepted")

    clean = _source_tree_clean()
    report = {
        "schema_version": 1,
        "stage": "e09-c-vector-scene-resource-phase3",
        "status": "PASS" if clean else "FAIL",
        "source": {"sha256": result.source_sha256, "tree_clean": clean},
        "object_count_after_duplicate": len(restored.objects),
        "collision_vertex_count": len(first.vector_geometry.collision_polygon),
        "save_reopen_preserved_geometry": restored.objects[0].vector_geometry
        == first.vector_geometry,
        "tampered_asset_rejected": "hash" in tamper_code.lower(),
        "tampered_asset_diagnostic": tamper_code,
        "limitations": [
            "The E09-C contract is integrated into the professional scene "
            "document; native vector contour panel rendering remains a UI follow-up.",
            "Engine export/import consumes this persisted resource in E10; this "
            "phase proves internal save/reopen and collision data, not engine runtime.",
        ],
    }
    (output / "stage3-e09-c-vector-scene-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
