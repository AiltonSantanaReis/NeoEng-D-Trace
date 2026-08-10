"""JSON metadata exporter for NeoEng-D-Trace.

Implementation preserved in the single ``src`` source tree.
The persistent JSON structures and serialization behavior are preserved.
"""

# src/exporters/json_exporter.py
import json
import os
import tempfile
from typing import Any, Dict, List

from src.models.scene import Scene


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
    objects_data: List[Dict[str, Any]] = []
    for oid, obj in scene.objects.items():
        if obj.polygon and len(obj.polygon) >= 3:
            xs = [p[0] for p in obj.polygon]
            ys = [p[1] for p in obj.polygon]
            x = min(xs)
            y = min(ys)
            w = max(xs) - x
            h = max(ys) - y
        else:
            x, y, w, h = 0, 0, 0, 0

        # Trimmed rect (em sprite space)
        rect_trimmed = {"x": 0, "y": 0, "w": w, "h": h}
        pivot = {"x": 0.5, "y": 0.5}

        group = None
        for g in scene.groups:
            if oid in g.members:
                group = g.id
                break

        polygon_in_sprite = (
            [[px - x, py - y] for px, py in obj.polygon] if obj.polygon else []
        )

        entry = {
            "id": oid,
            "layer": obj.layer_id or "layer_default",
            "group": group,
            "trimmed": True,
            "padding": 4,
            "rect": {"x": x, "y": y, "w": w, "h": h},
            "rect_trimmed": rect_trimmed,
            "pivot": pivot,
            "polygon_in_image": obj.polygon,
            "polygon_in_sprite": polygon_in_sprite,
        }
        objects_data.append(entry)

    data = {
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

    # Apply profile transformations directly here
    if profile == "unity":
        for sprite in data["sprites"]:
            # Unity expects normalized pivots relative to trimmed rect
            w = sprite["rect_trimmed"]["w"]
            h = sprite["rect_trimmed"]["h"]
            if w > 0:
                sprite["pivot"]["x"] /= w
            if h > 0:
                sprite["pivot"]["y"] /= h

    elif profile == "godot":
        # Godot uses offset from center, usually no change needed here
        # unless specific sprite sheet format is required.
        pass

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

    xs = [p[0] for p in obj.polygon]
    ys = [p[1] for p in obj.polygon]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    w = max_x - min_x
    h = max_y - min_y
    rect = {"x": min_x, "y": min_y, "w": w, "h": h}

    # Default pivot at center relative to sprite origin (0,0)
    pivot = {"x": w / 2, "y": h / 2}

    # Polygon relative to sprite top-left
    polygon = [[px - min_x, py - min_y] for px, py in obj.polygon]

    layer = getattr(obj, "layer_id", "Default")
    group = None
    for g in getattr(scene, "groups", []):
        if obj_id in getattr(g, "members", []):
            group = g.id
            break

    metadata = {
        "id": obj_id,
        "rect": rect,
        "pivot": pivot,
        "polygon": polygon,
        "layer": layer,
        "group": group,
        "trimmed": True,
        "padding": 4,
    }

    # Preserve the generic contract and dispatch engine-specific profiles
    # through their dedicated formatters. These modules are part of the
    # public export surface and must not become disconnected from this entrypoint.
    if profile in {"", "default", "generic"}:
        formatted = metadata
    else:
        formatter = _get_profile_formatter(profile)
        formatted = formatter(metadata)

    # Save to file
    if out_json_path:
        save_json_metadata(formatted, out_json_path)

    return formatted
