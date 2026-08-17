"""Load the approved NeoEng-D-Trace application icon."""

from __future__ import annotations

import sys
from pathlib import Path

ICON_RELATIVE_PATH = Path("assets") / "branding" / "neoeng-d-trace-icon.ico"


def application_icon_path() -> Path:
    """Return the icon path for source checkouts and PyInstaller bundles."""

    frozen_root = getattr(sys, "_MEIPASS", None)
    candidates = []
    if frozen_root:
        candidates.append(Path(frozen_root) / ICON_RELATIVE_PATH)
    candidates.append(Path(__file__).resolve().parents[2] / ICON_RELATIVE_PATH)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "NeoEng-D-Trace application icon is missing: "
        f"{ICON_RELATIVE_PATH.as_posix()}"
    )
