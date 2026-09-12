"""Deterministic E12 package for animation plus a bounded 3D vertical slice.

The package deliberately stops at a validated hybrid slice.  It does not claim
the complete Professional 3D release described by the master plans.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Any, Mapping

from src.exporters.composition_export import validate_composition_package

HYBRID_FORMAT_ID = "neoeng-d-trace-hybrid-composition"
HYBRID_SCHEMA_VERSION = 1
HYBRID_RUNTIME_FORMAT_ID = "neoeng-d-trace-hybrid-runtime"
HYBRID_RUNTIME_SCHEMA_VERSION = 1
HYBRID_RUNTIME_SCENE_FORMAT_ID = "neoeng-d-trace-hybrid-runtime-scene"
HYBRID_RUNTIME_SCENE_SCHEMA_VERSION = 1


class HybridCompositionExportError(ValueError):
    """Raised when an E12 hybrid package is invalid or unsafe."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _read_json(path: Path, kind: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HybridCompositionExportError(f"invalid {kind}: {path}") from exc
    if not isinstance(payload, dict):
        raise HybridCompositionExportError(f"{kind} must be an object")
    return payload


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HybridCompositionExportError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise HybridCompositionExportError(f"{name} must be finite")
    return result


def _vector(value: Any, name: str, size: int) -> list[float]:
    if not isinstance(value, list) or len(value) != size:
        raise HybridCompositionExportError(f"{name} must contain {size} values")
    return [_number(item, f"{name}[{index}]") for index, item in enumerate(value)]


def _safe_relative_path(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise HybridCompositionExportError(f"{name} must be a safe relative path")
    path = Path(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise HybridCompositionExportError(f"{name} must be a safe relative path")
    return path.as_posix()


def _binding(path: Path, root: Path) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    return {
        "path": relative,
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "required": True,
    }


def _resolve_binding(root: Path, binding: object, name: str) -> Path:
    if not isinstance(binding, Mapping):
        raise HybridCompositionExportError(f"{name} binding is invalid")
    relative = _safe_relative_path(binding.get("path"), f"{name}.path")
    path = root / relative
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise HybridCompositionExportError(f"{name} path escapes package") from exc
    if not path.is_file() or path.is_symlink():
        raise HybridCompositionExportError(f"{name} file is missing or unsafe")
    if path.stat().st_size != binding.get("bytes") or _sha256(path) != binding.get(
        "sha256"
    ):
        raise HybridCompositionExportError(
            f"{name} file hash mismatch or size mismatch"
        )
    return path


def _point(value: list[float]) -> dict[str, float]:
    return {"x": float(value[0]), "y": float(value[1]), "z": float(value[2])}


def _runtime_scene_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize array-heavy authoring JSON for native engine runtimes.

    Unity's source-only runtime contract intentionally consumes objects with
    named scalar fields rather than relying on nested JSON arrays.  Godot uses
    the same normalized contract, so both adapters receive identical data.
    The original ``hybrid3d.json`` remains in the package and is hash-bound by
    the runtime manifest.
    """

    camera = payload["camera"]
    materials = []
    for material in payload["materials"]:
        materials.append(
            {
                "id": material["id"],
                "metallic": float(material["metallic"]),
                "roughness": float(material["roughness"]),
                "base_color": material.get("base_color", [0.15, 0.72, 0.95, 1.0]),
            }
        )
    meshes = []
    for mesh in payload["meshes"]:
        meshes.append(
            {
                "id": mesh["id"],
                "material_id": mesh["material_id"],
                "position": _point(mesh.get("position", [0.0, 0.0, 0.0])),
                "vertices": [_point(vertex) for vertex in mesh["vertices"]],
                "triangles": [
                    {
                        "a": int(triangle[0]),
                        "b": int(triangle[1]),
                        "c": int(triangle[2]),
                    }
                    for triangle in mesh["triangles"]
                ],
            }
        )
    lights = []
    for light in payload["lights"]:
        lights.append(
            {
                "id": light["id"],
                "type": light["type"],
                "intensity": float(light["intensity"]),
                "position": _point(light.get("position", [0.0, 0.0, 0.0])),
            }
        )
    clips = []
    for clip in payload["animation_clips"]:
        clips.append(
            {
                "id": clip.get("id", "clip"),
                "mesh_id": clip["mesh_id"],
                "keyframes": [
                    {
                        "time": float(keyframe["time"]),
                        "position": _point(keyframe["position"]),
                    }
                    for keyframe in clip["keyframes"]
                ],
            }
        )
    return {
        "format_id": HYBRID_RUNTIME_SCENE_FORMAT_ID,
        "schema_version": HYBRID_RUNTIME_SCENE_SCHEMA_VERSION,
        "support_status": payload["support_status"],
        "camera": {
            "projection": camera["projection"],
            "fov_degrees": float(camera["fov_degrees"]),
            "near": float(camera["near"]),
            "far": float(camera["far"]),
            "position": _point(camera["position"]),
            "target": _point(camera["target"]),
        },
        "materials": materials,
        "meshes": meshes,
        "lights": lights,
        "animation_clips": clips,
    }


def validate_hybrid_scene(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the bounded 3D vertical-slice contract."""

    if payload.get("format_id") != "neoeng-d-trace-hybrid-3d-scene":
        raise HybridCompositionExportError("unsupported hybrid 3D scene format")
    if payload.get("schema_version") != 1:
        raise HybridCompositionExportError("unsupported hybrid 3D scene schema")
    if payload.get("support_status") != "VERTICAL_SLICE_ONLY":
        raise HybridCompositionExportError("hybrid 3D support status must be explicit")
    camera = payload.get("camera")
    if not isinstance(camera, dict) or camera.get("projection") != "perspective":
        raise HybridCompositionExportError("hybrid camera must be perspective")
    fov = _number(camera.get("fov_degrees"), "camera.fov_degrees")
    _number(camera.get("near"), "camera.near")
    _number(camera.get("far"), "camera.far")
    if not 1.0 <= fov < 180.0:
        raise HybridCompositionExportError("camera.fov_degrees is invalid")
    if float(camera["near"]) <= 0 or float(camera["far"]) <= float(camera["near"]):
        raise HybridCompositionExportError("camera clipping range is invalid")
    _vector(camera.get("position"), "camera.position", 3)
    _vector(camera.get("target"), "camera.target", 3)

    materials = payload.get("materials")
    if not isinstance(materials, list) or not materials:
        raise HybridCompositionExportError("at least one 3D material is required")
    material_ids: set[str] = set()
    for material in materials:
        if not isinstance(material, dict) or not isinstance(material.get("id"), str):
            raise HybridCompositionExportError("3D material record is invalid")
        material_id = material["id"]
        if not material_id or material_id in material_ids:
            raise HybridCompositionExportError("3D material IDs must be unique")
        material_ids.add(material_id)
        _number(material.get("metallic"), f"material {material['id']}.metallic")
        _number(material.get("roughness"), f"material {material['id']}.roughness")

    meshes = payload.get("meshes")
    if not isinstance(meshes, list) or not meshes:
        raise HybridCompositionExportError("at least one 3D mesh is required")
    mesh_ids: set[str] = set()
    for mesh in meshes:
        if not isinstance(mesh, dict) or not isinstance(mesh.get("id"), str):
            raise HybridCompositionExportError("3D mesh record is invalid")
        mesh_id = mesh["id"]
        if not mesh_id or mesh_id in mesh_ids:
            raise HybridCompositionExportError("3D mesh IDs must be unique")
        mesh_ids.add(mesh_id)
        vertices = mesh.get("vertices")
        triangles = mesh.get("triangles")
        if not isinstance(vertices, list) or len(vertices) < 3:
            raise HybridCompositionExportError("3D mesh needs at least 3 vertices")
        for index, vertex in enumerate(vertices):
            _vector(vertex, f"mesh {mesh['id']}.vertices[{index}]", 3)
        if (
            not isinstance(triangles, list)
            or not triangles
            or any(
                not isinstance(triangle, list)
                or len(triangle) != 3
                or any(
                    isinstance(item, bool)
                    or not isinstance(item, int)
                    or item < 0
                    or item >= len(vertices)
                    for item in triangle
                )
                for triangle in triangles
            )
        ):
            raise HybridCompositionExportError("3D mesh triangles are invalid")
        material_id = mesh.get("material_id")
        if material_id not in material_ids:
            raise HybridCompositionExportError("3D mesh references an unknown material")
        _vector(mesh.get("position", [0, 0, 0]), f"mesh {mesh['id']}.position", 3)

    lights = payload.get("lights")
    if not isinstance(lights, list) or not lights:
        raise HybridCompositionExportError("at least one 3D light is required")
    light_ids: set[str] = set()
    for light in lights:
        if not isinstance(light, dict) or light.get("type") not in {
            "directional",
            "point",
        }:
            raise HybridCompositionExportError("3D light type is invalid")
        light_id = light.get("id")
        if not isinstance(light_id, str) or not light_id or light_id in light_ids:
            raise HybridCompositionExportError("3D light IDs must be unique")
        light_ids.add(light_id)
        _number(light.get("intensity"), "light.intensity")
        _vector(light.get("position", [0, 0, 0]), "light.position", 3)

    clips = payload.get("animation_clips")
    if not isinstance(clips, list) or not clips:
        raise HybridCompositionExportError(
            "at least one hybrid animation clip is required"
        )
    for clip in clips:
        if not isinstance(clip, dict) or clip.get("mesh_id") not in mesh_ids:
            raise HybridCompositionExportError(
                "animation clip references an unknown mesh"
            )
        keyframes = clip.get("keyframes")
        if not isinstance(keyframes, list) or len(keyframes) < 2:
            raise HybridCompositionExportError("animation clip needs two keyframes")
        previous = -1.0
        for keyframe in keyframes:
            if not isinstance(keyframe, dict):
                raise HybridCompositionExportError("animation keyframe is invalid")
            time = _number(keyframe.get("time"), "animation keyframe.time")
            if time < previous:
                raise HybridCompositionExportError(
                    "animation keyframes must be ordered"
                )
            previous = time
            _vector(keyframe.get("position"), "animation keyframe.position", 3)
    return dict(payload)


def _copy_component(
    source: Path, destination: Path, kind: str, package_root: Path | None = None
) -> dict[str, Any]:
    if not source.is_file() or source.is_symlink():
        raise HybridCompositionExportError(f"unsafe or missing E12 component: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    relative_path = (
        destination.relative_to(package_root).as_posix()
        if package_root is not None
        else destination.name
    )
    return {
        "kind": kind,
        "path": relative_path,
        "bytes": destination.stat().st_size,
        "sha256": _sha256(destination),
        "required": True,
    }


def _copy_tree(
    source: Path, destination: Path, kind: str, package_root: Path
) -> list[dict[str, Any]]:
    if not source.is_dir() or source.is_symlink():
        raise HybridCompositionExportError(f"unsafe or missing E12 directory: {source}")
    components: list[dict[str, Any]] = []
    for path in sorted(source.rglob("*")):
        if path.is_dir():
            continue
        relative = path.relative_to(source)
        components.append(
            _copy_component(path, destination / relative, kind, package_root)
        )
    if not components:
        raise HybridCompositionExportError(f"E12 directory is empty: {source}")
    return components


def build_hybrid_composition_package(
    composition_package: str | Path,
    animation_directory: str | Path,
    hybrid_scene: Mapping[str, Any] | str | Path,
    output_directory: str | Path,
) -> dict[str, Any]:
    """Build one hash-bound E12 package from E11 composition inputs."""

    composition_root = Path(composition_package)
    validate_composition_package(composition_root)
    animation_root = Path(animation_directory)
    animation_manifest = _read_json(
        animation_root / "animation.json", "animation manifest"
    )
    if (
        animation_manifest.get("format_id") != "neoeng-d-trace-animation"
        or animation_manifest.get("schema_version") != 1
        or not isinstance(animation_manifest.get("frames"), list)
        or animation_manifest.get("frame_count") != len(animation_manifest["frames"])
    ):
        raise HybridCompositionExportError("animation manifest contract is invalid")
    hybrid_payload = (
        _read_json(Path(hybrid_scene), "hybrid scene")
        if isinstance(hybrid_scene, (str, Path))
        else dict(hybrid_scene)
    )
    validate_hybrid_scene(hybrid_payload)
    target = Path(output_directory)
    if target.exists():
        raise HybridCompositionExportError(
            f"refusing to overwrite E12 package: {target}"
        )
    target.mkdir(parents=True)
    components = _copy_tree(
        composition_root, target / "composition", "composition", target
    )
    components.extend(
        _copy_tree(animation_root, target / "animation", "animation", target)
    )
    hybrid_path = target / "hybrid3d.json"
    hybrid_path.write_bytes(_canonical_json(hybrid_payload))
    components.append(
        {
            "kind": "hybrid-3d-scene",
            "path": "hybrid3d.json",
            "bytes": hybrid_path.stat().st_size,
            "sha256": _sha256(hybrid_path),
            "required": True,
        }
    )
    runtime_scene_path = target / "hybrid-runtime-scene.json"
    runtime_scene_path.write_bytes(
        _canonical_json(_runtime_scene_payload(hybrid_payload))
    )
    components.append(
        {
            "kind": "hybrid-runtime-scene",
            "path": "hybrid-runtime-scene.json",
            "bytes": runtime_scene_path.stat().st_size,
            "sha256": _sha256(runtime_scene_path),
            "required": True,
        }
    )
    animation_manifest_path = target / "animation" / "animation.json"
    animation_manifest = _read_json(animation_manifest_path, "animation manifest")
    first_frame_path = (
        target
        / "animation"
        / Path(
            _safe_relative_path(
                animation_manifest["frames"][0]["texture"],
                "animation.frames[0].texture",
            )
        )
    )
    try:
        first_frame_path.relative_to(target / "animation")
    except ValueError as exc:
        raise HybridCompositionExportError(
            "animation first frame escapes package"
        ) from exc
    runtime_manifest = {
        "format_id": HYBRID_RUNTIME_FORMAT_ID,
        "schema_version": HYBRID_RUNTIME_SCHEMA_VERSION,
        "support_status": "VERTICAL_SLICE_ONLY",
        "scene": {
            "authoring": _binding(hybrid_path, target),
            "normalized": _binding(runtime_scene_path, target),
        },
        "animation": {
            "manifest": _binding(animation_manifest_path, target),
            "first_frame": _binding(first_frame_path, target),
            "frame_count": animation_manifest["frame_count"],
        },
        "capabilities": {
            "camera": "perspective",
            "geometry": "inline-mesh-triangles",
            "lighting": ["directional", "point"],
            "animation": "position-keyframes",
        },
    }
    runtime_manifest_path = target / "hybrid-runtime.json"
    runtime_manifest_path.write_bytes(_canonical_json(runtime_manifest))
    components.append(
        {
            "kind": "hybrid-runtime-manifest",
            "path": "hybrid-runtime.json",
            "bytes": runtime_manifest_path.stat().st_size,
            "sha256": _sha256(runtime_manifest_path),
            "required": True,
        }
    )
    manifest = {
        "format_id": HYBRID_FORMAT_ID,
        "schema_version": HYBRID_SCHEMA_VERSION,
        "support_status": "VERTICAL_SLICE_ONLY",
        "generator": {"id": "neoeng_d_trace", "version": "0.3.0"},
        "composition_manifest_sha256": _sha256(composition_root / "composition.json"),
        "animation_manifest_sha256": _sha256(animation_root / "animation.json"),
        "runtime_manifest_sha256": _sha256(runtime_manifest_path),
        "components": sorted(components, key=lambda item: item["path"]),
        "capabilities": {
            "composition_2d_25d": "preserved-e11-package",
            "animation": "coherent-frame-playback",
            "hybrid_3d": "perspective-mesh-material-light-vertical-slice",
            "hybrid_3d_runtime": "native-godot-unity-vertical-slice",
        },
    }
    (target / "hybrid-composition.json").write_bytes(_canonical_json(manifest))
    return manifest


def validate_hybrid_runtime_manifest(package: str | Path) -> dict[str, Any]:
    """Validate the hash-bound payload consumed by native 3D adapters."""

    root = Path(package)
    manifest = _read_json(root / "hybrid-runtime.json", "hybrid runtime manifest")
    if (
        manifest.get("format_id") != HYBRID_RUNTIME_FORMAT_ID
        or manifest.get("schema_version") != HYBRID_RUNTIME_SCHEMA_VERSION
        or manifest.get("support_status") != "VERTICAL_SLICE_ONLY"
    ):
        raise HybridCompositionExportError("hybrid runtime manifest schema is invalid")
    scene = manifest.get("scene")
    if not isinstance(scene, Mapping):
        raise HybridCompositionExportError("hybrid runtime scene bindings are invalid")
    authoring_path = _resolve_binding(root, scene.get("authoring"), "scene.authoring")
    normalized_path = _resolve_binding(
        root, scene.get("normalized"), "scene.normalized"
    )
    validate_hybrid_scene(_read_json(authoring_path, "hybrid scene"))
    normalized = _read_json(normalized_path, "hybrid runtime scene")
    if (
        normalized.get("format_id") != HYBRID_RUNTIME_SCENE_FORMAT_ID
        or normalized.get("schema_version") != HYBRID_RUNTIME_SCENE_SCHEMA_VERSION
        or normalized.get("support_status") != "VERTICAL_SLICE_ONLY"
    ):
        raise HybridCompositionExportError("hybrid runtime scene schema is invalid")
    for key in ("camera", "materials", "meshes", "lights", "animation_clips"):
        if key not in normalized:
            raise HybridCompositionExportError(f"hybrid runtime scene is missing {key}")
    animation = manifest.get("animation")
    if not isinstance(animation, Mapping):
        raise HybridCompositionExportError(
            "hybrid runtime animation bindings are invalid"
        )
    animation_manifest_path = _resolve_binding(
        root, animation.get("manifest"), "animation.manifest"
    )
    first_frame_path = _resolve_binding(
        root, animation.get("first_frame"), "animation.first_frame"
    )
    animation_manifest = _read_json(animation_manifest_path, "animation manifest")
    frames = animation_manifest.get("frames")
    if (
        animation_manifest.get("format_id") != "neoeng-d-trace-animation"
        or animation_manifest.get("schema_version") != 1
        or not isinstance(frames, list)
        or not frames
        or animation.get("frame_count") != animation_manifest.get("frame_count")
    ):
        raise HybridCompositionExportError(
            "hybrid runtime animation contract is invalid"
        )
    expected_first = (
        root
        / "animation"
        / Path(
            _safe_relative_path(frames[0].get("texture"), "animation.frames[0].texture")
        )
    )
    if expected_first != first_frame_path:
        raise HybridCompositionExportError(
            "hybrid runtime first animation frame binding is inconsistent"
        )
    return manifest


def validate_hybrid_composition_package(package: str | Path) -> dict[str, Any]:
    root = Path(package)
    manifest = _read_json(root / "hybrid-composition.json", "hybrid manifest")
    if (
        manifest.get("format_id") != HYBRID_FORMAT_ID
        or manifest.get("schema_version") != HYBRID_SCHEMA_VERSION
        or manifest.get("support_status") != "VERTICAL_SLICE_ONLY"
        or not isinstance(manifest.get("components"), list)
        or not manifest["components"]
    ):
        raise HybridCompositionExportError("hybrid manifest schema is invalid")
    validate_composition_package(root / "composition")
    animation_root = root / "animation"
    animation_manifest_path = animation_root / "animation.json"
    animation_manifest = _read_json(animation_manifest_path, "animation manifest")
    if (
        animation_manifest.get("format_id") != "neoeng-d-trace-animation"
        or animation_manifest.get("schema_version") != 1
        or not isinstance(animation_manifest.get("frames"), list)
        or animation_manifest.get("frame_count") != len(animation_manifest["frames"])
        or not animation_manifest["frames"]
    ):
        raise HybridCompositionExportError("animation manifest contract is invalid")
    for frame in animation_manifest["frames"]:
        if not isinstance(frame, dict) or not isinstance(frame.get("texture"), str):
            raise HybridCompositionExportError("animation frame record is invalid")
        texture = animation_root / Path(frame["texture"])
        try:
            texture.relative_to(animation_root)
        except ValueError as exc:
            raise HybridCompositionExportError(
                "animation texture path is unsafe"
            ) from exc
        if not texture.is_file() or texture.is_symlink():
            raise HybridCompositionExportError("animation texture is missing or unsafe")
    validate_hybrid_scene(_read_json(root / "hybrid3d.json", "hybrid scene"))
    expected_hashes = {
        "composition": manifest.get("composition_manifest_sha256"),
        "animation": manifest.get("animation_manifest_sha256"),
    }
    actual_hashes = {
        "composition": _sha256(root / "composition" / "composition.json"),
        "animation": _sha256(animation_manifest_path),
    }
    if expected_hashes != actual_hashes:
        raise HybridCompositionExportError("nested manifest hash mismatch")
    runtime_path = root / "hybrid-runtime.json"
    if manifest.get("runtime_manifest_sha256") is not None or runtime_path.exists():
        if manifest.get("runtime_manifest_sha256") != _sha256(runtime_path):
            raise HybridCompositionExportError("runtime manifest hash mismatch")
        validate_hybrid_runtime_manifest(root)
    seen_paths: set[str] = set()
    for component in manifest.get("components", []):
        if not isinstance(component, dict) or not component.get("required"):
            raise HybridCompositionExportError("hybrid component record is invalid")
        relative_value = str(component.get("path", ""))
        path = root / Path(relative_value)
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise HybridCompositionExportError(
                "hybrid component path is unsafe"
            ) from exc
        if not relative_value or "\\" in relative_value or relative_value in seen_paths:
            raise HybridCompositionExportError(
                "hybrid component path is unsafe or duplicated"
            )
        seen_paths.add(relative_value)
        if not path.is_file() or path.is_symlink():
            raise HybridCompositionExportError("hybrid component is missing or unsafe")
        if path.stat().st_size != component.get("bytes") or _sha256(
            path
        ) != component.get("sha256"):
            raise HybridCompositionExportError(
                f"hybrid component hash mismatch: {path}"
            )
    return manifest


__all__ = [
    "HYBRID_FORMAT_ID",
    "HYBRID_SCHEMA_VERSION",
    "HYBRID_RUNTIME_FORMAT_ID",
    "HYBRID_RUNTIME_SCHEMA_VERSION",
    "HYBRID_RUNTIME_SCENE_FORMAT_ID",
    "HYBRID_RUNTIME_SCENE_SCHEMA_VERSION",
    "HybridCompositionExportError",
    "build_hybrid_composition_package",
    "validate_hybrid_scene",
    "validate_hybrid_runtime_manifest",
    "validate_hybrid_composition_package",
]
