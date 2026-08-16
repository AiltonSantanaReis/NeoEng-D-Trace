"""JSON metadata exporter for NeoEng-D-Trace.

Implementation preserved in the single ``src`` source tree.
The persistent JSON structures and serialization behavior are preserved.
"""

# src/exporters/json_exporter.py
import json
import math
import os
import tempfile
from typing import Any, Dict, List

from src.exporters.collision_exporter import collision_shape_record
from src.models.scene import Scene

SCENE_METADATA_FORMAT_ID = "neoeng-d-trace-scene-metadata"
OBJECT_METADATA_FORMAT_ID = "neoeng-d-trace-object-metadata"
METADATA_SCHEMA_VERSION = 1


def _object_rect_and_pivot(
    scene: Scene, obj_id: str
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    """Return image rect, pixel pivot and normalized pivot for one object."""

    obj = scene.objects[obj_id]
    if obj.polygon and len(obj.polygon) >= 3:
        xs = [float(point[0]) for point in obj.polygon]
        ys = [float(point[1]) for point in obj.polygon]
        x = min(xs)
        y = min(ys)
        w = max(xs) - x
        h = max(ys) - y
    else:
        x, y, w, h = 0.0, 0.0, 0.0, 0.0

    normalized = getattr(obj, "pivot", (0.5, 0.5))
    if (
        not isinstance(normalized, (tuple, list))
        or len(normalized) != 2
        or isinstance(normalized[0], bool)
        or isinstance(normalized[1], bool)
    ):
        raise ValueError(f"Object {obj_id} has an invalid normalized pivot")
    pivot_normalized = {"x": float(normalized[0]), "y": float(normalized[1])}
    if not all(math.isfinite(value) for value in pivot_normalized.values()):
        raise ValueError(f"Object {obj_id} has an invalid normalized pivot")
    pivot_pixels = {
        "x": w * pivot_normalized["x"],
        "y": h * pivot_normalized["y"],
    }
    return {"x": x, "y": y, "w": w, "h": h}, pivot_pixels, pivot_normalized


def build_object_metadata(scene: Scene, oid: str) -> Dict[str, Any]:
    """Build canonical, profile-neutral metadata for one scene object."""

    if oid not in scene.objects:
        raise ValueError(f"Object {oid} not found in scene")
    obj = scene.objects[oid]
    rect, pivot, pivot_normalized = _object_rect_and_pivot(scene, oid)
    x, y = rect["x"], rect["y"]
    group = next((item.id for item in scene.groups if oid in item.members), None)
    polygon = obj.polygon if obj.polygon else []
    return {
        "id": oid,
        "layer": obj.layer_id or "layer_default",
        "group": group,
        "trimmed": True,
        "padding": 4,
        "rect": rect,
        "rect_trimmed": {
            "x": 0.0,
            "y": 0.0,
            "w": rect["w"],
            "h": rect["h"],
        },
        "pivot": pivot,
        "pivot_normalized": pivot_normalized,
        "polygon_in_image": polygon,
        "polygon_in_sprite": [[px - x, py - y] for px, py in polygon],
        "collision": collision_shape_record(scene, oid),
    }


def _get_profile_formatter(profile: str):
    """Return the formatter for a supported engine profile.

    Explicit imports keep the dispatch auditable and avoid loading
    arbitrary modules from user-controlled profile names.
    """
    normalized = profile.strip().lower()

    if normalized == "unity":
        from src.exporters.profiles.unity import format_metadata

        return format_metadata
    if normalized == "godot":
        from src.exporters.profiles.godot import format_metadata

        return format_metadata
    if normalized == "phaser":
        from src.exporters.profiles.phaser import format_metadata

        return format_metadata

    raise ValueError(f"Unsupported export profile: {profile}")


def export_scene_metadata(scene: Scene, profile: str = "default") -> Dict[str, Any]:
    """
    Exporta metadados da cena para dicionário JSON.

    Args:
        scene: Instância da Scene.
        profile: Perfil de exportação ('default', 'unity', 'godot').

    Returns:
        Dicionário com metadados serializáveis.
    """
    objects_data: List[Dict[str, Any]] = [
        build_object_metadata(scene, oid) for oid in scene.objects
    ]

    data: Dict[str, Any] = {
        "format_id": SCENE_METADATA_FORMAT_ID,
        "schema_version": METADATA_SCHEMA_VERSION,
        "sprites": objects_data,
        "layers": [
            {
                "id": layer.id,
                "name": layer.name,
                "visible": layer.visible,
                "locked": layer.locked,
            }
            for layer in scene.layers
        ],
        "groups": [
            {
                "id": g.id,
                "name": g.name,
                "visible": g.visible,
                "locked": g.locked,
                "members": list(g.members),
            }
            for g in scene.groups
        ],
    }

    normalized_profile = profile.strip().lower()
    if normalized_profile in {"", "default", "generic"}:
        data["profile"] = "generic"
    else:
        formatter = _get_profile_formatter(normalized_profile)
        data["profile"] = normalized_profile
        data["sprites"] = [formatter(sprite) for sprite in data["sprites"]]

    return data


def save_json_metadata(metadata: Dict[str, Any], path: str):
    """Save metadata with an atomic same-filesystem replacement."""
    dirn = os.path.dirname(path)
    if dirn:
        os.makedirs(dirn, exist_ok=True)

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
            dir=dirn or ".",
            encoding="utf-8",
        ) as tmp:
            json.dump(metadata, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = tmp.name

        # os.replace replaces an existing destination on Windows and POSIX.
        # Removing the destination first would create a data-loss window.
        os.replace(tmp_path, path)
        tmp_path = None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def export_metadata(
    obj_id: str, scene: Scene, out_json_path: str, profile: str = "generic"
) -> Dict[str, Any]:
    """
    Exporta metadados JSON para um objeto específico.
    """
    if obj_id not in scene.objects:
        raise ValueError(f"Object {obj_id} not found in scene")
    obj = scene.objects[obj_id]

    if not obj.polygon or len(obj.polygon) < 3:
        raise ValueError(f"Object {obj_id} has invalid polygon")

    common = build_object_metadata(scene, obj_id)
    metadata = {
        "format_id": OBJECT_METADATA_FORMAT_ID,
        "schema_version": METADATA_SCHEMA_VERSION,
        "coordinate_space": "image",
        "id": obj_id,
        "rect": common["rect"],
        "pivot": common["pivot"],
        "pivot_normalized": common["pivot_normalized"],
        "polygon": common["polygon_in_sprite"],
        "layer": common["layer"],
        "group": common["group"],
        "trimmed": common["trimmed"],
        "padding": common["padding"],
        "collision": common["collision"],
    }

    # Preserve the generic contract and dispatch engine-specific profiles
    # through their dedicated formatters. These modules are part of the
    # public export surface and must not become disconnected from this entrypoint.
    normalized_profile = profile.strip().lower()
    if normalized_profile in {"", "default", "generic"}:
        formatted = metadata
    else:
        formatter = _get_profile_formatter(normalized_profile)
        formatted = formatter(metadata)

    # Save to file
    if out_json_path:
        save_json_metadata(formatted, out_json_path)

    return formatted
