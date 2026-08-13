"""Implementation of :mod:`src.core.config`.

Implementation preserved in the single ``src`` source tree.
"""

import json
import os
import tempfile
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.core.logger import logger
from src.core.operational_limits import (
    MAX_CONFIG_FILE_BYTES,
    MAX_CONFIG_PATH_LENGTH,
    MAX_CONFIG_TEXT_LENGTH,
    MAX_EXPORT_PROFILES,
    MAX_PROFILE_OPTIONS,
    MAX_RECENT_FILES,
    MAX_WINDOW_GEOMETRY_LENGTH,
)


class ConfigLimitError(ValueError):
    """Raised when configuration exceeds a bounded resource contract."""


def _reject_duplicate_object_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


class StrictConfigModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        validate_assignment=True,
    )


class ExportProfile(StrictConfigModel):
    name: str = Field(min_length=1, max_length=MAX_CONFIG_TEXT_LENGTH)
    engine: str = Field(min_length=1, max_length=MAX_CONFIG_TEXT_LENGTH)
    options: Dict[str, Any] = Field(
        default_factory=dict,
        max_length=MAX_PROFILE_OPTIONS,
    )


class AppConfig(StrictConfigModel):
    config_version: Literal[1] = 1
    last_folder: Optional[str] = Field(default=None, max_length=MAX_CONFIG_PATH_LENGTH)
    zoom: float = Field(default=1.0, ge=0.01, le=100.0)
    tool: str = Field(default="polygonal_lasso", max_length=MAX_CONFIG_TEXT_LENGTH)
    window_geometry: Optional[str] = Field(
        default=None,
        max_length=MAX_WINDOW_GEOMETRY_LENGTH,
    )
    recent_files: List[str] = Field(
        default_factory=list,
        max_length=MAX_RECENT_FILES,
    )
    default_export_profile: str = Field(
        default="default",
        max_length=MAX_CONFIG_TEXT_LENGTH,
    )
    profiles: List[ExportProfile] = Field(
        default_factory=list,
        max_length=MAX_EXPORT_PROFILES,
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_to_file: bool = False
    log_file_path: Optional[str] = Field(
        default=None,
        max_length=MAX_CONFIG_PATH_LENGTH,
    )


class ConfigManager:
    def __init__(self, path: Optional[str]):
        self.path = path
        self.config = AppConfig()  # Start with defaults
        if self.path:
            self._load()

    def _load(self):
        path = self.path
        if path is None or not os.path.exists(path):
            return

        try:
            size = os.path.getsize(path)
            if size > MAX_CONFIG_FILE_BYTES:
                raise ConfigLimitError(
                    f"config file exceeds {MAX_CONFIG_FILE_BYTES} bytes"
                )
            with open(path, "rb") as handle:
                raw = handle.read(MAX_CONFIG_FILE_BYTES + 1)
            if len(raw) > MAX_CONFIG_FILE_BYTES:
                raise ConfigLimitError(
                    f"config file exceeds {MAX_CONFIG_FILE_BYTES} bytes"
                )
            content = raw.decode("utf-8", errors="strict").strip()
            if not content:
                return
            data = json.loads(
                content,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValueError(f"non-finite JSON number is not allowed: {value}")
                ),
                object_pairs_hook=_reject_duplicate_object_keys,
            )
            self.config = AppConfig.model_validate(data)

        except (
            ValidationError,
            ConfigLimitError,
            UnicodeDecodeError,
            ValueError,
        ) as exc:
            logger.error("Config validation error: %s", exc)
            self._backup_corrupted()

        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to load config: %s", exc)
            self._backup_corrupted()

        except Exception as exc:
            logger.error("Unexpected config load failure: %s", exc)
            self._backup_corrupted()

    def _backup_corrupted(self):
        """Renames corrupted config file so a new one can be created."""
        try:
            if self.path and os.path.exists(self.path):
                backup_path = self.path + ".corrupted"
                os.replace(self.path, backup_path)
                logger.warning(f"Corrupted config moved to {backup_path}")
        except Exception as e:
            logger.error(f"Failed to backup corrupted config: {e}")

    def get(self, key: str, default: Any = None):
        return getattr(self.config, key, default)

    def set(self, key: str, value: Any):
        if hasattr(self.config, key):
            setattr(self.config, key, value)
        else:
            # Log warning but don't crash on setting unknown key
            logger.warning(f"Attempted to set unknown config key: {key}")

    def save(self):
        if not self.path:
            return

        temporary_path = None
        try:
            data = self.config.model_dump(mode="json")
            payload = (
                json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
            ).encode("utf-8")
            if len(payload) > MAX_CONFIG_FILE_BYTES:
                raise ConfigLimitError(
                    f"serialized config exceeds {MAX_CONFIG_FILE_BYTES} bytes"
                )

            directory = os.path.dirname(self.path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            descriptor, temporary_path = tempfile.mkstemp(
                suffix=".tmp",
                dir=directory or ".",
            )
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.path)
            temporary_path = None

        except Exception as exc:
            logger.error("Failed to save config: %s", exc)
        finally:
            if temporary_path and os.path.exists(temporary_path):
                try:
                    os.remove(temporary_path)
                except OSError:
                    pass
