"""Platform-specific writable application-state paths."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Mapping

from src.core.app_identity import CONFIG_DIR_NAME


def default_state_directory(
    environment: Mapping[str, str] | None = None,
    *,
    home: Path | None = None,
    platform: str | None = None,
) -> Path:
    values = os.environ if environment is None else environment
    user_home = Path.home() if home is None else home
    current_platform = sys.platform if platform is None else platform

    if current_platform == "win32":
        root = Path(values.get("LOCALAPPDATA") or user_home / "AppData" / "Local")
    elif current_platform == "darwin":
        root = user_home / "Library" / "Application Support"
    else:
        root = Path(values.get("XDG_STATE_HOME") or user_home / ".local" / "state")
    return root / CONFIG_DIR_NAME


def default_autosave_path() -> Path:
    return default_state_directory() / "autosave" / "recovery.json"


def default_config_path() -> Path:
    return default_state_directory() / "config.json"
