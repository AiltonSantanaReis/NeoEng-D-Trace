"""Generate the deterministic Windows icon from the approved PNG source."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps

ICON_SIZES = (16, 32, 48, 64, 128, 256)


def build_icon(source: Path, destination: Path) -> None:
    """Crop transparent margins, preserve aspect ratio, and write a multi-size ICO."""

    image = Image.open(source).convert("RGBA")
    alpha_bbox = image.getchannel("A").getbbox()
    if alpha_bbox is None:
        raise ValueError("icon source has no visible pixels")
    image = image.crop(alpha_bbox)
    side = max(image.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(image, ((side - image.width) // 2, (side - image.height) // 2), image)
    square = ImageOps.contain(square, (256, 256), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    canvas.paste(
        square, ((256 - square.width) // 2, (256 - square.height) // 2), square
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, format="ICO", sizes=[(size, size) for size in ICON_SIZES])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    build_icon(args.source.resolve(), args.destination.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
