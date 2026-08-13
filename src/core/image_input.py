"""Bounded inspection and decoded-image validation for imported images."""

from __future__ import annotations

import hashlib
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from src.core.operational_limits import (
    MAX_DECODED_IMAGE_BYTES,
    MAX_IMAGE_DIMENSION,
    MAX_IMAGE_FILE_BYTES,
    MAX_IMAGE_PIXELS,
)

_FORMATS_BY_SUFFIX = {
    ".bmp": frozenset({"BMP"}),
    ".jpeg": frozenset({"JPEG"}),
    ".jpg": frozenset({"JPEG"}),
    ".png": frozenset({"PNG"}),
    ".tif": frozenset({"TIFF"}),
    ".tiff": frozenset({"TIFF"}),
}


class ImageInputError(ValueError):
    """Raised when an image violates the bounded input contract."""


@dataclass(frozen=True)
class ImageInputInfo:
    path: Path
    file_size: int
    modified_ns: int
    width: int
    height: int
    format: str


def _validate_dimensions(width: int, height: int) -> None:
    if width <= 0 or height <= 0:
        raise ImageInputError("image dimensions must be positive")
    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        raise ImageInputError(
            f"image dimensions exceed {MAX_IMAGE_DIMENSION} pixels per axis"
        )
    pixels = width * height
    if pixels > MAX_IMAGE_PIXELS:
        raise ImageInputError(f"image exceeds the {MAX_IMAGE_PIXELS} pixel limit")


def inspect_image_file(path: str | Path) -> ImageInputInfo:
    """Inspect one image before full decode and reject unsafe metadata."""

    target = Path(path).expanduser()
    if not target.exists():
        raise ImageInputError(f"image file not found: {target}")
    if not target.is_file():
        raise ImageInputError(f"image path is not a file: {target}")
    suffix = target.suffix.lower()
    expected_formats = _FORMATS_BY_SUFFIX.get(suffix)
    if expected_formats is None:
        raise ImageInputError(f"unsupported image extension: {suffix or '<none>'}")

    try:
        before = target.stat()
    except OSError as exc:
        raise ImageInputError(f"cannot stat image file: {exc}") from exc
    if before.st_size <= 0:
        raise ImageInputError("image file is empty")
    if before.st_size > MAX_IMAGE_FILE_BYTES:
        raise ImageInputError(f"image file exceeds {MAX_IMAGE_FILE_BYTES} bytes")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(target) as image:
                image_format = str(image.format or "").upper()
                if image_format not in expected_formats:
                    raise ImageInputError(
                        f"image content {image_format or '<unknown>'} does not match "
                        f"extension {suffix}"
                    )
                width, height = image.size
                _validate_dimensions(int(width), int(height))
                if int(getattr(image, "n_frames", 1)) != 1:
                    raise ImageInputError("multi-frame images are not supported")
                image.verify()
    except ImageInputError:
        raise
    except (Image.DecompressionBombError, OSError, SyntaxError, ValueError) as exc:
        raise ImageInputError(f"invalid or unsafe image: {exc}") from exc

    try:
        after = target.stat()
    except OSError as exc:
        raise ImageInputError(f"cannot restat image file: {exc}") from exc
    if (after.st_size, after.st_mtime_ns) != (before.st_size, before.st_mtime_ns):
        raise ImageInputError("image file changed during validation")

    return ImageInputInfo(
        path=target,
        file_size=before.st_size,
        modified_ns=before.st_mtime_ns,
        width=int(width),
        height=int(height),
        format=image_format,
    )


def validate_decoded_image(image: Any, expected: ImageInputInfo) -> None:
    """Validate dimensions and memory footprint after the real decoder runs."""

    try:
        current = expected.path.stat()
    except OSError as exc:
        raise ImageInputError(f"cannot restat decoded image file: {exc}") from exc
    if (current.st_size, current.st_mtime_ns) != (
        expected.file_size,
        expected.modified_ns,
    ):
        raise ImageInputError("image file changed after validation")

    if hasattr(image, "shape") and hasattr(image, "nbytes"):
        shape = tuple(int(value) for value in image.shape)
        if len(shape) not in (2, 3):
            raise ImageInputError("decoded image must have two or three dimensions")
        height, width = shape[:2]
        decoded_bytes = int(image.nbytes)
    elif isinstance(image, Image.Image):
        width, height = (int(value) for value in image.size)
        bands = max(1, len(image.getbands()))
        bytes_per_channel = (
            2 if "16" in image.mode else 4 if image.mode in {"I", "F"} else 1
        )
        decoded_bytes = width * height * bands * bytes_per_channel
    else:
        raise ImageInputError("decoder returned an unsupported image type")

    _validate_dimensions(width, height)
    if (width, height) != (expected.width, expected.height):
        raise ImageInputError("decoded dimensions differ from inspected metadata")
    if decoded_bytes > MAX_DECODED_IMAGE_BYTES:
        raise ImageInputError(f"decoded image exceeds {MAX_DECODED_IMAGE_BYTES} bytes")


def hash_validated_image_file(expected: ImageInputInfo) -> str:
    """Hash exactly the inspected image bytes without unbounded growth."""

    digest = hashlib.sha256()
    remaining = expected.file_size
    try:
        with expected.path.open("rb") as handle:
            while remaining:
                chunk = handle.read(min(1024 * 1024, remaining))
                if not chunk:
                    raise ImageInputError("image file changed during hashing")
                digest.update(chunk)
                remaining -= len(chunk)
            if handle.read(1):
                raise ImageInputError("image file changed during hashing")
        current = expected.path.stat()
    except ImageInputError:
        raise
    except OSError as exc:
        raise ImageInputError(f"cannot hash image file: {exc}") from exc
    if (current.st_size, current.st_mtime_ns) != (
        expected.file_size,
        expected.modified_ns,
    ):
        raise ImageInputError("image file changed during hashing")
    return digest.hexdigest()
