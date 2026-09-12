"""Controlled, deterministic raster-to-polygon detection for scene authoring.

E09-A deliberately owns only the import and detection boundary.  The result
keeps the source hash and every detection parameter so later editing and
persistence stages cannot silently detach a polygon from the image that
produced it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
from PIL import Image

from src.core.image_input import (
    ImageInputError,
    ImageInputInfo,
    hash_validated_image_file,
    inspect_image_file,
    validate_decoded_image,
)
from src.core.operational_limits import MAX_POLYGON_POINTS
from src.core.polygon_validation import is_valid_polygon, signed_polygon_area2

VectorizationChannel = Literal["alpha", "luminance"]
VECTORISATION_ALGORITHM = "opencv-contour-tree-r1"


class VectorizationError(ValueError):
    """Actionable failure in the controlled image-to-contour contract."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class VectorizationRequest:
    """Bounded parameters for one deterministic detection attempt."""

    channel: VectorizationChannel = "alpha"
    threshold: int = 1
    approximation_epsilon: float = 1.0
    minimum_area: float = 16.0
    maximum_vertices: int = MAX_POLYGON_POINTS

    def __post_init__(self) -> None:
        if self.channel not in ("alpha", "luminance"):
            raise VectorizationError(
                "invalid_channel", "channel must be alpha or luminance"
            )
        if isinstance(self.threshold, bool) or not 0 <= self.threshold <= 255:
            raise VectorizationError(
                "invalid_threshold", "threshold must be between 0 and 255"
            )
        if (
            not np.isfinite(self.approximation_epsilon)
            or self.approximation_epsilon < 0
        ):
            raise VectorizationError(
                "invalid_epsilon",
                "approximation_epsilon must be finite and non-negative",
            )
        if not np.isfinite(self.minimum_area) or self.minimum_area <= 0:
            raise VectorizationError(
                "invalid_area", "minimum_area must be finite and positive"
            )
        if (
            isinstance(self.maximum_vertices, bool)
            or not 3 <= self.maximum_vertices <= MAX_POLYGON_POINTS
        ):
            raise VectorizationError(
                "invalid_vertex_limit",
                f"maximum_vertices must be between 3 and {MAX_POLYGON_POINTS}",
            )


@dataclass(frozen=True)
class VectorizationResult:
    """Hash-bound polygon plus enough metadata for later provenance checks."""

    source_path: str
    source_sha256: str
    image_format: str
    image_width: int
    image_height: int
    channel: VectorizationChannel
    threshold: int
    approximation_epsilon: float
    minimum_area: float
    polygon: tuple[tuple[float, float], ...]
    contour_area: float
    algorithm: str = VECTORISATION_ALGORITHM

    @property
    def area2(self) -> float:
        return signed_polygon_area2(self.polygon)

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["polygon"] = [list(point) for point in self.polygon]
        return payload


def _read_validated_image(path: str | Path) -> tuple[np.ndarray, ImageInputInfo, str]:
    try:
        info = inspect_image_file(path)
    except ImageInputError as exc:
        raise VectorizationError("invalid_image", str(exc)) from exc

    try:
        with Image.open(info.path) as image:
            image.load()
            decoded = np.asarray(image.convert("RGBA"), dtype=np.uint8)
        validate_decoded_image(decoded, info)
        source_sha256 = hash_validated_image_file(info)
    except ImageInputError as exc:
        raise VectorizationError("invalid_image", str(exc)) from exc
    except (OSError, ValueError) as exc:
        raise VectorizationError(
            "invalid_image", f"cannot decode image: {exc}"
        ) from exc

    return decoded, info, source_sha256


def _mask_for_channel(image: np.ndarray, request: VectorizationRequest) -> np.ndarray:
    if request.channel == "alpha":
        channel = image[:, :, 3]
        if not np.any(channel > request.threshold):
            raise VectorizationError(
                "empty_mask", "alpha threshold produced no foreground"
            )
    else:
        rgb = image[:, :, :3]
        channel = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        if not np.any(channel > request.threshold):
            raise VectorizationError(
                "empty_mask", "luminance threshold produced no foreground"
            )
    return np.where(channel > request.threshold, 255, 0).astype(np.uint8)


def _detect_polygon(
    mask: np.ndarray, request: VectorizationRequest
) -> tuple[list[tuple[float, float]], float]:
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if not contours or hierarchy is None:
        raise VectorizationError("empty_mask", "detection produced no contour")

    hierarchy_row = hierarchy[0]
    external = [
        index
        for index, contour in enumerate(contours)
        if int(hierarchy_row[index][3]) == -1
        and cv2.contourArea(contour) >= request.minimum_area
    ]
    if not external:
        raise VectorizationError("empty_contour", "no contour meets minimum_area")
    if len(external) != 1:
        raise VectorizationError(
            "unsupported_islands",
            "multiple foreground components are not supported in E09-A; "
            "correct the image or select one component",
        )

    root = external[0]
    child = int(hierarchy_row[root][2])
    if child != -1:
        raise VectorizationError(
            "unsupported_holes",
            "contours with holes are not supported in E09-A; "
            "close the hole or use a solid source",
        )

    contour = contours[root]
    if request.approximation_epsilon > 0:
        contour = cv2.approxPolyDP(contour, request.approximation_epsilon, True)
    points: list[tuple[float, float]] = [
        (float(point[0]), float(point[1]))
        for point in np.asarray(contour).reshape(-1, 2)
    ]
    if len(points) > request.maximum_vertices:
        raise VectorizationError(
            "vertex_limit",
            f"detected contour has {len(points)} vertices; "
            f"limit is {request.maximum_vertices}",
        )
    if len(points) < 3:
        raise VectorizationError(
            "invalid_geometry", "detected contour has fewer than three vertices"
        )
    if signed_polygon_area2(points) < 0:
        points.reverse()
    first = min(range(len(points)), key=lambda index: points[index])
    points = points[first:] + points[:first]
    if not is_valid_polygon(points):
        raise VectorizationError(
            "invalid_geometry", "detected contour is not a valid simple polygon"
        )
    return points, float(cv2.contourArea(contours[root]))


def vectorize_image_file(
    path: str | Path, request: VectorizationRequest | None = None
) -> VectorizationResult:
    """Decode one real image and return a provenance-bound polygon."""

    active_request = request or VectorizationRequest()
    image, info, source_sha256 = _read_validated_image(path)
    mask = _mask_for_channel(image, active_request)
    polygon, contour_area = _detect_polygon(mask, active_request)
    return VectorizationResult(
        source_path=str(info.path.resolve()),
        source_sha256=source_sha256,
        image_format=str(info.format),
        image_width=int(info.width),
        image_height=int(info.height),
        channel=active_request.channel,
        threshold=active_request.threshold,
        approximation_epsilon=float(active_request.approximation_epsilon),
        minimum_area=float(active_request.minimum_area),
        polygon=tuple(polygon),
        contour_area=contour_area,
    )


__all__ = [
    "VECTORISATION_ALGORITHM",
    "VectorizationError",
    "VectorizationRequest",
    "VectorizationResult",
    "vectorize_image_file",
]
