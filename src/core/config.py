"""Implementation of :mod:`src.core.config`.

Implementation preserved in the single ``src`` source tree.
"""

import json
import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional

from src.core.logger import logger

try:
    from pydantic import BaseModel, Field, ValidationError

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

    # Fallback dummy classes se pydantic não estiver instalado
    class BaseModel:
        def dict(self):
            return self.__dict__

        def model_dump(self):
            return self.__dict__

    def Field(default=None, **kwargs):
        return default


class ExportProfile(BaseModel):
    name: str
    engine: str
    options: Dict[str, Any] = Field(default_factory=dict)


class AppConfig(BaseModel):
    # Configuração Pydantic V2 (Permite ignorar campos extras no JSON)
    model_config = {"extra": "ignore"}

    config_version: int = Field(default=1, description="Version of config schema")
    last_folder: Optional[str] = None
    zoom: float = Field(default=1.0, ge=0.01, le=100.0)
    tool: str = "polygonal_lasso"
    window_geometry: Optional[str] = None
    recent_files: List[str] = Field(default_factory=list)
    default_export_profile: str = "default"
    profiles: List[ExportProfile] = Field(default_factory=list)

    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR",
    )
    log_to_file: bool = Field(default=False, description="Whether to log to file")
    log_file_path: Optional[str] = Field(
        default=None, description="Path to log file if log_to_file is True"
    )


class ConfigManager:
    def __init__(self, path: Optional[str]):
        self.path = path
        self.config = AppConfig()  # Start with defaults
        if self.path:
            self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return  # Empty file, use defaults
                data = json.loads(content)

            # Validate and load data
            self.config = AppConfig(**data)

        except ValidationError as e:
            logger.error(f"Config validation error: {e}")
            self._backup_corrupted()

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            self._backup_corrupted()

        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    def _backup_corrupted(self):
        """Renames corrupted config file so a new one can be created."""
        try:
            if self.path and os.path.exists(self.path):
                backup_path = self.path + ".corrupted"
                shutil.move(self.path, backup_path)
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

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.path), exist_ok=True)

            # Compatibility: Pydantic V2 uses model_dump(), V1 uses dict()
            if hasattr(self.config, "model_dump"):
                data = self.config.model_dump()
            else:
                data = self.config.dict()

            # Atomic write
            dirn = os.path.dirname(self.path)
            fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=dirn, text=True)

            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Replace original file
            if os.path.exists(self.path):
                os.replace(tmp_path, self.path)  # Atomic on POSIX, safe on Py3+ Windows
            else:
                os.rename(tmp_path, self.path)

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            if "tmp_path" in locals() and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
