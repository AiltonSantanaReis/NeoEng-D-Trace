"""Versioned, bounded timeline data; playback state is never persisted."""

from typing import Literal

from pydantic import Field, model_validator

from src.persistence.project_schema import StrictProjectModel


class SceneClip(StrictProjectModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    kind: Literal[
        "camera", "motion", "light", "rain", "snow", "dust", "fire", "audio", "text"
    ]
    start: float = Field(default=0.0, ge=0, le=86400, allow_inf_nan=False)
    duration: float = Field(default=5.0, gt=0, le=86400, allow_inf_nan=False)
    enabled: bool = True
    loop: bool = False
    target_id: str | None = None
    layer_id: str | None = None
    asset_id: str | None = None
    text: str = Field(default="", max_length=4096)
    color: str = Field(default="#ffffff", pattern=r"^#[0-9a-fA-F]{6}$")
    x: float = Field(default=0, ge=-1e6, le=1e6, allow_inf_nan=False)
    y: float = Field(default=0, ge=-1e6, le=1e6, allow_inf_nan=False)
    end_x: float = Field(default=0, ge=-1e6, le=1e6, allow_inf_nan=False)
    end_y: float = Field(default=0, ge=-1e6, le=1e6, allow_inf_nan=False)
    zoom: float = Field(default=1, ge=0.001, le=1000, allow_inf_nan=False)
    end_zoom: float = Field(default=1, ge=0.001, le=1000, allow_inf_nan=False)
    rotation: float = Field(default=0, ge=-36000, le=36000, allow_inf_nan=False)
    end_rotation: float = Field(default=0, ge=-36000, le=36000, allow_inf_nan=False)
    opacity: float = Field(default=1, ge=0, le=1, allow_inf_nan=False)
    end_opacity: float = Field(default=1, ge=0, le=1, allow_inf_nan=False)
    intensity: float = Field(default=1, ge=0, le=10, allow_inf_nan=False)
    seed: int = Field(default=1, ge=0, le=2147483647)

    @model_validator(mode="after")
    def required_references(self):
        if self.kind == "motion" and not self.target_id:
            raise ValueError("motion requires an object target")
        if self.kind != "motion" and self.target_id is not None:
            raise ValueError("only motion clips can target an object")
        if self.kind == "audio" and not self.asset_id:
            raise ValueError("audio requires a project asset")
        return self


class SceneSequence(StrictProjectModel):
    schema_version: Literal[1] = 1
    duration: float = Field(default=30, gt=0, le=86400, allow_inf_nan=False)
    loop: bool = True
    clips: list[SceneClip] = Field(default_factory=list, max_length=2048)

    @model_validator(mode="after")
    def validate_tracks(self):
        ids = [clip.id for clip in self.clips]
        if len(ids) != len(set(ids)):
            raise ValueError("clip IDs must be unique")
        for clip in self.clips:
            if clip.start + clip.duration > self.duration + 1e-8:
                raise ValueError("clip exceeds sequence duration")
        # Two simultaneous writers on a transform are ambiguous, not last-write-wins.
        writers = [
            c for c in self.clips if c.enabled and c.kind in {"camera", "motion"}
        ]
        for index, clip in enumerate(writers):
            for other in writers[index + 1 :]:
                if (clip.kind, clip.target_id) != (other.kind, other.target_id):
                    continue
                if max(clip.start, other.start) < min(
                    clip.start + clip.duration, other.start + other.duration
                ):
                    raise ValueError("overlapping transform clips share a target")
        return self
