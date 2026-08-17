from __future__ import annotations

import hashlib
from typing import Any, Dict, List

import numpy as np
import pytest

from src.core.commands import CommandManager
from src.core.operational_limits import MAX_POLYGON_POINTS
from src.models.scene import Scene
from src.tools.auto_detect import detect_and_create_objects, detect_polygons
from tools.benchmark_auto_detection import _boundary_f1, _polygons_mask, build_cases


def _run(case: Any, mode: str) -> tuple[List[Dict[str, Any]], np.ndarray, np.ndarray]:
    kwargs: Dict[str, Any] = {"min_area": 25.0}
    truth = case.ground_truth
    if mode == "grabcut":
        kwargs.update(roi=case.roi, detect_holes=True, grabcut_iterations=5)
        if case.grabcut_ground_truth is not None:
            truth = case.grabcut_ground_truth
    elif mode == "perfect":
        kwargs.update(downscale=1.0, separate_touching=False)
    elif mode == "enhanced":
        kwargs.update(downscale=1.0, detect_holes=True, morph_kernel_size=3)
    result = list(detect_polygons(case.image, mode=mode, **kwargs))
    return result, _polygons_mask(result, truth.shape), truth


@pytest.mark.parametrize("mode", ["perfect", "enhanced", "grabcut"])
def test_real_adversarial_corpus_keeps_quality_and_boundaries(mode: str) -> None:
    for case in build_cases():
        polygons, predicted, truth = _run(case, mode)
        intersection = np.count_nonzero((predicted > 0) & (truth > 0))
        union = np.count_nonzero((predicted > 0) | (truth > 0))
        iou = intersection / max(1, union)
        boundary = _boundary_f1(predicted, truth)
        assert iou >= 0.94, f"{mode}/{case.name} IoU={iou:.3f}"
        assert boundary >= 0.95, f"{mode}/{case.name} boundary_f1={boundary:.3f}"
        assert polygons
        assert all(
            len(item.get("polygon", [])) <= MAX_POLYGON_POINTS for item in polygons
        )


@pytest.mark.parametrize("mode", ["perfect", "enhanced", "grabcut"])
def test_real_hole_contract_is_one_object_with_one_hole(mode: str) -> None:
    case = next(case for case in build_cases() if case.name == "ring_hole")
    polygons, _, _ = _run(case, mode)

    outer = [item for item in polygons if not item.get("is_hole", False)]
    holes = [item for item in polygons if item.get("is_hole", False)]
    assert len(outer) == 1
    assert len(outer[0].get("holes", [])) == 1
    if mode == "enhanced":
        assert len(holes) == 1
    else:
        assert not holes


def test_basic_detection_preserves_internal_hole() -> None:
    case = next(case for case in build_cases() if case.name == "ring_hole")
    polygons = list(
        detect_polygons(case.image, mode="basic", min_area=25.0, detect_holes=True)
    )

    assert len(polygons) == 1
    assert len(polygons[0].get("holes", [])) == 1


def test_high_detail_contour_is_bounded_and_deterministic() -> None:
    case = next(case for case in build_cases() if case.name == "high_detail_boundary")
    first, first_mask, _ = _run(case, "enhanced")
    second, second_mask, _ = _run(case, "enhanced")

    assert max(len(item["polygon"]) for item in first) <= MAX_POLYGON_POINTS
    assert (
        hashlib.sha256(first_mask.tobytes()).hexdigest()
        == hashlib.sha256(second_mask.tobytes()).hexdigest()
    )
    assert first == second


@pytest.mark.parametrize("mode", ["perfect", "enhanced"])
def test_numeric_and_rgba_inputs_use_the_same_real_pipeline(mode: str) -> None:
    case = next(case for case in build_cases() if case.name == "rgba_alpha")
    result = detect_polygons(case.image.astype(np.float32), mode=mode, min_area=25.0)
    assert result
    assert all(len(item["polygon"]) >= 3 for item in result)


def test_enhanced_morphology_parameter_is_validated() -> None:
    case = next(case for case in build_cases() if case.name == "clean_rectangle")
    with pytest.raises(ValueError, match="morph_kernel_size"):
        detect_polygons(case.image, mode="enhanced", morph_kernel_size=2)


def test_legacy_hole_record_is_not_created_as_a_scene_object() -> None:
    case = next(case for case in build_cases() if case.name == "ring_hole")
    scene = Scene()
    scene.cmd = CommandManager()

    object_ids = detect_and_create_objects(
        scene,
        case.image,
        mode="enhanced",
        min_area=25.0,
        detect_holes=True,
        morph_kernel_size=3,
    )

    assert len(object_ids) == 1
    assert len(scene.objects) == 1
