from __future__ import annotations

import json

import pytest

from tools.create_reference_3d_asset import generate
from tools.validate_reference_3d_asset import _run_tamper_test, validate


def test_reference_asset_generation_and_contract(tmp_path):
    output = tmp_path / "eclipse-warden"
    manifest = generate(output)
    report = validate(output)

    assert manifest["asset"]["name"] == "Eclipse Warden"
    assert report["status"] == "PASS"
    assert report["checks"]["mesh_count"] == 23
    assert report["checks"]["joint_count"] == 18
    assert report["checks"]["gltf_version"] == "2.0"
    assert report["unity_contract"]["status"] == "PENDING_EVIDENCE"
    assert json.loads((output / "structural-validation.json").read_text(encoding="utf-8"))["status"] == "PASS"
    assert _run_tamper_test(output)["status"] == "PASS"


def test_reference_asset_refuses_overwrite(tmp_path):
    output = tmp_path / "eclipse-warden"
    generate(output)
    with pytest.raises(FileExistsError):
        generate(output)
