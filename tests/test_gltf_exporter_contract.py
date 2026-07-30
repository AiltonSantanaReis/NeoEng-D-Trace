from __future__ import annotations

import ast
import hashlib
import importlib
import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest

from src.core.app_identity import GLTF_GENERATOR
from src.models.scene import Group, Layer, Scene, SceneObject

ROOT = Path(__file__).resolve().parents[1]
MODULE_NAME = "src.exporters.gltf_exporter"
MODULE_PATH = ROOT / "src" / "exporters" / "gltf_exporter.py"

EXPECTED_CONTRACT = {
    "binary_sha256": "8acbb1d1117affb68c0e059a386a76c89d4267a3ecdedc742ce23b4659aafeb8",
    "binary_size": 84,
    "no_metadata_ok": True,
    "no_metadata_sha256": "ee2bd28df5f9eaee030e24aa9aa82a7f80b9c4615c14f3326fc324c6592834fb",
    "no_metadata_size": 1198,
    "object_ok": True,
    "object_sha256": "01239871697a5e6ee9238fee4e6b5dca586d288b64397dd3c48668f9d1c90b24",
    "object_size": 1110,
    "scene_ok": True,
    "scene_sha256": "e650d8d0919c50591c03a89b6bad91945df93e8f3583b481b92ab43da0cac670",
    "scene_size": 1595,
}
EXPECTED_DOCUMENT = {
    "accessors": [
        {
            "bufferView": 0,
            "byteOffset": 0,
            "componentType": 5126,
            "count": 3,
            "max": [4.0, 3.0, 0.0],
            "min": [0.0, 0.0, 0.0],
            "type": "VEC3",
        },
        {
            "bufferView": 1,
            "byteOffset": 0,
            "componentType": 5123,
            "count": 3,
            "max": [2],
            "min": [0],
            "type": "SCALAR",
        },
        {
            "bufferView": 0,
            "byteOffset": 36,
            "componentType": 5126,
            "count": 3,
            "max": [12.0, 14.0, 0.0],
            "min": [10.0, 10.0, 0.0],
            "type": "VEC3",
        },
        {
            "bufferView": 1,
            "byteOffset": 6,
            "componentType": 5123,
            "count": 3,
            "max": [2],
            "min": [0],
            "type": "SCALAR",
        },
    ],
    "asset": {"generator": "NeoEng-D-Trace GLTF Exporter", "version": "2.0"},
    "bufferViews": [
        {
            "buffer": 0,
            "byteLength": 72,
            "byteOffset": 0,
            "byteStride": 12,
            "target": 34962,
        },
        {"buffer": 0, "byteLength": 12, "byteOffset": 72, "target": 34963},
    ],
    "buffers": [{"byteLength": 84}],
    "meshes": [
        {
            "extras": {
                "groups": ["group_main"],
                "layer": "layer_fx",
                "object_id": "obj_a",
            },
            "primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "mode": 4}],
        },
        {
            "extras": {"groups": [], "layer": "layer_default", "object_id": "obj_b"},
            "primitives": [{"attributes": {"POSITION": 2}, "indices": 3, "mode": 4}],
        },
    ],
    "nodes": [
        {"extras": {"object_id": "obj_a"}, "mesh": 0},
        {"extras": {"object_id": "obj_b"}, "mesh": 1},
    ],
    "scene": 0,
    "scenes": [
        {
            "extras": {
                "groups": [{"id": "group_main", "members": ["obj_a"], "name": "Grupo"}],
                "layers": [
                    {"id": "layer_default", "name": "Default", "visible": True},
                    {"id": "layer_fx", "name": "Efeitos", "visible": False},
                ],
            },
            "nodes": [0, 1],
        }
    ],
}
EXPECTED_BINARY = (
    np.array(
        [
            0.0,
            0.0,
            0.0,
            4.0,
            0.0,
            0.0,
            0.0,
            3.0,
            0.0,
            10.0,
            10.0,
            0.0,
            12.0,
            10.0,
            0.0,
            10.0,
            14.0,
            0.0,
        ],
        dtype=np.float32,
    ).tobytes()
    + np.array([0, 1, 2, 0, 1, 2], dtype=np.uint16).tobytes()
)


class _FakeRecord:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _FakeGLTF2:
    fail_save = False

    def __init__(self):
        self.asset = None
        self.scenes = []
        self.nodes = []
        self.meshes = []
        self.buffers = []
        self.bufferViews = []
        self.accessors = []
        self.scene = None
        self._blob = b""

    def set_binary_blob(self, data):
        self._blob = bytes(data)

    def save(self, path):
        if type(self).fail_save:
            raise OSError("simulated save failure")
        Path(path).write_bytes(_serialize_fake(self))


class _FakeScene(_FakeRecord):
    pass


class _FakeNode(_FakeRecord):
    pass


class _FakeMesh(_FakeRecord):
    pass


class _FakePrimitive(_FakeRecord):
    pass


class _FakeBuffer(_FakeRecord):
    pass


class _FakeBufferView(_FakeRecord):
    pass


class _FakeAccessor(_FakeRecord):
    pass


class _FakeAsset(_FakeRecord):
    pass


def _normalize(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalize(value[key]) for key in sorted(value, key=str)}
    if hasattr(value, "__dict__"):
        return {
            key: _normalize(val)
            for key, val in sorted(value.__dict__.items())
            if not key.startswith("_")
        }
    raise TypeError(type(value).__name__)


def _serialize_fake(gltf):
    payload = {
        "document": _normalize(gltf),
        "binary_sha256": hashlib.sha256(gltf._blob).hexdigest(),
        "binary_hex": gltf._blob.hex(),
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


_BACKEND_SYMBOLS = (
    "GLTF2",
    "Scene",
    "Node",
    "Mesh",
    "Primitive",
    "Buffer",
    "BufferView",
    "Accessor",
    "Asset",
    "_HAS_PYGLTF",
)


def _install_fake_backend(module, *, fail_save=False):
    _FakeGLTF2.fail_save = fail_save
    classes = {
        "GLTF2": _FakeGLTF2,
        "Scene": _FakeScene,
        "Node": _FakeNode,
        "Mesh": _FakeMesh,
        "Primitive": _FakePrimitive,
        "Buffer": _FakeBuffer,
        "BufferView": _FakeBufferView,
        "Accessor": _FakeAccessor,
        "Asset": _FakeAsset,
    }
    for name, value in classes.items():
        setattr(module, name, value)
    module._HAS_PYGLTF = True


@contextmanager
def _temporary_fake_backend(module, *, fail_save=False):
    """Install the deterministic fake backend without leaking it to later tests."""
    missing = object()
    original = {name: getattr(module, name, missing) for name in _BACKEND_SYMBOLS}
    try:
        _install_fake_backend(module, fail_save=fail_save)
        yield
    finally:
        _FakeGLTF2.fail_save = False
        for name, value in original.items():
            if value is missing:
                try:
                    delattr(module, name)
                except AttributeError:
                    pass
            else:
                setattr(module, name, value)


def _fixture_scene() -> Scene:
    scene = Scene()
    scene.layers.append(
        Layer(id="layer_fx", name="Efeitos", visible=False, locked=True)
    )
    scene.add_object("obj_a", [(0, 0), (4, 0), (0, 3)], layer_id="layer_fx")
    scene.add_object("obj_b", [(10, 10), (12, 10), (10, 14)], layer_id="layer_default")
    group = Group(id="group_main", name="Grupo", visible=True, locked=False)
    group.members = ["obj_a"]
    scene.groups.append(group)
    return scene


def _fake_contract(module, tmp_path: Path) -> dict:
    with _temporary_fake_backend(module):
        scene = _fixture_scene()
        results = {}
        operations = (
            ("scene", lambda p: module.export_scene_to_gltf(scene, str(p), True)),
            (
                "no_metadata",
                lambda p: module.export_scene_to_gltf(scene, str(p), False),
            ),
            (
                "object",
                lambda p: module.export_object_to_gltf("obj_a", scene, str(p), True),
            ),
        )
        for key, operation in operations:
            path = tmp_path / f"{key}.glb"
            results[f"{key}_ok"] = operation(path)
            raw = path.read_bytes()
            results[f"{key}_sha256"] = hashlib.sha256(raw).hexdigest()
            results[f"{key}_size"] = len(raw)
        payload = json.loads((tmp_path / "scene.glb").read_text(encoding="utf-8"))
        results["binary_sha256"] = payload["binary_sha256"]
        results["binary_size"] = len(bytes.fromhex(payload["binary_hex"]))
        results["document"] = payload["document"]
        return results


def test_gltf_exporter_uses_single_src_implementation() -> None:
    module = importlib.import_module(MODULE_NAME)
    assert Path(module.__file__).resolve() == MODULE_PATH.resolve()
    assert module.export_scene_to_gltf.__module__ == MODULE_NAME
    assert module.export_object_to_gltf.__module__ == MODULE_NAME
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "generator=GLTF_GENERATOR" in source
    assert "neoeng_d_trace" not in source


def test_gltf_fake_backend_exact_contract_is_frozen(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    actual = _fake_contract(module, tmp_path)
    assert {
        key: value for key, value in actual.items() if key != "document"
    } == EXPECTED_CONTRACT
    assert actual["document"] == EXPECTED_DOCUMENT
    assert (
        bytes.fromhex(
            json.loads((tmp_path / "scene.glb").read_text(encoding="utf-8"))[
                "binary_hex"
            ]
        )
        == EXPECTED_BINARY
    )


def test_gltf_atomic_replacement_and_failure_cleanup_are_preserved(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    scene = _fixture_scene()
    target = tmp_path / "scene.glb"
    target.write_bytes(b"old")

    with _temporary_fake_backend(module):
        assert module.export_scene_to_gltf(scene, str(target)) is True
        assert target.read_bytes() != b"old"
        assert [path.name for path in tmp_path.iterdir()] == ["scene.glb"]

    before = target.read_bytes()
    with _temporary_fake_backend(module, fail_save=True):
        assert module.export_scene_to_gltf(scene, str(target)) is False
        assert target.read_bytes() == before
        assert [path.name for path in tmp_path.iterdir()] == ["scene.glb"]


def test_gltf_failure_contracts_are_preserved(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    original_available = module._HAS_PYGLTF
    try:
        module._HAS_PYGLTF = False
        assert (
            module.export_scene_to_gltf(
                _fixture_scene(), str(tmp_path / "disabled.glb")
            )
            is False
        )
        assert not (tmp_path / "disabled.glb").exists()
    finally:
        module._HAS_PYGLTF = original_available

    with _temporary_fake_backend(module):
        scene = _fixture_scene()
        assert (
            module.export_object_to_gltf(
                "missing", scene, str(tmp_path / "missing.glb")
            )
            is False
        )
        scene.objects["bad"] = SceneObject("bad", [(0, 0), (1, 1)], "layer_default")
        assert (
            module.export_object_to_gltf("bad", scene, str(tmp_path / "bad.glb"))
            is False
        )
        empty = Scene()
        assert module.export_scene_to_gltf(empty, str(tmp_path / "empty.glb")) is False


def test_gltf_fake_backend_is_restored_after_each_test() -> None:
    module = importlib.import_module(MODULE_NAME)
    original = {name: getattr(module, name, None) for name in _BACKEND_SYMBOLS}

    with _temporary_fake_backend(module, fail_save=True):
        assert module.GLTF2 is _FakeGLTF2
        assert module._HAS_PYGLTF is True
        assert _FakeGLTF2.fail_save is True

    assert _FakeGLTF2.fail_save is False
    for name, value in original.items():
        assert getattr(module, name, None) is value


def test_gltf_glb_persistence_prefers_binary_save_and_rejects_false(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    calls: list[tuple[str, str]] = []

    class _Probe:
        def save_binary(self, path):
            calls.append(("save_binary", str(path)))
            Path(path).write_bytes(b"glb")
            return True

        def save(self, path):
            calls.append(("save", str(path)))
            raise AssertionError(
                "generic save() must not be used when save_binary() exists"
            )

    target = tmp_path / "probe.glb"
    module._save_glb(_Probe(), str(target))
    assert calls == [("save_binary", str(target))]
    assert target.read_bytes() == b"glb"

    class _FalseProbe:
        def save_binary(self, path):
            return False

    with pytest.raises(OSError, match="failed save operation"):
        module._save_glb(_FalseProbe(), str(tmp_path / "false.glb"))


def test_gltf_required_pygltflib_dependency_is_available() -> None:
    module = importlib.import_module(MODULE_NAME)
    assert module._HAS_PYGLTF, (
        "pygltflib is declared as a runtime dependency and is required for "
        "validated GLTF/GLB export"
    )


@pytest.mark.skipif(
    not importlib.import_module(MODULE_NAME)._HAS_PYGLTF,
    reason="pygltflib unavailable; the required-dependency test reports this as a failure",
)
def test_gltf_real_glb_structure_and_binary_contract(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    path = tmp_path / "scene.glb"
    assert module.export_scene_to_gltf(_fixture_scene(), str(path), True) is True
    assert path.is_file() and path.stat().st_size > 20

    loaded = module.GLTF2().load(str(path))
    assert loaded.asset.version == "2.0"
    assert loaded.asset.generator == GLTF_GENERATOR
    assert len(loaded.scenes) == 1
    assert len(loaded.nodes) == 2
    assert len(loaded.meshes) == 2
    assert len(loaded.accessors) == 4
    assert len(loaded.bufferViews) == 2
    assert len(loaded.buffers) == 1
    assert loaded.scene == 0

    assert [
        (a.bufferView, a.byteOffset, a.count, a.type) for a in loaded.accessors
    ] == [
        (0, 0, 3, "VEC3"),
        (1, 0, 3, "SCALAR"),
        (0, 36, 3, "VEC3"),
        (1, 6, 3, "SCALAR"),
    ]
    assert loaded.bufferViews[0].byteOffset in (None, 0)
    assert loaded.bufferViews[0].byteLength == 72
    assert loaded.bufferViews[0].byteStride == 12
    assert loaded.bufferViews[1].byteOffset == 72
    assert loaded.bufferViews[1].byteLength == 12
    assert loaded.buffers[0].byteLength == 84

    blob = loaded.binary_blob()
    assert blob == EXPECTED_BINARY
    assert hashlib.sha256(blob).hexdigest() == EXPECTED_CONTRACT["binary_sha256"]
    assert loaded.meshes[0].extras == {
        "object_id": "obj_a",
        "layer": "layer_fx",
        "groups": ["group_main"],
    }
    # pygltflib 1.16.5 removes empty iterables while serializing JSON.
    # The in-memory exporter assigns ``groups: []``, but after a real GLB
    # save/load round trip the key is absent. Absence is the persisted
    # representation of an object with no group memberships.
    assert loaded.meshes[1].extras == {
        "object_id": "obj_b",
        "layer": "layer_default",
    }
    assert "groups" not in loaded.meshes[1].extras
    assert loaded.meshes[1].extras.get("groups", []) == []
    assert loaded.nodes[0].extras == {"object_id": "obj_a"}
    assert loaded.nodes[1].extras == {"object_id": "obj_b"}


@pytest.mark.skipif(
    not importlib.import_module(MODULE_NAME)._HAS_PYGLTF,
    reason="pygltflib unavailable; the required-dependency test reports this as a failure",
)
def test_gltf_real_single_object_export_contract(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    path = tmp_path / "object.glb"
    assert (
        module.export_object_to_gltf("obj_a", _fixture_scene(), str(path), True) is True
    )
    loaded = module.GLTF2().load(str(path))
    assert len(loaded.nodes) == 1
    assert len(loaded.meshes) == 1
    assert loaded.nodes[0].extras == {"object_id": "obj_a"}
    assert loaded.meshes[0].extras == {
        "object_id": "obj_a",
        "layer": "layer_fx",
        "groups": ["group_main"],
    }
    expected = EXPECTED_BINARY[:36] + EXPECTED_BINARY[72:78]
    blob = loaded.binary_blob()
    padded_length = (len(expected) + 3) & ~3
    assert loaded.buffers[0].byteLength == padded_length
    assert len(blob) == padded_length
    assert blob[: len(expected)] == expected
    assert bytes(blob[len(expected) :]) == b"\x00" * (padded_length - len(expected))
    assert loaded.bufferViews[0].byteLength == 36
    assert loaded.bufferViews[1].byteOffset == 36
    assert loaded.bufferViews[1].byteLength == 6
