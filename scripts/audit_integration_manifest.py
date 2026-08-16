"""Produce reproducible stage-one integration manifest artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from src.exporters.integration_manifest import (
    build_integration_manifest,
    save_integration_manifest,
)
from src.exporters.json_exporter import export_scene_metadata
from src.models.scene import Scene


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/evidence/artifacts/integration-manifest"),
    )
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)

    image_path = output / "source.png"
    Image.new("RGBA", (16, 12), (18, 42, 58, 255)).save(image_path)

    scene = Scene()
    scene.add_object("hero", [(1, 2), (15, 2), (15, 10), (1, 10)])
    metadata = export_scene_metadata(scene)

    outputs: list[Path] = [image_path]
    for engine in ("godot", "unity"):
        manifest = build_integration_manifest(
            metadata,
            engine=engine,
            image_path=image_path,
            image_reference="source.png",
        )
        manifest_path = output / f"{engine}.integration.json"
        save_integration_manifest(manifest, manifest_path)
        outputs.append(manifest_path)

    index = {
        "format_id": "neoeng-d-trace-integration-audit-artifacts",
        "schema_version": 1,
        "artifacts": [{"path": path.name, "sha256": _sha256(path)} for path in outputs],
    }
    index_path = output / "artifact-index.json"
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    newline="\n",
    )
    print(json.dumps(index, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
