from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

import src.core.view_processor as view_processor
from src.core.config import ConfigManager
from src.core.view_processor import ViewProcessor, has_cuda
from src.tools.edge_utils import (
    canny_edges,
    enhanced_edge_detection,
    log_response,
    multi_scale_edges,
    normalize_array,
)
from src.tools.smoothing import catmull_rom_to_beziers, chaikin_smooth
from src.utils.selection_tools import (
    expand_contract_polygon,
    invert_selection,
    mask_to_polygon,
    polygon_to_mask,
)


def test_chaikin_preserves_open_endpoints_and_grows_deterministically():
    points = [(0, 0), (8, 0), (8, 8)]

    once = chaikin_smooth(points, iterations=1)
    twice = chaikin_smooth(points, iterations=2)

    assert once == [
        (0.0, 0.0),
        (2.0, 0.0),
        (6.0, 0.0),
        (8.0, 2.0),
        (8.0, 6.0),
        (8.0, 8.0),
    ]
    assert twice[0] == (0.0, 0.0)
    assert twice[-1] == (8.0, 8.0)
    assert len(twice) == 12


def test_chaikin_handles_noop_and_malformed_input_without_mutating_source():
    points = [(1, 2)]
    assert chaikin_smooth(points, iterations=3) == points
    assert chaikin_smooth([(0, 0), (2, 2)], iterations=0) == [(0, 0), (2, 2)]
    malformed = [(0, 0), ("invalid", 1)]
    assert chaikin_smooth(malformed) is malformed


def test_catmull_rom_open_and_closed_segments_have_expected_endpoints():
    points = [(0, 0), (6, 0), (6, 6)]

    opened = catmull_rom_to_beziers(points)
    closed = catmull_rom_to_beziers(points, closed=True)

    assert len(opened) == 2
    assert opened[0][0] == (0.0, 0.0)
    assert opened[-1][-1] == (6.0, 6.0)
    assert len(closed) == 3
    assert closed[-1][0] == (6.0, 6.0)
    assert closed[-1][-1] == (0.0, 0.0)
    assert catmull_rom_to_beziers([(1, 1)]) == []
    assert catmull_rom_to_beziers([(0, 0), (object(), 1)]) == []


def test_normalize_array_covers_range_constant_and_malformed_inputs():
    result = normalize_array(np.array([[2.0, 4.0], [6.0, 8.0]]))
    assert result.dtype == np.uint8
    assert result.tolist() == [[0, 85], [170, 255]]
    assert not normalize_array(np.full((2, 3), 7.0)).any()
    malformed = np.array([object()], dtype=object)
    fallback = normalize_array(malformed)
    assert fallback.dtype == np.uint8
    assert fallback.shape == malformed.shape


def test_edge_detectors_accept_gray_and_rgb_and_preserve_shape():
    gray = np.zeros((32, 32), dtype=np.uint8)
    gray[8:24, 8:24] = 255
    rgb = np.dstack([gray, gray, gray])

    canny = canny_edges(rgb, 20, 80)
    response = log_response(rgb, sigma=1.0)
    combined = enhanced_edge_detection(rgb, 20, 80)

    assert canny.shape == gray.shape
    assert canny.dtype == np.uint8
    assert response.shape == gray.shape
    assert response.dtype == np.float32
    assert combined.shape == gray.shape
    assert combined.dtype == np.uint8
    assert np.count_nonzero(combined) > 0


@pytest.mark.parametrize("sigma", [0, -1.0])
def test_log_response_rejects_invalid_sigma(sigma):
    with pytest.raises(ValueError, match="sigma"):
        log_response(np.zeros((4, 4), dtype=np.uint8), sigma)


def test_log_response_and_multiscale_reject_invalid_contracts():
    with pytest.raises(ValueError, match="numpy"):
        log_response("not-an-array", 1.0)
    with pytest.raises(ValueError, match="numpy"):
        multi_scale_edges("not-an-array")
    with pytest.raises(ValueError, match="non-empty"):
        multi_scale_edges(np.zeros((4, 4), dtype=np.uint8), scales=[])
    with pytest.raises(ValueError, match="positive finite"):
        multi_scale_edges(np.zeros((4, 4), dtype=np.uint8), scales=[1.0, 0.0])
    with pytest.raises(ValueError, match="match scales"):
        multi_scale_edges(
            np.zeros((4, 4), dtype=np.uint8), scales=[1.0], weights=[0.5, 0.5]
        )
    with pytest.raises(ValueError, match="non-zero finite"):
        multi_scale_edges(
            np.zeros((4, 4), dtype=np.uint8), scales=[1.0, 2.0], weights=[1, -1]
        )


def test_multiscale_default_and_custom_weights_are_finite():
    gray = np.arange(64, dtype=np.uint8).reshape(8, 8)
    default = multi_scale_edges(gray)
    custom = multi_scale_edges(gray, scales=[0.5, 1.0], weights=[3.0, 1.0])

    assert default.shape == gray.shape
    assert custom.shape == gray.shape
    assert default.dtype == np.float32
    assert custom.dtype == np.float32
    assert np.isfinite(default).all()
    assert np.isfinite(custom).all()


def test_has_cuda_handles_available_missing_and_failed_runtime(monkeypatch):
    monkeypatch.setattr(
        view_processor,
        "cv2",
        SimpleNamespace(cuda=SimpleNamespace(getCudaEnabledDeviceCount=lambda: 1)),
    )
    assert has_cuda() is True

    monkeypatch.setattr(view_processor, "cv2", SimpleNamespace())
    assert has_cuda() is False

    def fail():
        raise RuntimeError("driver unavailable")

    monkeypatch.setattr(
        view_processor,
        "cv2",
        SimpleNamespace(cuda=SimpleNamespace(getCudaEnabledDeviceCount=fail)),
    )
    assert has_cuda() is False


@pytest.mark.parametrize(
    "array",
    [
        np.arange(12, dtype=np.uint8).reshape(3, 4),
        np.zeros((3, 4, 3), dtype=np.uint8),
        np.zeros((3, 4, 4), dtype=np.uint8),
    ],
)
def test_to_qimage_supports_gray_bgr_bgra_and_noncontiguous_arrays(array):
    noncontiguous = array[:, ::-1]
    assert not noncontiguous.flags["C_CONTIGUOUS"]

    image = ViewProcessor.to_qimage(noncontiguous)

    assert image is not None
    assert image.width() == 4
    assert image.height() == 3


@pytest.mark.parametrize(
    "pil_image",
    [
        Image.new("L", (3, 2), 12),
        Image.new("RGB", (3, 2), (10, 20, 30)),
        Image.new("RGBA", (3, 2), (10, 20, 30, 40)),
        Image.new("CMYK", (3, 2), (10, 20, 30, 40)),
    ],
)
def test_to_qimage_supports_pillow_modes(pil_image):
    image = ViewProcessor.to_qimage(pil_image)
    assert image is not None
    assert (image.width(), image.height()) == pil_image.size


def test_to_qimage_rejects_none_objects_and_invalid_array_dimensions():
    assert ViewProcessor.to_qimage(None) is None
    assert ViewProcessor.to_qimage(object()) is None
    assert ViewProcessor.to_qimage(np.array([1, 2, 3], dtype=np.uint8)) is None
    assert ViewProcessor.to_qimage(np.zeros((2, 2, 2), dtype=np.uint8)) is None


@pytest.mark.parametrize("mode", [1, 2, 3, 99])
def test_cpu_xray_modes_return_three_channel_uint8(mode):
    gray = np.zeros((16, 16), dtype=np.uint8)
    gray[4:12, 4:12] = 255

    result = ViewProcessor._cpu_generate_xray(gray, mode)

    assert result.shape == (16, 16, 3)
    assert result.dtype == np.uint8


def test_generate_xray_uses_cpu_and_falls_back_when_gpu_fails(monkeypatch):
    source = np.zeros((8, 8, 3), dtype=np.uint8)
    source[2:6, 2:6] = 255
    monkeypatch.setattr(view_processor, "HAS_GPU", False)
    cpu_image = ViewProcessor.generate_xray(source, mode=2)
    assert cpu_image is not None
    assert (cpu_image.width(), cpu_image.height()) == (8, 8)

    monkeypatch.setattr(view_processor, "HAS_GPU", True)
    monkeypatch.setattr(
        ViewProcessor,
        "_gpu_generate_xray",
        staticmethod(lambda *_: (_ for _ in ()).throw(RuntimeError("gpu failed"))),
    )
    fallback = ViewProcessor.generate_xray(source, mode=1)
    assert fallback is not None
    assert ViewProcessor.generate_xray(None) is None


def test_polygon_mask_roundtrip_reuse_and_empty_contract():
    polygon = [(3, 3), (15, 3), (15, 15), (3, 15)]
    reusable = np.full((20, 20), 17, dtype=np.uint8)

    mask = polygon_to_mask(polygon, (20, 20), reusable)
    roundtrip = mask_to_polygon(mask, approx_dp=0)

    assert mask is reusable
    assert mask[0, 0] == 0
    assert mask[8, 8] == 255
    assert len(roundtrip) >= 4
    assert mask_to_polygon(np.zeros((5, 5), dtype=np.uint8)) == []
    assert not polygon_to_mask([], (4, 6)).any()
    assert polygon_to_mask(polygon, (20, 20), np.zeros((2, 2))).shape == (20, 20)


def test_expand_contract_and_invert_selection_have_real_geometric_effect():
    polygon = [(8, 8), (20, 8), (20, 20), (8, 20)]
    original = polygon_to_mask(polygon, (32, 32))
    expanded = polygon_to_mask(expand_contract_polygon(polygon, (32, 32), 2), (32, 32))
    contracted = polygon_to_mask(
        expand_contract_polygon(polygon, (32, 32), -2), (32, 32)
    )
    unchanged = expand_contract_polygon(polygon, (32, 32), 0)
    inverted = polygon_to_mask(invert_selection(polygon, (32, 32)), (32, 32))

    assert np.count_nonzero(expanded) > np.count_nonzero(original)
    assert np.count_nonzero(contracted) < np.count_nonzero(original)
    assert unchanged
    assert inverted[0, 0] == 255
    assert inverted.shape == original.shape


def test_config_roundtrip_defaults_unknown_key_and_atomic_replace(tmp_path):
    path = tmp_path / "settings" / "config.json"
    manager = ConfigManager(str(path))
    assert manager.get("zoom") == 1.0
    assert manager.get("missing", "fallback") == "fallback"

    manager.set("zoom", 2.5)
    manager.set("recent_files", ["one.ndtproj"])
    manager.set("unknown", "ignored")
    manager.save()

    loaded = ConfigManager(str(path))
    assert loaded.get("zoom") == 2.5
    assert loaded.get("recent_files") == ["one.ndtproj"]
    assert not hasattr(loaded.config, "unknown")

    loaded.set("zoom", 3.0)
    loaded.save()
    assert ConfigManager(str(path)).get("zoom") == 3.0
    ConfigManager(None).save()


@pytest.mark.parametrize("content", ["{broken", '{"zoom": 0}'])
def test_config_corruption_is_backed_up_and_defaults_are_retained(tmp_path, content):
    path = tmp_path / "config.json"
    path.write_text(content, encoding="utf-8")

    manager = ConfigManager(str(path))

    assert manager.get("zoom") == 1.0
    assert not path.exists()
    backup_content = path.with_name("config.json.corrupted").read_text(encoding="utf-8")
    assert backup_content == content


def test_config_failed_replace_preserves_destination_and_cleans_temp(
    tmp_path, monkeypatch
):
    path = tmp_path / "config.json"
    path.write_text('{"zoom": 1.0}', encoding="utf-8")
    manager = ConfigManager(str(path))
    manager.set("zoom", 4.0)

    def fail_replace(*_):
        raise OSError("blocked")

    monkeypatch.setattr("src.core.config.os.replace", fail_replace)

    manager.save()

    assert path.read_text(encoding="utf-8") == '{"zoom": 1.0}'
    assert list(tmp_path.glob("*.tmp")) == []
