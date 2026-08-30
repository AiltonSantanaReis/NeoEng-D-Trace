"""Strict, versioned clipboard payloads for professional scene authoring."""

from __future__ import annotations

import json
from typing import Final, Literal

from pydantic import Field, model_validator

from src.core.operational_limits import (
    MAX_GROUP_MEMBERS,
    MAX_PROJECT_GROUPS,
    MAX_PROJECT_OBJECTS,
)
from src.persistence.project_schema import (
    MAX_ID_LENGTH,
    MAX_NAME_LENGTH,
    StrictProjectModel,
)
from src.persistence.scene_authoring_schema import SceneObjectAuthoringRecord

SCENE_CLIPBOARD_MIME = "application/x-neoeng-d-trace-scene-objects"
SCENE_CLIPBOARD_FORMAT_ID: Final = "neoeng-d-trace-scene-objects"
SCENE_CLIPBOARD_SCHEMA_VERSION: Final = 1


class SceneClipboardGroupRecord(StrictProjectModel):
    """A group relation copied with a complete set of direct members."""

    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    members: list[str] = Field(max_length=MAX_GROUP_MEMBERS)
    visible: bool = True
    locked: bool = False
    parent_group_id: str | None = Field(default=None, max_length=MAX_ID_LENGTH)

    @model_validator(mode="after")
    def validate_members(self) -> "SceneClipboardGroupRecord":
        if any(not value or len(value) > MAX_ID_LENGTH for value in self.members):
            raise ValueError("clipboard group members must be non-empty object IDs")
        if len(self.members) != len(set(self.members)):
            raise ValueError("clipboard group members must be unique")
        return self


class SceneClipboardPayload(StrictProjectModel):
    """Strict JSON contract carried by the professional scene clipboard."""

    format_id: Literal["neoeng-d-trace-scene-objects"] = SCENE_CLIPBOARD_FORMAT_ID
    schema_version: Literal[1] = SCENE_CLIPBOARD_SCHEMA_VERSION
    objects: list[SceneObjectAuthoringRecord] = Field(
        min_length=1,
        max_length=MAX_PROJECT_OBJECTS,
    )
    groups: list[SceneClipboardGroupRecord] = Field(max_length=MAX_PROJECT_GROUPS)

    @model_validator(mode="after")
    def validate_references(self) -> "SceneClipboardPayload":
        object_ids = [item.id for item in self.objects]
        if len(object_ids) != len(set(object_ids)):
            raise ValueError("clipboard object IDs must be unique")
        group_ids = [item.id for item in self.groups]
        if len(group_ids) != len(set(group_ids)):
            raise ValueError("clipboard group IDs must be unique")
        known_objects = set(object_ids)
        for group in self.groups:
            if any(member not in known_objects for member in group.members):
                raise ValueError("clipboard group references an uncopied object")
        known_groups = set(group_ids)
        for group in self.groups:
            if (
                group.parent_group_id is not None
                and group.parent_group_id not in known_groups
            ):
                raise ValueError("clipboard group references an uncopied parent")
        for group in self.groups:
            seen = {group.id}
            current = group.parent_group_id
            while current is not None:
                if current in seen:
                    raise ValueError("clipboard group hierarchy contains a cycle")
                seen.add(current)
                parent = next(item for item in self.groups if item.id == current)
                current = parent.parent_group_id
        return self


def encode_scene_clipboard(
    objects: list[SceneObjectAuthoringRecord],
    groups: list[SceneClipboardGroupRecord] | None = None,
) -> bytes:
    """Validate and serialize a scene clipboard payload as UTF-8 JSON."""

    payload = SceneClipboardPayload(objects=objects, groups=groups or [])
    return payload.model_dump_json().encode("utf-8")


def decode_scene_clipboard(value: bytes | bytearray) -> SceneClipboardPayload:
    """Decode a strict payload and normalize all invalid input to ValueError."""

    if not isinstance(value, (bytes, bytearray)):
        raise ValueError("scene clipboard payload must be bytes")
    try:
        return SceneClipboardPayload.model_validate_json(bytes(value), strict=True)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("invalid or incompatible scene clipboard payload") from exc
