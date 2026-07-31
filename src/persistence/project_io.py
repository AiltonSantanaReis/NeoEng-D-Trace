"""Read, validate, migrate, and atomically write project documents."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from src.core.app_identity import PROJECT_FORMAT_ID, PROJECT_FORMAT_VERSION

from .errors import (
    LegacyProjectMigrationError,
    ProjectFormatError,
    ProjectReadError,
    ProjectValidationError,
    ProjectWriteError,
    UnsupportedProjectVersionError,
)
from .project_schema import (
    MAX_ID_LENGTH,
    MAX_NAME_LENGTH,
    MAX_PROJECT_FILE_BYTES,
    BezierSegmentRecord,
    GroupRecord,
    ImageReferenceRecord,
    LayerRecord,
    PointRecord,
    ProjectDocumentV1,
    SceneObjectRecord,
    default_metadata,
)

if TYPE_CHECKING:
    from src.models.scene import Scene


_LEGACY_ROOT_FIELDS = frozenset(
    {
        "layers",
        "objects",
        "groups",
        "collisions",
    }
)


@dataclass(frozen=True)
class LoadedProject:
    """A fully validated document and its explicit migration warnings."""

    document: ProjectDocumentV1
    warnings: tuple[str, ...]
    migrated_from_legacy: bool


class _LegacyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _LegacyLayer(_LegacyModel):
    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    name: str = Field(default="Layer", max_length=MAX_NAME_LENGTH)
    visible: bool = True
    locked: bool = False


class _LegacyObject(_LegacyModel):
    polygon: list[list[int | float]] = Field(default_factory=list)
    layer_id: str | None = Field(default=None, max_length=MAX_ID_LENGTH)

    @field_validator("polygon")
    @classmethod
    def validate_polygon_points(
        cls,
        polygon: list[list[int | float]],
    ) -> list[list[int | float]]:
        for point in polygon:
            if len(point) != 2:
                raise ValueError("legacy polygon points must contain two coordinates")
            for value in point:
                if isinstance(value, bool):
                    raise ValueError("boolean coordinates are not allowed")
                if isinstance(value, float) and not _is_finite(value):
                    raise ValueError("coordinates must be finite")
        return polygon


class _LegacyGroup(_LegacyModel):
    id: str = Field(min_length=1, max_length=MAX_ID_LENGTH)
    name: str = Field(default="Group", max_length=MAX_NAME_LENGTH)
    visible: bool = True
    locked: bool = False
    members: list[str] = Field(default_factory=list)


class _LegacyProject(_LegacyModel):
    layers: list[_LegacyLayer] = Field(default_factory=list)
    objects: dict[str, _LegacyObject] = Field(default_factory=dict)
    groups: list[_LegacyGroup] = Field(default_factory=list)
    collisions: list[str] = Field(default_factory=list)


def _is_finite(value: float) -> bool:
    return value == value and value not in (float("inf"), float("-inf"))


def _point(value: Any) -> PointRecord:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ProjectValidationError("points must contain exactly two coordinates")
    try:
        return PointRecord(x=value[0], y=value[1])
    except ValidationError as exc:
        raise ProjectValidationError(str(exc)) from exc


def _collision_point(value: Any) -> PointRecord:
    point = _point(value)
    return PointRecord(x=float(point.x), y=float(point.y))


def _bezier_segment(value: Any) -> BezierSegmentRecord:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ProjectValidationError("Bezier segments must contain exactly four points")
    return BezierSegmentRecord(
        p0=_point(value[0]),
        p1=_point(value[1]),
        p2=_point(value[2]),
        p3=_point(value[3]),
    )


def _hash_file_if_available(path: Path) -> str | None:
    try:
        if not path.is_file():
            return None
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _is_absolute_path_text(path: str) -> bool:
    return PurePosixPath(path).is_absolute() or PureWindowsPath(path).is_absolute()


def _image_reference(scene: "Scene", project_path: Path) -> ImageReferenceRecord | None:
    raw_path = getattr(scene, "image_path", None)
    if raw_path is None:
        return None

    path_text = os.fsdecode(raw_path)
    stored_path_kind = getattr(scene, "image_path_kind", None)
    path_kind: Literal["relative", "absolute"]
    if stored_path_kind is None:
        path_kind = "absolute" if _is_absolute_path_text(path_text) else "relative"
    elif stored_path_kind in ("relative", "absolute"):
        path_kind = cast(Literal["relative", "absolute"], stored_path_kind)
    else:
        raise ProjectValidationError(
            f"unsupported image path kind: {stored_path_kind!r}"
        )

    hash_candidate = (
        Path(path_text) if path_kind == "absolute" else project_path.parent / path_text
    )
    stored_sha256 = getattr(scene, "image_sha256", None)
    preserve_loaded_reference = bool(getattr(scene, "_image_reference_loaded", False))
    image_sha256 = (
        stored_sha256
        if preserve_loaded_reference
        else _hash_file_if_available(hash_candidate)
    )

    return ImageReferenceRecord(
        path=path_text,
        path_kind=path_kind,
        sha256=image_sha256,
    )


def build_project_document(
    scene: "Scene",
    project_path: str | os.PathLike[str],
) -> ProjectDocumentV1:
    """Build and validate a deterministic v1 document from a scene."""

    try:
        destination = Path(project_path)

        layers = [
            LayerRecord(
                id=layer.id,
                name=layer.name,
                visible=layer.visible,
                locked=layer.locked,
            )
            for layer in scene.layers
        ]

        orphan_collisions = sorted(set(scene.collision_shapes) - set(scene.objects))
        if orphan_collisions:
            raise ProjectValidationError(
                "collision shapes reference unknown objects: " f"{orphan_collisions!r}"
            )

        objects: list[SceneObjectRecord] = []
        for object_id, scene_object in scene.objects.items():
            if scene_object.id != object_id:
                raise ProjectValidationError(
                    f"scene object key {object_id!r} does not match "
                    f"object ID {scene_object.id!r}"
                )
            collision_value = scene.collision_shapes.get(object_id)
            beziers_value = getattr(scene_object, "beziers", None)
            objects.append(
                SceneObjectRecord(
                    id=object_id,
                    layer_id=scene_object.layer_id or "layer_default",
                    polygon=[_point(value) for value in scene_object.polygon],
                    collision=(
                        [_collision_point(value) for value in collision_value]
                        if collision_value is not None
                        else None
                    ),
                    beziers=(
                        [_bezier_segment(value) for value in beziers_value]
                        if beziers_value is not None
                        else None
                    ),
                )
            )

        groups = [
            GroupRecord(
                id=group.id,
                name=group.name,
                visible=group.visible,
                locked=group.locked,
                members=list(group.members),
            )
            for group in scene.groups
        ]

        return ProjectDocumentV1(
            metadata=default_metadata(),
            image=_image_reference(scene, destination),
            layers=layers,
            objects=objects,
            groups=groups,
        )
    except ProjectValidationError:
        raise
    except ValidationError as exc:
        raise ProjectValidationError(str(exc)) from exc
    except (AttributeError, TypeError, ValueError) as exc:
        raise ProjectValidationError(
            f"scene cannot be represented by project schema v1: {exc}"
        ) from exc


def _serialize_document(document: ProjectDocumentV1) -> bytes:
    try:
        payload = document.model_dump(mode="json")
        text = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        return (text + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProjectValidationError(f"project cannot be serialized: {exc}") from exc


def _atomic_write(destination: Path, payload: bytes) -> None:
    parent = destination.parent
    if not parent.exists():
        raise ProjectWriteError(f"destination directory does not exist: {parent}")
    if not parent.is_dir():
        raise ProjectWriteError(f"destination parent is not a directory: {parent}")
    if destination.exists() and destination.is_dir():
        raise ProjectWriteError(f"destination is a directory: {destination}")
    if len(payload) > MAX_PROJECT_FILE_BYTES:
        raise ProjectWriteError(
            f"serialized project exceeds {MAX_PROJECT_FILE_BYTES} bytes"
        )

    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=parent,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
        temporary_path = None
    except ProjectWriteError:
        raise
    except OSError as exc:
        raise ProjectWriteError(
            f"failed to atomically write project {destination}: {exc}"
        ) from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def save_scene_project(
    scene: "Scene",
    path: str | os.PathLike[str],
) -> None:
    """Validate and atomically save the complete persistent scene state."""

    destination = Path(path)
    document = build_project_document(scene, destination)
    _atomic_write(destination, _serialize_document(document))


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _reject_duplicate_object_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise ProjectReadError(f"project file not found: {path}")
    if not path.is_file():
        raise ProjectReadError(f"project path is not a file: {path}")

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ProjectReadError(f"cannot stat project file {path}: {exc}") from exc

    if size > MAX_PROJECT_FILE_BYTES:
        raise ProjectReadError(f"project file exceeds {MAX_PROJECT_FILE_BYTES} bytes")

    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ProjectReadError(f"cannot read project file {path}: {exc}") from exc

    if len(raw) > MAX_PROJECT_FILE_BYTES:
        raise ProjectReadError(f"project file exceeds {MAX_PROJECT_FILE_BYTES} bytes")

    if raw.startswith(b"\xef\xbb\xbf"):
        raise ProjectFormatError("UTF-8 BOM is not allowed")

    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ProjectFormatError("project file is not valid UTF-8") from exc

    try:
        return json.loads(
            text,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_object_keys,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ProjectFormatError(f"invalid project JSON: {exc}") from exc


def _validate_v1_document(value: Any) -> ProjectDocumentV1:
    try:
        return ProjectDocumentV1.model_validate(value, strict=True)
    except ValidationError as exc:
        raise ProjectValidationError(str(exc)) from exc


def _migrate_legacy(value: Any) -> LoadedProject:
    if not isinstance(value, dict) or set(value) != _LEGACY_ROOT_FIELDS:
        raise LegacyProjectMigrationError(
            "unversioned project does not match the known legacy root fields"
        )

    try:
        legacy = _LegacyProject.model_validate(value, strict=True)
    except ValidationError as exc:
        raise LegacyProjectMigrationError(str(exc)) from exc

    layers = [
        LayerRecord(
            id=item.id,
            name=item.name,
            visible=item.visible,
            locked=item.locked,
        )
        for item in legacy.layers
    ]
    if not any(layer.id == "layer_default" for layer in layers):
        layers.insert(
            0,
            LayerRecord(
                id="layer_default",
                name="Default",
                visible=True,
                locked=False,
            ),
        )

    collision_ids = set(legacy.collisions)
    unknown_collision_ids = sorted(collision_ids - set(legacy.objects))
    if unknown_collision_ids:
        raise LegacyProjectMigrationError(
            "legacy collision references unknown objects: " f"{unknown_collision_ids!r}"
        )

    objects: list[SceneObjectRecord] = []
    for object_id, item in legacy.objects.items():
        if not object_id or len(object_id) > MAX_ID_LENGTH:
            raise LegacyProjectMigrationError("legacy object IDs must be non-empty")
        polygon = [_point(point) for point in item.polygon]
        objects.append(
            SceneObjectRecord(
                id=object_id,
                layer_id=item.layer_id or "layer_default",
                polygon=polygon,
                collision=(
                    [
                        PointRecord(
                            x=float(point.x),
                            y=float(point.y),
                        )
                        for point in polygon
                    ]
                    if object_id in collision_ids
                    else None
                ),
                beziers=None,
            )
        )

    groups = [
        GroupRecord(
            id=item.id,
            name=item.name,
            visible=item.visible,
            locked=item.locked,
            members=list(item.members),
        )
        for item in legacy.groups
    ]

    try:
        document = ProjectDocumentV1(
            metadata=default_metadata(),
            image=None,
            layers=layers,
            objects=objects,
            groups=groups,
        )
    except ValidationError as exc:
        raise LegacyProjectMigrationError(str(exc)) from exc

    warnings = [
        "legacy_project_migrated_to_schema_v1",
        "legacy_format_does_not_store_image_or_bezier_data",
    ]
    if collision_ids:
        warnings.append("legacy_collision_geometry_reconstructed_from_visual_polygon")

    return LoadedProject(
        document=document,
        warnings=tuple(warnings),
        migrated_from_legacy=True,
    )


def load_project_document(
    path: str | os.PathLike[str],
) -> LoadedProject:
    """Read and validate a v1 document or explicitly migrate known legacy JSON."""

    value = _read_json(Path(path))
    if not isinstance(value, dict):
        raise ProjectFormatError("project root must be a JSON object")

    has_format = "format_id" in value
    has_version = "schema_version" in value

    if has_format or has_version:
        if not has_format or not has_version:
            raise ProjectFormatError(
                "format_id and schema_version must be present together"
            )

        format_id = value.get("format_id")
        version = value.get("schema_version")

        if format_id != PROJECT_FORMAT_ID:
            raise ProjectFormatError(
                f"unsupported project format identifier: {format_id!r}"
            )
        if isinstance(version, bool) or not isinstance(version, int):
            raise ProjectFormatError("schema_version must be an integer")
        if version != PROJECT_FORMAT_VERSION:
            raise UnsupportedProjectVersionError(
                f"unsupported project schema version: {version}"
            )

        return LoadedProject(
            document=_validate_v1_document(value),
            warnings=(),
            migrated_from_legacy=False,
        )

    return _migrate_legacy(value)


def _point_tuple(point: PointRecord) -> tuple[int | float, int | float]:
    return (point.x, point.y)


def load_project_into_scene(
    scene: "Scene",
    path: str | os.PathLike[str],
) -> tuple[str, ...]:
    """Replace scene state only after the complete document is validated."""

    loaded = load_project_document(path)
    document = loaded.document

    from src.models.scene import Group, Layer, SceneObject

    new_layers = [
        Layer(
            id=item.id,
            name=item.name,
            visible=item.visible,
            locked=item.locked,
        )
        for item in document.layers
    ]

    new_objects: dict[str, SceneObject] = {}
    new_collisions: dict[str, list[tuple[float, float]]] = {}
    for object_record in document.objects:
        polygon = [_point_tuple(point) for point in object_record.polygon]
        scene_object = SceneObject(
            object_record.id,
            cast(Any, polygon),
            object_record.layer_id,
        )
        if object_record.beziers is not None:
            cast(Any, scene_object).beziers = [
                (
                    _point_tuple(segment.p0),
                    _point_tuple(segment.p1),
                    _point_tuple(segment.p2),
                    _point_tuple(segment.p3),
                )
                for segment in object_record.beziers
            ]
        new_objects[object_record.id] = scene_object

        if object_record.collision is not None:
            new_collisions[object_record.id] = [
                (float(point.x), float(point.y)) for point in object_record.collision
            ]

    new_groups: list[Group] = []
    for group_record in document.groups:
        group = Group(
            id=group_record.id,
            name=group_record.name,
            visible=group_record.visible,
            locked=group_record.locked,
        )
        group.members = list(group_record.members)
        new_groups.append(group)

    new_image_path = document.image.path if document.image is not None else None
    new_image_path_kind = (
        document.image.path_kind if document.image is not None else None
    )
    new_image_sha256 = document.image.sha256 if document.image is not None else None

    scene.image = None
    scene.image_path = new_image_path
    scene.image_path_kind = new_image_path_kind
    scene.image_sha256 = new_image_sha256
    scene._image_reference_loaded = document.image is not None
    scene.layers = new_layers
    scene.objects = new_objects
    scene.groups = new_groups
    scene.collision_shapes = new_collisions
    scene.selected_id = None
    scene._notify()

    return loaded.warnings
