#!/usr/bin/env python3
"""Validate the Unity-facing reference asset without relying on a GUI."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import struct
import sys
import tempfile
from pathlib import Path
from typing import Any


COMPONENTS = {
    5121: ("B", 1),
    5123: ("H", 2),
    5125: ("I", 4),
    5126: ("f", 4),
}
TYPE_COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


class ValidationError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path.name} must contain an object")
    return value


def _load_glb(path: Path) -> tuple[dict[str, Any], bytes]:
    payload = path.read_bytes()
    if len(payload) < 20:
        raise ValidationError("GLB is shorter than its header")
    magic, version, declared_length = struct.unpack_from("<4sII", payload, 0)
    if magic != b"glTF" or version != 2:
        raise ValidationError("GLB header is not glTF 2.0")
    if declared_length != len(payload):
        raise ValidationError("GLB declared length does not match file length")
    offset = 12
    json_data: bytes | None = None
    binary_data = b""
    while offset + 8 <= len(payload):
        chunk_length, chunk_type = struct.unpack_from("<I4s", payload, offset)
        offset += 8
        chunk = payload[offset : offset + chunk_length]
        if len(chunk) != chunk_length:
            raise ValidationError("GLB chunk exceeds file length")
        offset += chunk_length
        if chunk_type == b"JSON":
            json_data = chunk
        elif chunk_type == b"BIN\x00":
            binary_data = chunk
    if json_data is None or not binary_data:
        raise ValidationError("GLB must contain JSON and BIN chunks")
    gltf = json.loads(json_data.rstrip(b" \t\r\n\x00").decode("utf-8"))
    if not isinstance(gltf, dict):
        raise ValidationError("GLB JSON chunk must contain an object")
    return gltf, binary_data


def _accessor_values(
    gltf: dict[str, Any],
    accessor_index: int,
    binary: bytes,
) -> list[tuple[float, ...]]:
    accessors = gltf.get("accessors", [])
    views = gltf.get("bufferViews", [])
    accessor = accessors[accessor_index]
    component_type = int(accessor["componentType"])
    if component_type not in COMPONENTS:
        raise ValidationError(f"unsupported accessor component type {component_type}")
    fmt, component_size = COMPONENTS[component_type]
    component_count = TYPE_COMPONENTS[accessor["type"]]
    view = views[int(accessor["bufferView"])]
    stride = int(view.get("byteStride", component_size * component_count))
    element_size = component_size * component_count
    if stride < element_size:
        raise ValidationError("accessor byteStride is smaller than the element")
    start = int(view.get("byteOffset", 0)) + int(accessor.get("byteOffset", 0))
    count = int(accessor["count"])
    values: list[tuple[float, ...]] = []
    for index in range(count):
        element_start = start + index * stride
        element_end = element_start + element_size
        if element_end > len(binary):
            raise ValidationError("accessor reads beyond the binary buffer")
        unpacked = struct.unpack_from("<" + fmt * component_count, binary, element_start)
        values.append(tuple(float(value) for value in unpacked))
    return values


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _validate_hashes(asset_dir: Path) -> int:
    sums_path = asset_dir / "SHA256SUMS.txt"
    _assert(sums_path.is_file(), "SHA256SUMS.txt is missing")
    checked = 0
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, relative = line.split("  ", 1)
        target = asset_dir / relative
        _assert(target.is_file(), f"checksum target is missing: {relative}")
        _assert(_sha256(target) == digest, f"checksum mismatch: {relative}")
        checked += 1
    _assert(checked >= 20, "checksum manifest contains too few files")
    return checked


def _validate_glb_consistency(
    gltf: dict[str, Any],
    glb_gltf: dict[str, Any],
    glb_binary: bytes,
) -> None:
    _assert(gltf.get("asset", {}).get("version") == "2.0", "external glTF is not version 2.0")
    _assert(glb_gltf.get("asset", {}).get("version") == "2.0", "GLB is not version 2.0")
    _assert(len(gltf.get("meshes", [])) == len(glb_gltf.get("meshes", [])), "GLB mesh count differs from glTF")
    _assert(len(gltf.get("nodes", [])) == len(glb_gltf.get("nodes", [])), "GLB node count differs from glTF")
    _assert(len(gltf.get("materials", [])) == len(glb_gltf.get("materials", [])), "GLB material count differs from glTF")
    _assert(glb_gltf.get("buffers", [{}])[0].get("byteLength") == len(glb_binary), "GLB buffer length is invalid")
    for image in glb_gltf.get("images", []):
        _assert("bufferView" in image and "uri" not in image, "GLB image is not embedded")
        view = glb_gltf.get("bufferViews", [])[int(image["bufferView"])]
        end = int(view.get("byteOffset", 0)) + int(view["byteLength"])
        _assert(end <= len(glb_binary), "embedded GLB image exceeds binary buffer")


def _validate_materials(gltf: dict[str, Any]) -> int:
    textures = gltf.get("textures", [])
    images = gltf.get("images", [])
    materials = gltf.get("materials", [])
    _assert(len(materials) >= 4, "asset has too few PBR materials")
    for material in materials:
        pbr = material.get("pbrMetallicRoughness", {})
        for field in ("baseColorTexture", "metallicRoughnessTexture"):
            _assert(field in pbr, f"material {material.get('name')} misses {field}")
            texture_index = int(pbr[field]["index"])
            _assert(0 <= texture_index < len(textures), f"material {material.get('name')} has invalid texture index")
            source = int(textures[texture_index]["source"])
            _assert(0 <= source < len(images), "texture source index is invalid")
        _assert("normalTexture" in material, f"material {material.get('name')} misses normalTexture")
        normal_source = int(textures[int(material["normalTexture"]["index"])]["source"])
        _assert(0 <= normal_source < len(images), "normal texture source index is invalid")
    return len(materials)


def _validate_geometry(gltf: dict[str, Any], binary: bytes, manifest: dict[str, Any]) -> tuple[int, int]:
    meshes = gltf.get("meshes", [])
    nodes = gltf.get("nodes", [])
    _assert(len(meshes) >= 10, "asset has too few separate meshes")
    names = [str(mesh.get("name", "")) for mesh in meshes]
    _assert(all(names) and len(names) == len(set(names)), "mesh names must be non-empty and unique")
    mesh_nodes = [node for node in nodes if "mesh" in node]
    _assert(len(mesh_nodes) == len(meshes), "every mesh must have one visible node")
    _assert(all("skin" in node for node in mesh_nodes), "every visible mesh node must be skinned")
    component_names = {item["name"] for item in manifest.get("components", [])}
    _assert(component_names == set(names), "manifest component names differ from glTF mesh names")
    total_triangles = 0
    for mesh in meshes:
        primitives = mesh.get("primitives", [])
        _assert(len(primitives) == 1, f"mesh {mesh.get('name')} must have one primitive")
        primitive = primitives[0]
        _assert(int(primitive.get("mode", 4)) == 4, "all asset primitives must be triangles")
        attributes = primitive.get("attributes", {})
        required = ("POSITION", "NORMAL", "TEXCOORD_0", "JOINTS_0", "WEIGHTS_0")
        _assert(all(name in attributes for name in required), f"mesh {mesh.get('name')} misses a required attribute")
        positions = _accessor_values(gltf, int(attributes["POSITION"]), binary)
        normals = _accessor_values(gltf, int(attributes["NORMAL"]), binary)
        uvs = _accessor_values(gltf, int(attributes["TEXCOORD_0"]), binary)
        joints = _accessor_values(gltf, int(attributes["JOINTS_0"]), binary)
        weights = _accessor_values(gltf, int(attributes["WEIGHTS_0"]), binary)
        _assert(len(positions) >= 4, f"mesh {mesh.get('name')} is too small")
        _assert(len(positions) == len(normals) == len(uvs) == len(joints) == len(weights), "mesh attribute counts differ")
        for normal in normals:
            _assert(all(math.isfinite(value) for value in normal), "normal contains a non-finite value")
        for uv in uvs:
            _assert(all(-1e-6 <= value <= 1.000001 for value in uv), f"mesh {mesh.get('name')} has UV outside 0..1")
        for weight in weights:
            _assert(abs(sum(weight) - 1.0) <= 1e-4, f"mesh {mesh.get('name')} has unnormalized skin weights")
        indices = _accessor_values(gltf, int(primitive["indices"]), binary)
        _assert(len(indices) % 3 == 0 and indices, f"mesh {mesh.get('name')} has invalid triangle indices")
        _assert(max(int(value[0]) for value in indices) < len(positions), "mesh index exceeds vertex count")
        total_triangles += len(indices) // 3
    return len(meshes), total_triangles


def _validate_rig(gltf: dict[str, Any]) -> tuple[int, int]:
    skins = gltf.get("skins", [])
    _assert(len(skins) == 1, "asset must contain exactly one skin")
    skin = skins[0]
    joints = skin.get("joints", [])
    _assert(len(joints) >= 8, "skeleton has too few joints")
    _assert("inverseBindMatrices" in skin, "skin misses inverse bind matrices")
    inverse_count = int(gltf["accessors"][int(skin["inverseBindMatrices"])]["count"])
    _assert(inverse_count == len(joints), "inverse bind matrix count differs from joint count")
    animations = gltf.get("animations", [])
    idle = next((item for item in animations if item.get("name") == "Idle"), None)
    _assert(idle is not None, "Idle animation is missing")
    _assert(idle.get("samplers") and idle.get("channels"), "Idle animation has no channels")
    return len(joints), len(idle["channels"])


def _validate_obj(asset_dir: Path, mesh_count: int) -> None:
    obj_path = asset_dir / "eclipse_warden.obj"
    mtl_path = asset_dir / "eclipse_warden.mtl"
    _assert(obj_path.is_file() and mtl_path.is_file(), "OBJ/MTL export is missing")
    obj = obj_path.read_text(encoding="utf-8")
    mtl = mtl_path.read_text(encoding="utf-8")
    object_count = sum(line.startswith("o ") for line in obj.splitlines())
    material_count = sum(line.startswith("newmtl ") for line in mtl.splitlines())
    _assert(object_count == mesh_count, "OBJ object count differs from glTF mesh count")
    _assert(material_count >= 4 and obj.count("usemtl ") >= mesh_count, "OBJ material assignments are incomplete")


def _validate_no_machine_paths(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _validate_no_machine_paths(item)
    elif isinstance(value, list):
        for item in value:
            _validate_no_machine_paths(item)
    elif isinstance(value, str):
        windows_separator = chr(92)
        unix_user_marker = chr(47) + "Users" + chr(47)
        has_windows_user_path = (
            len(value) > 3
            and value[1:2] == ":"
            and windows_separator + "Users" + windows_separator in value
        )
        _assert(
            not has_windows_user_path and unix_user_marker not in value,
            "manifest leaks an absolute machine user path",
        )


def validate(asset_dir: Path, *, write_report: bool = True) -> dict[str, Any]:
    manifest = _read_json(asset_dir / "manifest.json")
    _assert(manifest.get("schema_version") == 1, "unsupported asset manifest schema")
    _validate_no_machine_paths(manifest)
    checksum_count = _validate_hashes(asset_dir)
    gltf = _read_json(asset_dir / "eclipse_warden.gltf")
    gltf_binary = (asset_dir / "eclipse_warden.bin").read_bytes()
    glb_gltf, glb_binary = _load_glb(asset_dir / "eclipse_warden.glb")
    _validate_glb_consistency(gltf, glb_gltf, glb_binary)
    mesh_count, triangle_count = _validate_geometry(gltf, gltf_binary, manifest)
    material_count = _validate_materials(gltf)
    joint_count, animation_channels = _validate_rig(gltf)
    _validate_obj(asset_dir, mesh_count)
    for texture in manifest.get("textures", []):
        path = asset_dir / texture["uri"]
        _assert(path.is_file(), f"manifest texture is missing: {texture['uri']}")
    report = {
        "status": "PASS",
        "schema": "neoeng-d-trace-reference-3d-asset-validation",
        "asset": manifest.get("asset", {}),
        "checks": {
            "checksum_files": checksum_count,
            "mesh_count": mesh_count,
            "triangle_count": triangle_count,
            "material_count": material_count,
            "joint_count": joint_count,
            "idle_animation_channels": animation_channels,
            "gltf_version": gltf["asset"]["version"],
            "glb_binary_bytes": len(glb_binary),
            "obj_export": True,
            "absolute_machine_paths": False,
        },
        "unity_contract": {
            "format": "glTF 2.0 / GLB",
            "status": "PENDING_EVIDENCE",
            "note": "Structural readiness only; no native Unity import is claimed by this report.",
        },
    }
    if write_report:
        report_path = asset_dir / "structural-validation.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _refresh_checksums(asset_dir)
    return report


def _refresh_checksums(asset_dir: Path) -> None:
    lines = []
    for path in sorted(
        item
        for item in asset_dir.rglob("*")
        if item.is_file()
        and item.name != "SHA256SUMS.txt"
        and ".godot" not in item.parts
        and not item.name.endswith(".import")
        and item.suffix.lower() != ".uid"
        and not (
            item.parent.name == "godot_preview"
            and item.name.startswith("eclipse_warden_")
            and item.suffix.lower() == ".png"
        )
    ):
        lines.append(f"{_sha256(path)}  {path.relative_to(asset_dir).as_posix()}")
    (asset_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_tamper_test(asset_dir: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="neoeng-asset-tamper-") as temporary:
        copy_dir = Path(temporary) / asset_dir.name
        shutil.copytree(asset_dir, copy_dir)
        target = copy_dir / "textures" / "armor_basecolor.png"
        payload = bytearray(target.read_bytes())
        payload[-1] ^= 0x01
        target.write_bytes(payload)
        try:
            validate(copy_dir, write_report=False)
        except ValidationError as error:
            return {"status": "PASS", "detected": True, "error": str(error)}
        return {"status": "FAIL", "detected": False, "error": "tampered texture was accepted"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-dir", required=True, type=Path)
    parser.add_argument("--tamper-test", action="store_true")
    arguments = parser.parse_args()
    try:
        report = validate(arguments.asset_dir.resolve())
        if arguments.tamper_test:
            report["tamper_test"] = _run_tamper_test(arguments.asset_dir.resolve())
            if report["tamper_test"]["status"] != "PASS":
                raise ValidationError("tamper test did not detect the mutation")
            (arguments.asset_dir.resolve() / "structural-validation.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            _refresh_checksums(arguments.asset_dir.resolve())
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (OSError, KeyError, IndexError, ValueError, ValidationError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
