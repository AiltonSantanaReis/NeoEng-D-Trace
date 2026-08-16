from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from src.exporters import animation_batch, tileset_exporter
from src.exporters.animation_batch import (
    _resample_closed_polygon,
    detect_frame,
    discover_frames,
    export_animation_frames,
    stabilize_animation_detections,
)
from src.exporters.tileset_exporter import (
    collision_from_tile,
    prepare_tileset,
    save_tileset,
    slice_tilesheet,
)


def test_tileset_slicing_snaps_edge_collision_and_writes_manifest(
    tmp_path: Path,
) -> None:
    sheet = Image.new("RGBA", (9, 4), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sheet)
    draw.rectangle((0, 0, 3, 3), fill=(255, 0, 0, 255))
    draw.rectangle((6, 1, 7, 2), fill=(0, 255, 0, 255))

    prepared = prepare_tileset(sheet, tile_size=(4, 4), spacing=1, tolerance=0)
    assert len(slice_tilesheet(sheet, tile_size=(4, 4), spacing=1)) == 2
    assert prepared["tiles"][0]["collision"] == [[0, 0], [4, 0], [4, 4], [0, 4]]
    assert prepared["tiles"][1]["collision"] == [[1, 1], [3, 1], [3, 3], [1, 3]]

    result = save_tileset(prepared, tmp_path)
    assert Path(result["manifest_path"]).is_file()
    assert (tmp_path / "tile_0000.png").is_file()
    assert result["manifest"]["tiles"][0]["texture"] == "tile_0000.png"


def test_tileset_rejects_incomplete_or_invalid_grid() -> None:
    image = Image.new("RGBA", (3, 3))
    assert slice_tilesheet(image, tile_size=(4, 4)) == []
    with pytest.raises(ValueError, match="positive integer"):
        slice_tilesheet(image, tile_size=(0, 1))


def test_animation_batch_detects_and_exports_all_natural_order_frames(
    tmp_path: Path,
) -> None:
    source = tmp_path / "frames"
    output = tmp_path / "out"
    source.mkdir()
    for name, offset in (("frame_10.png", 0), ("frame_2.png", 1)):
        image = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
        ImageDraw.Draw(image).rectangle(
            (2 + offset, 2, 16 + offset, 16), fill=(255, 255, 255, 255)
        )
        image.save(source / name)

    result = export_animation_frames(source, output, mode="basic", min_area=10)

    manifest = result["manifest"]
    assert manifest["frame_count"] == 2
    assert [frame["source"] for frame in manifest["frames"]] == [
        "frame_2.png",
        "frame_10.png",
    ]
    assert all(len(frame["polygon"]) >= 3 for frame in manifest["frames"])
    assert (output / "frame_0000.png").is_file()
    assert (output / "frame_0001.png").is_file()
    assert Path(result["manifest_path"]).is_file()


def test_animation_coherence_resamples_and_aligns_different_vertex_counts() -> None:
    records = [
        {
            "polygon": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]],
        },
        {
            "polygon": [
                [0.0, 0.0],
                [5.0, 0.0],
                [10.0, 0.0],
                [10.0, 5.0],
                [10.0, 10.0],
                [0.0, 10.0],
            ],
        },
    ]

    vertex_count = stabilize_animation_detections(records)

    assert vertex_count == 6
    assert [len(record["polygon"]) for record in records] == [6, 6]
    assert records[0]["polygon"][0] == records[1]["polygon"][0]


def test_animation_discovery_and_detection_fail_closed(
    tmp_path: Path, monkeypatch
) -> None:
    with pytest.raises(ValueError, match="existing directory"):
        discover_frames(tmp_path / "missing")
    frames = tmp_path / "frames"
    frames.mkdir()
    with pytest.raises(ValueError, match="matched"):
        discover_frames(frames)

    class Result(list):
        feedback = {"status": "ok"}

    monkeypatch.setattr(
        animation_batch, "detect_polygons", lambda *args, **kwargs: Result()
    )
    with pytest.raises(ValueError, match="no polygon"):
        detect_frame(Image.new("RGBA", (4, 4)))

    monkeypatch.setattr(
        animation_batch,
        "detect_polygons",
        lambda *args, **kwargs: Result([{"area": 1, "polygon": [[0, 0], [1, 1]]}]),
    )
    with pytest.raises(ValueError, match="invalid polygon"):
        detect_frame(Image.new("RGBA", (4, 4)))


def test_animation_resampling_validates_geometry_and_zero_edges() -> None:
    with pytest.raises(ValueError, match="three points"):
        _resample_closed_polygon([[0, 0], [1, 1]], 4)
    with pytest.raises(ValueError, match="at least three"):
        _resample_closed_polygon([[0, 0], [1, 1], [2, 2]], 2)
    with pytest.raises(ValueError, match="perimeter"):
        _resample_closed_polygon([[0, 0], [0, 0], [0, 0]], 3)
    result = _resample_closed_polygon([[0, 0], [0, 0], [2, 0], [0, 2]], 3)
    assert len(result) == 3


def test_animation_coherence_rejects_invalid_record_sets() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        stabilize_animation_detections([])
    records = [{"polygon": [[0, 0], [1, 0], [0, 1]]}]
    with pytest.raises(ValueError, match="between 3 and 256"):
        stabilize_animation_detections(records, vertex_count=257)
    with pytest.raises(ValueError, match="between 3 and 256"):
        stabilize_animation_detections(records, vertex_count=2)


def test_animation_coherence_aligns_opposite_winding() -> None:
    records = [
        {"polygon": [[0.0, 0.0], [4.0, 0.0], [4.0, 4.0], [0.0, 4.0]]},
        {"polygon": [[0.0, 4.0], [4.0, 4.0], [4.0, 0.0], [0.0, 0.0]]},
    ]
    stabilize_animation_detections(records)
    assert records[0]["polygon"] == records[1]["polygon"]


def test_tileset_rejects_non_image_and_invalid_spacing_contracts() -> None:
    with pytest.raises(ValueError, match="Pillow"):
        slice_tilesheet("not-an-image", tile_size=(1, 1))
    image = Image.new("RGBA", (2, 2))
    with pytest.raises(ValueError, match="positive integer"):
        slice_tilesheet(image, tile_size=(True, 1))
    with pytest.raises(ValueError, match="non-negative integer"):
        slice_tilesheet(image, tile_size=(1, 1), spacing=-1)
    with pytest.raises(ValueError, match="non-negative integer"):
        slice_tilesheet(image, tile_size=(1, 1), margin=-1)


def test_tileset_empty_alpha_and_no_snap_contracts() -> None:
    empty = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    assert collision_from_tile(empty) is None
    tile = Image.new("RGBA", (5, 5), (0, 0, 0, 0))
    ImageDraw.Draw(tile).rectangle((1, 1, 3, 3), fill=(255, 255, 255, 255))
    assert collision_from_tile(tile, snap_to_edges=False) == [
        [1, 1],
        [4, 1],
        [4, 4],
        [1, 4],
    ]


def test_tileset_prepare_and_save_fail_closed_for_missing_tile_image(
    tmp_path: Path,
) -> None:
    assert prepare_tileset(Image.new("RGBA", (2, 2)), tile_size=(3, 3))["tiles"] == []
    with pytest.raises(ValueError, match="must contain images"):
        save_tileset({"tiles": [{"id": "tile_0000", "image": None}]}, tmp_path)


def test_animation_resampling_walks_past_zero_length_first_edge() -> None:
    polygon = [[0.0, 0.0], [0.1, 0.0], [10.0, 0.0], [0.0, 10.0]]
    assert len(_resample_closed_polygon(polygon, 4)) == 4


def test_animation_manifest_replace_failure_cleans_temporary_file(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "frames"
    output = tmp_path / "out"
    source.mkdir()
    image = Image.new("RGBA", (12, 12), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((2, 2, 9, 9), fill=(255, 255, 255, 255))
    image.save(source / "frame_1.png")

    def fail_replace(*args, **kwargs):
        raise OSError("controlled manifest replace failure")

    monkeypatch.setattr(animation_batch.os, "replace", fail_replace)
    with pytest.raises(OSError, match="controlled manifest replace failure"):
        export_animation_frames(source, output, mode="basic", min_area=2)
    assert not list(output.glob("tmp_animation_*.json"))


def test_tileset_collision_rejects_degenerate_alpha_bounds(monkeypatch) -> None:
    monkeypatch.setattr(tileset_exporter, "_alpha_bounds", lambda tile: (1, 1, 1, 2))
    assert (
        collision_from_tile(
            Image.new("RGBA", (4, 4), (255, 255, 255, 255)),
            snap_to_edges=False,
        )
        is None
    )


def test_tileset_manifest_replace_failure_cleans_temporary_file(
    tmp_path: Path, monkeypatch
) -> None:
    prepared = prepare_tileset(
        Image.new("RGBA", (2, 2), (255, 255, 255, 255)), tile_size=(2, 2)
    )

    def fail_replace(*args, **kwargs):
        raise OSError("controlled tileset replace failure")

    monkeypatch.setattr(tileset_exporter.os, "replace", fail_replace)
    with pytest.raises(OSError, match="controlled tileset replace failure"):
        save_tileset(prepared, tmp_path)
    assert not list(tmp_path.glob("tmp_tileset_*.json"))


def test_animation_resampling_continues_after_long_first_edge() -> None:
    polygon = [[0.0, 0.0], [100.0, 0.0], [100.0, 1.0], [0.0, 1.0]]
    assert len(_resample_closed_polygon(polygon, 3)) == 3


def test_tileset_manifest_write_failure_cleans_temporary_file(
    tmp_path: Path, monkeypatch
) -> None:
    prepared = prepare_tileset(
        Image.new("RGBA", (2, 2), (255, 255, 255, 255)), tile_size=(2, 2)
    )

    def fail_dump(*args, **kwargs):
        raise OSError("controlled manifest write failure")

    monkeypatch.setattr(tileset_exporter.json, "dump", fail_dump)
    with pytest.raises(OSError, match="controlled manifest write failure"):
        save_tileset(prepared, tmp_path)
    assert not list(tmp_path.glob("tmp_tileset_*.json"))
