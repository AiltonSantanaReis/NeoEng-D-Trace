from __future__ import annotations

import hashlib
import json
import logging
import struct
import zlib
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from pydantic import ValidationError

from src.collision.broadphase import AABB, UniformGridBroadPhase
from src.core import image_input
from src.core.app_identity import LOGGER_NAME
from src.core.bezier_geometry import canonicalize_beziers, sample_beziers
from src.core.config import ConfigManager
from src.core.image_input import ImageInputError
from src.core.logger import setup_logging
from src.core.operational_limits import MAX_BEZIER_SEGMENTS, MAX_POLYGON_POINTS
from src.exporters.atlas_exporter import pack_sprites_to_atlas
from src.models.scene import Scene, SceneObject
from src.persistence.project_schema import (
    BezierSegmentRecord,
    LayerRecord,
    PointRecord,
    ProjectDocumentV1,
    ProjectMetadataRecord,
    SceneObjectRecord,
)
from src.tools.smoothing import chaikin_smooth


def _project_document(**overrides):
    values = {
        "metadata": ProjectMetadataRecord(
            generator="NeoEng-D-Trace",
            app_version="0.2.0",
        ),
        "layers": [
            LayerRecord(
                id="layer_default",
                name="Default",
                visible=True,
                locked=False,
            )
        ],
        "objects": [],
        "groups": [],
    }
    values.update(overrides)
    return ProjectDocumentV1(**values)


def test_config_rejects_unknown_fields_instead_of_silently_accepting_them(
    tmp_path: Path,
) -> None:
    path = tmp_path / "config.json"
    path.write_text('{"zoom": 3.0, "unexpected": true}', encoding="utf-8")

    manager = ConfigManager(str(path))

    assert manager.get("zoom") == 1.0
    assert not path.exists()
    assert path.with_name("config.json.corrupted").is_file()


def test_config_rejects_oversized_collections_with_controlled_recovery(
    tmp_path: Path,
) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps({"recent_files": ["item.ndtproj"] * 10_001}),
        encoding="utf-8",
    )

    manager = ConfigManager(str(path))

    assert manager.get("recent_files") == []
    assert not path.exists()
    assert path.with_name("config.json.corrupted").is_file()


def test_project_rejects_polygon_above_runtime_complexity_ceiling() -> None:
    with pytest.raises(ValidationError, match="at most 2000 items"):
        SceneObjectRecord(
            id="object-1",
            layer_id="layer_default",
            polygon=[PointRecord(x=index, y=index % 2) for index in range(2_001)],
        )


def test_uniform_grid_rejects_invalid_cell_size_and_pathological_span() -> None:
    with pytest.raises(ValueError, match="grid_cell_size"):
        UniformGridBroadPhase(0)

    broadphase = UniformGridBroadPhase(64)
    with pytest.raises(ValueError, match="grid cell limit"):
        broadphase.insert("huge", AABB(0, 0, 64 * 100_001, 1))
    assert broadphase.objects == {}
    assert broadphase.grid == {}


def test_gltf_rejects_uint16_index_overflow_without_partial_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from src.exporters import gltf_exporter

    scene = Scene()
    scene.objects["object-1"] = SceneObject(
        "object-1",
        [(0, 0), (1, 0), (0, 1)],
        "layer_default",
    )
    oversized = [(float(index), 0.0) for index in range(65_537)]
    monkeypatch.setattr(
        gltf_exporter,
        "triangulate_to_convex",
        lambda _polygon: [oversized],
    )
    target = tmp_path / "overflow.glb"

    assert gltf_exporter.export_scene_to_gltf(scene, str(target)) is False
    assert not target.exists()


def test_file_logging_rotates_and_redacts_personal_paths(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    import src.core.logger as logger_module

    root = logging.getLogger()
    app_logger = logging.getLogger(LOGGER_NAME)
    root_before = list(root.handlers)
    app_before = list(app_logger.handlers)
    target = tmp_path / "application.log"
    personal_path = Path.home() / "private folder" / "asset.png"
    try:
        monkeypatch.setattr(logger_module, "MAX_LOG_FILE_BYTES", 300)
        setup_logging("INFO", True, str(target))
        module_logger = logging.getLogger("stage12.rotation")
        for index in range(12):
            app_logger.error("Cannot open %s iteration=%d", personal_path, index)
            module_logger.error("Cannot open %s iteration=%d", personal_path, index)
        for handler in app_logger.handlers:
            handler.flush()

        owned_file_handlers = [
            handler
            for handler in app_logger.handlers
            if getattr(handler, "_neoeng_d_trace_owned", False)
            and hasattr(handler, "baseFilename")
        ]
        assert len(owned_file_handlers) == 1
        assert type(owned_file_handlers[0]).__name__ == "RotatingFileHandler"
        assert target.with_name("application.log.1").is_file()
        content = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(tmp_path.glob("application.log*"))
        )
        assert str(personal_path) not in content
        assert "private folder" not in content
        assert "<PATH>" in content
        assert "Logging error" not in capsys.readouterr().err
    finally:
        for handler in list(root.handlers):
            if handler not in root_before:
                root.removeHandler(handler)
                handler.close()
        for handler in list(app_logger.handlers):
            if handler not in app_before:
                app_logger.removeHandler(handler)
                handler.close()


def test_project_accepts_polygon_at_ceiling_and_rejects_complexity_sum(
    monkeypatch,
) -> None:
    from src.persistence import project_schema

    monkeypatch.setattr(project_schema, "is_valid_polygon", lambda _points: True)
    at_limit = SceneObjectRecord(
        id="at-limit",
        layer_id="layer_default",
        polygon=[PointRecord(x=index, y=index % 2) for index in range(2_000)],
    )
    assert _project_document(objects=[at_limit]).objects == [at_limit]

    first = SceneObjectRecord(
        id="first",
        layer_id="layer_default",
        polygon=[PointRecord(x=0, y=0)] * 3,
    )
    second = SceneObjectRecord(
        id="second",
        layer_id="layer_default",
        polygon=[PointRecord(x=1, y=1)] * 3,
    )
    monkeypatch.setattr(project_schema, "MAX_PROJECT_POLYGON_COMPLEXITY", 17)
    with pytest.raises(ValidationError, match="complexity limit"):
        _project_document(objects=[first, second])


def test_uniform_grid_failed_update_preserves_previous_registration() -> None:
    broadphase = UniformGridBroadPhase(64)
    original = AABB(0, 0, 10, 10)
    broadphase.insert("object", original)

    with pytest.raises(ValueError, match="grid cell limit"):
        broadphase.update("object", AABB(0, 0, 64 * 100_001, 1))

    assert broadphase.objects == {"object": original}
    assert broadphase.query(original) == {"object"}


@pytest.mark.parametrize(
    "coordinates",
    [
        (0, 0, float("inf"), 1),
        (0, 0, float("nan"), 1),
        (2, 0, 1, 1),
        (True, 0, 1, 1),
    ],
)
def test_aabb_rejects_non_finite_inverted_and_boolean_coordinates(
    coordinates,
) -> None:
    with pytest.raises(ValueError, match="AABB"):
        AABB(*coordinates)


def test_image_inspection_accepts_real_png_and_validates_decoded_array(
    tmp_path: Path,
) -> None:
    path = tmp_path / "valid.png"
    Image.new("RGBA", (8, 6), (1, 2, 3, 4)).save(path)

    info = image_input.inspect_image_file(path)
    assert (
        image_input.hash_validated_image_file(info)
        == hashlib.sha256(path.read_bytes()).hexdigest()
    )
    with pytest.raises(ImageInputError, match="changed during hashing"):
        image_input.hash_validated_image_file(
            replace(info, file_size=info.file_size + 1)
        )
    decoded = np.zeros((6, 8, 4), dtype=np.uint8)
    image_input.validate_decoded_image(decoded, info)

    assert info.width == 8
    assert info.height == 6
    assert info.format == "PNG"


def test_image_inspection_rejects_pixel_limit_before_full_decode(
    tmp_path: Path,
    monkeypatch,
) -> None:
    path = tmp_path / "too-many-pixels.png"
    Image.new("RGB", (3, 3), (0, 0, 0)).save(path)
    monkeypatch.setattr(image_input, "MAX_IMAGE_PIXELS", 8)

    with pytest.raises(ImageInputError, match="pixel limit"):
        image_input.inspect_image_file(path)


def test_image_file_size_is_checked_before_pillow_open(
    tmp_path: Path,
    monkeypatch,
) -> None:
    path = tmp_path / "oversized.png"
    path.write_bytes(b"12345")
    monkeypatch.setattr(image_input, "MAX_IMAGE_FILE_BYTES", 4)
    monkeypatch.setattr(
        image_input.Image,
        "open",
        lambda *_args, **_kwargs: pytest.fail("decoder must not be called"),
    )

    with pytest.raises(ImageInputError, match="exceeds 4 bytes"):
        image_input.inspect_image_file(path)


def test_image_content_must_match_extension(tmp_path: Path) -> None:
    path = tmp_path / "disguised.png"
    Image.new("RGB", (2, 2), (0, 0, 0)).save(path, format="JPEG")

    with pytest.raises(ImageInputError, match="does not match extension"):
        image_input.inspect_image_file(path)


def test_headless_image_route_enforces_preflight(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    import src.launcher as launcher

    path = tmp_path / "input.png"
    Image.new("RGB", (2, 2), (0, 0, 0)).save(path)
    monkeypatch.setattr(
        launcher,
        "inspect_image_file",
        lambda _path: (_ for _ in ()).throw(ImageInputError("blocked by limit")),
    )
    arguments = launcher.build_parser().parse_args(["--image", str(path)])

    assert launcher.run_headless(arguments) == launcher.EXIT_FAILURE
    assert "blocked by limit" in capsys.readouterr().err


@pytest.mark.parametrize(
    "raw",
    [
        b"\xff",
        b'{"zoom":NaN}',
        b'{"zoom":1.0,"zoom":2.0}',
        (b"[" * 1_100) + (b"]" * 1_100),
    ],
)
def test_malformed_config_corpus_recovers_without_exception(
    tmp_path: Path,
    raw: bytes,
) -> None:
    path = tmp_path / "config.json"
    path.write_bytes(raw)

    manager = ConfigManager(str(path))

    assert manager.get("zoom") == 1.0
    assert not path.exists()
    assert path.with_name("config.json.corrupted").read_bytes() == raw


def test_validation_log_rotates_and_caps_large_event(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import src.core.validation_events as validation_events

    output = tmp_path / "validation.jsonl"
    monkeypatch.setattr(validation_events, "MAX_VALIDATION_LOG_FILE_BYTES", 700)
    monkeypatch.setattr(validation_events, "MAX_VALIDATION_EVENT_BYTES", 350)
    validation_events.start_validation_session(output)
    try:
        for index in range(12):
            validation_events.record_validation_event(
                f"event.{index}",
                "SUCCESS",
                payload="x" * 1_000,
            )
    finally:
        validation_events.stop_validation_session(exit_code=0)

    files = [output, output.with_name("validation.jsonl.1")]
    assert all(path.is_file() for path in files)
    rows = []
    for path in files:
        rows.extend(
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
        )
    assert any(row["details"].get("truncated") is True for row in rows)
    assert (
        json.loads(output.read_text(encoding="utf-8").splitlines()[-1])["event"]
        == "session.summary"
    )


def test_project_load_rejects_invalid_geometry_without_mutating_scene(
    tmp_path: Path,
) -> None:
    from src.persistence.errors import ProjectValidationError

    payload = {
        "format_id": "neoeng-d-trace-project",
        "schema_version": 1,
        "metadata": {"generator": "NeoEng-D-Trace", "app_version": "0.2.0"},
        "image": None,
        "layers": [
            {
                "id": "layer_default",
                "name": "Default",
                "visible": True,
                "locked": False,
            }
        ],
        "objects": [
            {
                "id": "invalid",
                "layer_id": "layer_default",
                "polygon": [
                    {"x": 0, "y": 0},
                    {"x": 4, "y": 4},
                    {"x": 0, "y": 4},
                    {"x": 4, "y": 0},
                ],
                "collision": None,
                "beziers": None,
            }
        ],
        "groups": [],
    }
    path = tmp_path / "invalid-geometry.ndtproj"
    path.write_text(json.dumps(payload), encoding="utf-8")
    scene = Scene()
    scene.add_object("preserved", [(0, 0), (4, 0), (0, 4)])

    with pytest.raises(ProjectValidationError, match="invalid polygon geometry"):
        scene.load_project(str(path))

    assert list(scene.objects) == ["preserved"]


def test_project_schema_rejects_invalid_collision_geometry() -> None:
    item = SceneObjectRecord(
        id="object-1",
        layer_id="layer_default",
        polygon=[
            PointRecord(x=0, y=0),
            PointRecord(x=4, y=0),
            PointRecord(x=0, y=4),
        ],
        collision=[
            PointRecord(x=0, y=0),
            PointRecord(x=1, y=1),
            PointRecord(x=2, y=2),
        ],
    )

    with pytest.raises(ValidationError, match="invalid collision geometry"):
        _project_document(objects=[item])


def test_bezier_sampling_accepts_exact_ceiling_and_rejects_next_point() -> None:
    segment = ((0, 0), (1, 0), (1, 1), (0, 1))

    assert len(sample_beziers([segment], steps_per_segment=1_999)) == 2_000
    with pytest.raises(ValueError, match="point limit"):
        sample_beziers([segment], steps_per_segment=2_000)
    with pytest.raises(ValueError, match="segment limit"):
        canonicalize_beziers([segment] * (MAX_BEZIER_SEGMENTS + 1))


def test_chaikin_growth_is_bounded_before_expansion() -> None:
    accepted = [(float(index), 0.0) for index in range(125)]
    rejected = [(float(index), 0.0) for index in range(126)]

    assert len(chaikin_smooth(accepted, iterations=4)) == MAX_POLYGON_POINTS
    with pytest.raises(ValueError, match="point limit"):
        chaikin_smooth(rejected, iterations=4)
    with pytest.raises(ValueError, match="between 0 and"):
        chaikin_smooth(accepted, iterations=9)


def test_detection_rejects_upscale_and_oversized_array_before_opencv(
    monkeypatch,
) -> None:
    from src.tools import auto_detect

    image = np.zeros((4, 4), dtype=np.uint8)
    with pytest.raises(ValueError, match="downscale"):
        auto_detect.detect_polygons(image, downscale=2.0)

    monkeypatch.setattr(auto_detect, "MAX_IMAGE_PIXELS", 15)
    monkeypatch.setattr(
        auto_detect,
        "_detect_polygons_basic",
        lambda *_args, **_kwargs: pytest.fail("OpenCV route must not run"),
    )
    with pytest.raises(ValueError, match="pixel limit"):
        auto_detect.detect_polygons(image)


def test_enhanced_detection_rejects_raw_contour_above_polygon_limit(
    monkeypatch,
) -> None:
    from src.tools import auto_detect

    contour = np.zeros((MAX_POLYGON_POINTS + 1, 1, 2), dtype=np.int32)
    monkeypatch.setattr(
        auto_detect.cv2,
        "findContours",
        lambda *_args, **_kwargs: ([contour], None),
    )

    with pytest.raises(ValueError, match="point limit"):
        auto_detect.detect_polygons(
            np.zeros((8, 8), dtype=np.uint8),
            mode="enhanced",
            min_area=-1,
        )


def test_atlas_rejects_oversized_dimensions_before_canvas_allocation(
    monkeypatch,
) -> None:
    from src.exporters import atlas_exporter

    item = Image.new("RGBA", (1, 1))
    monkeypatch.setattr(
        atlas_exporter.Image,
        "new",
        lambda *_args, **_kwargs: pytest.fail("atlas canvas must not be allocated"),
    )

    with pytest.raises(ValueError, match="dimensions"):
        pack_sprites_to_atlas([(item, {"name": "item"})], max_size=(8_193, 1))


def test_atlas_page_count_has_a_controlled_ceiling() -> None:
    items = [
        (Image.new("RGBA", (4, 4)), {"name": f"item-{index}"}) for index in range(17)
    ]

    with pytest.raises(ValueError, match="page count"):
        pack_sprites_to_atlas(items, max_size=(4, 4), padding=0)


def test_project_schema_rejects_bezier_segments_above_object_limit() -> None:
    point = PointRecord(x=0, y=0)
    segment = BezierSegmentRecord(p0=point, p1=point, p2=point, p3=point)

    with pytest.raises(ValidationError, match="at most 1999 items"):
        SceneObjectRecord(
            id="oversized-bezier",
            layer_id="layer_default",
            polygon=[],
            beziers=[segment] * 2_000,
        )


def test_real_png_metadata_above_pixel_limit_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "oversized-metadata.png"
    Image.new("RGB", (1, 1)).save(path)
    raw = bytearray(path.read_bytes())
    raw[16:24] = struct.pack(">II", 4_097, 4_097)
    raw[29:33] = struct.pack(">I", zlib.crc32(raw[12:29]) & 0xFFFFFFFF)
    path.write_bytes(raw)

    with pytest.raises(ImageInputError, match="pixel limit"):
        image_input.inspect_image_file(path)


def test_truncated_png_and_multiframe_tiff_are_rejected(tmp_path: Path) -> None:
    truncated = tmp_path / "truncated.png"
    Image.new("RGB", (16, 16)).save(truncated)
    raw = truncated.read_bytes()
    truncated.write_bytes(raw[: len(raw) // 2])

    with pytest.raises(ImageInputError, match="invalid or unsafe image"):
        image_input.inspect_image_file(truncated)

    multiframe = tmp_path / "multiframe.tiff"
    frames = [Image.new("L", (2, 2), value) for value in (0, 255)]
    frames[0].save(multiframe, save_all=True, append_images=frames[1:])
    with pytest.raises(ImageInputError, match="multi-frame"):
        image_input.inspect_image_file(multiframe)


@pytest.mark.parametrize(
    ("array", "message"),
    [
        (np.zeros((2,), dtype=np.uint8), "2D grayscale"),
        (np.zeros((2, 2, 2), dtype=np.uint8), "2D grayscale"),
        (np.zeros((0, 2), dtype=np.uint8), "positive"),
        (np.zeros((2, 2), dtype=object), "numeric"),
    ],
)
def test_detection_array_shape_and_dtype_contract(array, message) -> None:
    from src.tools import auto_detect

    with pytest.raises(ValueError, match=message):
        auto_detect.detect_polygons(array)


def test_detection_array_dimension_byte_and_parameter_limits(monkeypatch) -> None:
    from src.tools import auto_detect

    image = np.zeros((4, 4), dtype=np.uint8)
    monkeypatch.setattr(auto_detect, "MAX_IMAGE_DIMENSION", 3)
    with pytest.raises(ValueError, match="dimensions"):
        auto_detect.detect_polygons(image)

    monkeypatch.setattr(auto_detect, "MAX_IMAGE_DIMENSION", 8_192)
    monkeypatch.setattr(auto_detect, "MAX_DECODED_IMAGE_BYTES", 15)
    with pytest.raises(ValueError, match="decoded byte"):
        auto_detect.detect_polygons(image)

    for value in (True, "0.5", float("nan"), 0.0):
        with pytest.raises(ValueError, match="downscale"):
            auto_detect._bounded_downscale(value)
    for value in (True, 1.5):
        with pytest.raises(ValueError, match="chaikin_iterations"):
            auto_detect._bounded_chaikin_iterations(value)


def test_detection_count_and_aggregate_point_limits(monkeypatch) -> None:
    from src.tools import auto_detect

    contour = np.zeros((2, 1, 2), dtype=np.int32)
    monkeypatch.setattr(auto_detect, "MAX_PROJECT_OBJECTS", 0)
    with pytest.raises(ValueError, match="contour count"):
        auto_detect._validate_contours([contour])
    with pytest.raises(ValueError, match="polygon count"):
        auto_detect._validate_detection_result([{"polygon": []}])

    monkeypatch.setattr(auto_detect, "MAX_PROJECT_OBJECTS", 10)
    monkeypatch.setattr(auto_detect, "MAX_PROJECT_POINTS", 1)
    with pytest.raises(ValueError, match="contour points"):
        auto_detect._validate_contours([contour])
    with pytest.raises(ValueError, match="polygon points"):
        auto_detect._validate_detection_result(
            [{"polygon": [(0, 0)]}, {"polygon": [(1, 1)]}]
        )


@pytest.mark.parametrize(
    ("max_size", "padding", "message"),
    [
        (1, 0, "max_size"),
        ((1,), 0, "max_size"),
        ((True, 1), 0, "max_size"),
        ((1.5, 1), 0, "max_size"),
        ((0, 1), 0, "positive"),
        ((4_096, 4_097), 0, "pixel limit"),
        ((8, 8), True, "padding"),
        ((8, 8), -1, "padding"),
        ((8, 8), 4, "usable"),
    ],
)
def test_atlas_argument_validation_matrix(max_size, padding, message) -> None:
    item = Image.new("RGBA", (1, 1))

    with pytest.raises(ValueError, match=message):
        pack_sprites_to_atlas(
            [(item, {"name": "item"})],
            max_size=max_size,
            padding=padding,
        )


def test_atlas_item_and_aggregate_limits(monkeypatch) -> None:
    from src.exporters import atlas_exporter

    item = Image.new("RGBA", (1, 1))
    monkeypatch.setattr(atlas_exporter, "MAX_ATLAS_ITEMS", 0)
    with pytest.raises(ValueError, match="item count"):
        pack_sprites_to_atlas([(item, {"name": "item"})])

    monkeypatch.setattr(atlas_exporter, "MAX_ATLAS_ITEMS", 10)
    with pytest.raises(ValueError, match="Pillow"):
        pack_sprites_to_atlas([("not-an-image", {"name": "item"})])

    empty = Image.Image()
    with pytest.raises(ValueError, match="positive"):
        pack_sprites_to_atlas([(empty, {"name": "empty"})])

    monkeypatch.setattr(atlas_exporter, "MAX_ATLAS_TOTAL_INPUT_PIXELS", 0)
    with pytest.raises(ValueError, match="aggregate pixel"):
        pack_sprites_to_atlas([(item, {"name": "item"})])


def test_decoded_image_contract_matrix(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "source.png"
    pil_image = Image.new("RGBA", (2, 2))
    pil_image.save(path)
    info = image_input.inspect_image_file(path)

    image_input.validate_decoded_image(pil_image, info)
    with pytest.raises(ImageInputError, match="two or three"):
        image_input.validate_decoded_image(np.zeros((2,), dtype=np.uint8), info)
    with pytest.raises(ImageInputError, match="unsupported"):
        image_input.validate_decoded_image(object(), info)
    with pytest.raises(ImageInputError, match="differ"):
        image_input.validate_decoded_image(np.zeros((1, 2), dtype=np.uint8), info)

    monkeypatch.setattr(image_input, "MAX_DECODED_IMAGE_BYTES", 3)
    with pytest.raises(ImageInputError, match="decoded image"):
        image_input.validate_decoded_image(pil_image, info)

    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ImageInputError, match="changed after validation"):
        image_input.validate_decoded_image(pil_image, info)
    with pytest.raises(ImageInputError, match="changed during hashing"):
        image_input.hash_validated_image_file(info)
