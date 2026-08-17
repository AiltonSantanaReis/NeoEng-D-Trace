"""Qt adapter for the approved NeoEng-D-Trace application icon."""

from __future__ import annotations

from PySide6.QtGui import QIcon

from src.core.app_icon import application_icon_path


def application_icon() -> QIcon:
    """Load and validate the approved application icon for Qt widgets."""

    path = application_icon_path()
    icon = QIcon(str(path))
    if icon.isNull():
        raise ValueError(f"Unable to load application icon: {path.name}")
    return icon
