"""Implementation of :mod:`src.models.scene`.

Implementation preserved in the single ``src`` source tree.
"""

import time
import uuid
from typing import Callable, Dict, List, Optional, Tuple

from src.core.bezier_geometry import (
    BezierSegments,
    canonical_point,
    canonicalize_beziers,
    sample_beziers_to_polygon,
)
from src.core.logger import logger
from src.core.operational_limits import (
    MAX_GROUP_MEMBERS,
    MAX_PROJECT_GROUPS,
    MAX_PROJECT_LAYERS,
    MAX_PROJECT_OBJECTS,
)
from src.core.polygon_validation import is_valid_polygon as _validate_polygon
from src.core.polygon_validation import lines_intersect
from src.core.polygon_validation import signed_polygon_area2 as _signed_polygon_area2
from src.core.transform_geometry import anchor_for_polygon, finite_float
from src.core.validation_events import (
    elapsed_ms,
    object_token,
    record_validation_event,
    record_validation_exception,
)

try:
    from shapely.geometry import Polygon

    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False

_lines_intersect = lines_intersect


def _normalize_polygon_winding(points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Remove a duplicated terminal vertex and enforce counter-clockwise order."""

    normalized = list(points)
    if len(normalized) > 1 and normalized[0] == normalized[-1]:
        normalized.pop()
    if len(normalized) >= 3 and _signed_polygon_area2(normalized) < 0:
        normalized.reverse()
    return normalized


def _remove_close_duplicates(
    points: List[Tuple[float, float]], tol: float = 1.0
) -> List[Tuple[float, float]]:
    """Remove pontos repetidos ou muito próximos sucessivos."""
    if not points:
        return []
    out = [points[0]]
    for p in points[1:]:
        last = out[-1]
        dx = p[0] - last[0]
        dy = p[1] - last[1]
        if (dx * dx + dy * dy) ** 0.5 >= tol:
            out.append(p)
    # Also check closing point against first
    if len(out) > 1:
        dx = out[0][0] - out[-1][0]
        dy = out[0][1] - out[-1][1]
        if (dx * dx + dy * dy) ** 0.5 < tol:
            out.pop()  # remove last if equals first
    return out


def _remove_colinear(
    points: List[Tuple[float, float]], tol: float = 1e-6
) -> List[Tuple[float, float]]:
    """Remove vértices colineares consecutivos (simplificação básica)."""
    if len(points) < 3:
        return points
    out = []
    n = len(points)
    for i in range(n):
        a = points[i - 1]
        b = points[i]
        c = points[(i + 1) % n]
        # Compute cross product magnitude for (b-a) x (c-b)
        bax = b[0] - a[0]
        bay = b[1] - a[1]
        cbx = c[0] - b[0]
        cby = c[1] - b[1]
        cross = bax * cby - bay * cbx
        if abs(cross) > tol:
            out.append(b)
    # If simplification removed too many points, fall back to original
    if len(out) < 3:
        return points
    return out


def _attempt_repair(
    points: List[Tuple[int, int]],
) -> Tuple[List[Tuple[int, int]], bool]:
    """Try to repair a polygon returning (new_points, repaired_flag).

    Repairs attempted:
    - remove near-duplicate consecutive points
    - remove trivial colinear vertices
    - when Shapely available, try buffer(0) to fix self-intersections
    """
    if not points:
        return points, False

    # Work in canonical floats for intermediate math. Invalid or
    # unrepresentable coordinates are not repair candidates.
    try:
        ptsf = [
            canonical_point(point, label=f"polygon repair point {index}")
            for index, point in enumerate(points)
        ]
    except ValueError:
        return points, False
    ptsf = _remove_close_duplicates(ptsf, tol=1.0)
    ptsf = _remove_colinear(ptsf, tol=1e-6)

    if len(ptsf) < 3:
        return points, False

    # Try shapely-based repairs if available
    if HAS_SHAPELY:
        try:
            poly = Polygon(ptsf)
            if not poly.is_valid:
                # buffer(0) is a common trick to fix self-intersections
                fixed = poly.buffer(0)
                if fixed and not fixed.is_empty:
                    # Extract exterior coordinates and convert to ints
                    coords = list(fixed.exterior.coords)[:-1]
                    if len(coords) >= 3:
                        repaired = [(int(round(x)), int(round(y))) for x, y in coords]
                        repaired = _normalize_polygon_winding(repaired)
                        if _validate_polygon(repaired):
                            return repaired, True
            else:
                # polygon is valid after simple cleaning
                cleaned = [(int(round(x)), int(round(y))) for x, y in ptsf]
                cleaned = _normalize_polygon_winding(cleaned)
                if _validate_polygon(cleaned):
                    return cleaned, True
        except Exception:
            # Fall through to fallback
            pass

    # Fallback heuristic: convert cleaned floats to ints and validate
    candidate = [(int(round(x)), int(round(y))) for x, y in ptsf]
    candidate = _normalize_polygon_winding(candidate)
    if _validate_polygon(candidate):
        return candidate, True

    return points, False


class Layer:
    def __init__(
        self,
        id: Optional[str] = None,
        name: str = "Layer",
        visible: bool = True,
        locked: bool = False,
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.visible = visible
        self.locked = locked


class Group:
    def __init__(
        self,
        id: Optional[str] = None,
        name: str = "Group",
        visible: bool = True,
        locked: bool = False,
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.visible = visible
        self.locked = locked
        self.members: List[str] = []


class SceneObject:
    def __init__(
        self,
        oid: str,
        polygon: List[Tuple[int, int]],
        layer_id: Optional[str] = None,
    ):
        self.id = oid
        self.polygon = polygon
        self.layer_id = layer_id
        self.beziers: Optional[BezierSegments] = None
        self.pivot = (0.5, 0.5)
        self.position = (
            (*anchor_for_polygon(polygon, self.pivot), 0.0)
            if polygon
            else (0.0, 0.0, 0.0)
        )
        self.rotation = (0.0, 0.0, 0.0)
        self.scale = (1.0, 1.0, 1.0)

    def set_pivot(self, x: float, y: float) -> None:
        """Set the normalized bounding-box pivot and keep it anchored."""

        self.pivot = (finite_float(x, "pivot.x"), finite_float(y, "pivot.y"))
        self.sync_position_from_polygon()

    def sync_position_from_polygon(self) -> None:
        """Recompute the world position of the current normalized pivot."""

        if self.polygon:
            anchor = anchor_for_polygon(self.polygon, self.pivot)
            self.position = (anchor[0], anchor[1], self.position[2])


class Scene:
    def __init__(self):
        self.image = None
        self.image_path = None
        self.image_path_kind: Optional[str] = None
        self.image_sha256: Optional[str] = None
        self._image_reference_loaded = False
        self.objects: Dict[str, SceneObject] = {}
        self.layers: List[Layer] = []
        self.groups: List[Group] = []
        # Static collision shapes
        self.collision_shapes: Dict[str, List[Tuple[float, float]]] = {}
        self.collision_parts: Dict[str, List[List[Tuple[float, float]]]] = {}
        self.selected_id: Optional[str] = None
        self.selected_ids: List[str] = []
        self._listeners: List[Callable[[], None]] = []
        self.cmd = None

        # By default do not attempt to silently repair invalid polygons.
        # This must be opt-in by consumers that want tolerant behavior.
        self.auto_repair = False

        # create default layer
        default = Layer(id="layer_default", name="Default", visible=True, locked=False)
        self.layers.append(default)

    # subscription
    def subscribe(self, cb: Callable[[], None]):
        if cb not in self._listeners:
            self._listeners.append(cb)

    def _notify(self):
        to_remove = []
        for cb in list(self._listeners):
            try:
                cb()
            except Exception as e:
                logger.warning(f"Listener failed, removing: {e}")
                to_remove.append(cb)
        for cb in to_remove:
            self._listeners.remove(cb)

    # --- Formas de colisão estática ---
    def set_object_collision(self, oid: str, enabled: bool):
        """Ativa ou desativa a forma de colisão de um objeto."""
        if oid not in self.objects:
            return

        if enabled:
            obj = self.objects[oid]
            # Canonicaliza coordenadas da forma de colisão.
            self.collision_shapes[oid] = [
                (float(p[0]), float(p[1])) for p in obj.polygon
            ]
            self.collision_parts.pop(oid, None)
        else:
            if oid in self.collision_shapes:
                del self.collision_shapes[oid]
            self.collision_parts.pop(oid, None)
        self._notify()

    def has_collision(self, oid: str) -> bool:
        """Retorna True se o objeto tem colisão ativa."""
        return oid in self.collision_shapes

    # --- Layers Methods ---
    def create_layer(self, name: str = "Layer") -> Layer:
        if len(self.layers) >= MAX_PROJECT_LAYERS:
            raise ValueError(f"layer limit is {MAX_PROJECT_LAYERS}")
        layer = Layer(name=name)
        self.layers.append(layer)
        self._notify()
        return layer

    def remove_layer(self, layer_id: str):
        if layer_id == "layer_default":
            raise ValueError("Cannot remove default layer")
        self.layers = [layer for layer in self.layers if layer.id != layer_id]
        for obj in self.objects.values():
            if obj.layer_id == layer_id:
                obj.layer_id = "layer_default"
        self._notify()

    def move_layer(self, layer_id: str, new_index: int):
        ids = [layer.id for layer in self.layers]
        if layer_id not in ids:
            raise KeyError("layer not found")
        cur = ids.index(layer_id)
        layer = self.layers.pop(cur)
        new_index = max(0, min(new_index, len(self.layers)))
        self.layers.insert(new_index, layer)
        self._notify()

    def set_layer_visibility(self, layer_id: str, visible: bool):
        for layer in self.layers:
            if layer.id == layer_id:
                layer.visible = bool(visible)
                self._notify()
                return
        raise KeyError("layer not found")

    def set_layer_lock(self, layer_id: str, locked: bool):
        for layer in self.layers:
            if layer.id == layer_id:
                layer.locked = bool(locked)
                self._notify()
                return
        raise KeyError("layer not found")

    def set_object_layer(self, object_id: str, layer_id: str):
        if object_id not in self.objects:
            raise KeyError("object not found")
        if layer_id not in [layer.id for layer in self.layers]:
            raise KeyError("layer not found")
        self.objects[object_id].layer_id = layer_id
        self._notify()

    # --- Objects ---
    def add_object(
        self,
        oid: str,
        polygon: List[Tuple[int, int]],
        layer_id: Optional[str] = None,
        select: bool = False,
    ):
        if oid not in self.objects and len(self.objects) >= MAX_PROJECT_OBJECTS:
            raise ValueError(f"object limit is {MAX_PROJECT_OBJECTS}")
        polygon = _normalize_polygon_winding(polygon)
        if not _validate_polygon(polygon):
            # Repair is strictly opt-in. Invalid coordinates must never enter
            # the repair heuristic when auto-repair is disabled.
            if self.auto_repair:
                repaired, repaired_flag = _attempt_repair(polygon)
                if repaired_flag and _validate_polygon(repaired):
                    logger.warning(f"Auto-repaired polygon for object {oid}")
                    polygon = repaired
                else:
                    logger.warning(
                        f"Invalid polygon for object {oid}; auto_repair=enabled"
                    )
                    raise ValueError("Invalid polygon")
            else:
                logger.warning(
                    f"Invalid polygon for object {oid}; auto_repair=disabled"
                )
                raise ValueError("Invalid polygon")
        if oid in self.objects:
            logger.warning(f"Object id {oid} already exists, skipping")
            raise ValueError("Object id exists")
        if layer_id is None:
            layer_id = "layer_default"
        self.objects[oid] = SceneObject(oid, polygon, layer_id)
        if select:
            self.selected_id = oid
            self.selected_ids = [oid]
        self._notify()

    @staticmethod
    def prepare_bezier_geometry(
        beziers,
        *,
        steps_per_segment: int = 20,
    ) -> Tuple[BezierSegments, List[Tuple[int, int]]]:
        """Return canonical controls and one valid counter-clockwise polygon."""

        try:
            canonical = canonicalize_beziers(beziers)
            polygon = sample_beziers_to_polygon(
                canonical,
                steps_per_segment=steps_per_segment,
            )
        except OverflowError as exc:
            raise ValueError(
                "Bézier coordinates must be finite and representable."
            ) from exc
        polygon = _normalize_polygon_winding(polygon)
        if not _validate_polygon(polygon):
            raise ValueError("Invalid sampled Bézier polygon")
        return canonical, polygon

    def add_bezier_object(
        self,
        beziers,
        layer_id: Optional[str] = None,
        object_id: Optional[str] = None,
        *,
        select: bool = False,
        steps_per_segment: int = 20,
    ) -> str:
        """Insert one complete Bézier object and notify only its final state."""

        canonical, polygon = self.prepare_bezier_geometry(
            beziers,
            steps_per_segment=steps_per_segment,
        )

        oid = str(object_id) if object_id is not None else str(uuid.uuid4())
        if oid not in self.objects and len(self.objects) >= MAX_PROJECT_OBJECTS:
            raise ValueError(f"object limit is {MAX_PROJECT_OBJECTS}")
        if oid in self.objects:
            logger.warning(f"Object id {oid} already exists, skipping")
            raise ValueError("Object id exists")

        target_layer_id = layer_id or "layer_default"
        obj = SceneObject(oid, polygon, target_layer_id)
        obj.beziers = canonical
        self.objects[oid] = obj
        if select:
            self.selected_id = oid
            self.selected_ids = [oid]
        self._notify()
        return oid

    def set_auto_repair(self, enabled: bool):
        """Enable or disable automatic polygon repair.

        By default the Scene will raise when a polygon is invalid. Enabling
        auto_repair makes `add_object` try the repair heuristics and accept
        the repaired polygon when possible.
        """
        self.auto_repair = bool(enabled)

    def add_polygon(
        self, polygon: List[Tuple[int, int]], layer_id: Optional[str] = None
    ):
        started_at = time.perf_counter()
        oid = str(uuid.uuid4())
        try:
            self.add_object(oid, polygon, layer_id, select=True)
            selected = self.selected_id == oid
            record_validation_event(
                "polygon.created",
                "SUCCESS" if selected else "FAILURE",
                duration_ms=elapsed_ms(started_at),
                object_token=object_token(oid),
                vertex_count=len(polygon),
                selected=selected,
                object_count=len(self.objects),
            )
            return oid
        except Exception as exc:
            record_validation_exception(
                "polygon.created",
                exc,
                duration_ms=elapsed_ms(started_at),
                vertex_count=len(polygon),
            )
            raise

    def remove_object(self, oid: str):
        if oid not in self.objects:
            logger.warning(f"Object {oid} not found for removal")
            raise KeyError(oid)

        # Remove colisão associada se existir
        if oid in self.collision_shapes:
            del self.collision_shapes[oid]
        self.collision_parts.pop(oid, None)

        self.objects.pop(oid)
        self.selected_ids = [item for item in self.selected_ids if item != oid]
        if self.selected_id == oid:
            self.selected_id = self.selected_ids[0] if self.selected_ids else None
        # Remove de grupos
        for g in self.groups:
            if oid in g.members:
                g.members.remove(oid)

        logger.debug(f"Removed object {oid}")
        self._notify()

    def rename_object(self, old_id: str, new_id: str):
        # Rename an object while preserving all persistent references.
        old_id = str(old_id)
        new_id = str(new_id).strip()
        if not new_id:
            raise ValueError("new object id must not be empty")
        if old_id not in self.objects:
            raise KeyError(old_id)
        if new_id == old_id:
            return
        if new_id in self.objects:
            raise ValueError("Object id exists")

        renamed_objects: Dict[str, SceneObject] = {}
        for object_id, obj in self.objects.items():
            if object_id == old_id:
                obj.id = new_id
                renamed_objects[new_id] = obj
            else:
                renamed_objects[object_id] = obj
        self.objects = renamed_objects

        if old_id in self.collision_shapes:
            renamed_collisions = {}
            for object_id, shape in self.collision_shapes.items():
                key = new_id if object_id == old_id else object_id
                renamed_collisions[key] = shape
            self.collision_shapes = renamed_collisions

        if old_id in self.collision_parts:
            renamed_parts = {}
            for object_id, parts in self.collision_parts.items():
                key = new_id if object_id == old_id else object_id
                renamed_parts[key] = parts
            self.collision_parts = renamed_parts

        for group in self.groups:
            group.members = [
                new_id if member == old_id else member for member in group.members
            ]

        if old_id in self.selected_ids:
            self.selected_ids = [
                new_id if item == old_id else item for item in self.selected_ids
            ]
        if self.selected_id == old_id:
            self.selected_id = new_id
        self._notify()

    def update_polygon(self, oid: str, polygon: List[Tuple[int, int]]):
        if oid not in self.objects:
            logger.warning(f"Object {oid} not found for update")
            raise KeyError(oid)
        polygon = _normalize_polygon_winding(polygon)
        if not _validate_polygon(polygon):
            raise ValueError("Invalid polygon")
        self.objects[oid].polygon = polygon

        # Se tiver colisão, atualiza também
        if oid in self.collision_shapes:
            self.collision_shapes[oid] = [(float(p[0]), float(p[1])) for p in polygon]
            self.collision_parts.pop(oid, None)

        self.objects[oid].sync_position_from_polygon()

        logger.debug(f"Updated polygon for object {oid} with {len(polygon)} vertices")
        self._notify()

    def select_object(self, oid: Optional[str]):
        if oid is None:
            self.selected_id = None
            self.selected_ids = []
        else:
            if oid not in self.objects:
                raise KeyError(oid)
            self.selected_id = oid
            self.selected_ids = [oid]
        self._notify()

    def select_objects(self, object_ids: List[str], primary: Optional[str] = None):
        """Select existing objects deterministically, preserving one primary."""

        unique = list(dict.fromkeys(object_ids))
        missing = [oid for oid in unique if oid not in self.objects]
        if missing:
            raise KeyError(missing[0])
        if primary is not None and primary not in unique:
            raise KeyError(primary)
        self.selected_ids = unique
        self.selected_id = (
            primary if primary is not None else (unique[0] if unique else None)
        )
        self._notify()

    def clear(self):
        """Limpa todos os objetos, grupos e colisões da cena."""
        self.objects.clear()
        self.groups.clear()
        self.collision_shapes.clear()
        self.collision_parts.clear()
        self.selected_id = None
        self.selected_ids = []
        self._notify()

    # --- Rendering Helpers ---
    def render_list(self):
        ordered = []
        for layer in self.layers:
            if not layer.visible:
                continue
            for obj in self.objects.values():
                if obj.layer_id == layer.id:
                    ordered.append(obj)
        return ordered

    def is_layer_locked_for_object(self, oid: str) -> bool:
        obj = self.objects.get(oid)
        if not obj:
            return False
        lid = obj.layer_id or "layer_default"
        for layer in self.layers:
            if layer.id == lid:
                return layer.locked
        return False

    # --- Groups ---
    def create_group(self, name="Group"):
        if len(self.groups) >= MAX_PROJECT_GROUPS:
            raise ValueError(f"group limit is {MAX_PROJECT_GROUPS}")
        g = Group(name=name)
        self.groups.append(g)
        self._notify()
        return g

    def remove_group(self, group_id):
        self.groups = [g for g in self.groups if g.id != group_id]
        self._notify()

    def add_object_to_group(self, group_id, object_id):
        if object_id not in self.objects:
            raise KeyError("object not found")
        g = next((x for x in self.groups if x.id == group_id), None)
        if not g:
            raise KeyError("group not found")
        if object_id not in g.members:
            if len(g.members) >= MAX_GROUP_MEMBERS:
                raise ValueError(f"group member limit is {MAX_GROUP_MEMBERS}")
            g.members.append(object_id)
        self._notify()

    def remove_object_from_group(self, group_id, object_id):
        g = next((x for x in self.groups if x.id == group_id), None)
        if not g:
            raise KeyError("group not found")
        if object_id in g.members:
            g.members.remove(object_id)
        self._notify()

    def move_group(self, group_id, new_index):
        ids = [g.id for g in self.groups]
        if group_id not in ids:
            raise KeyError("group not found")
        cur = ids.index(group_id)
        g = self.groups.pop(cur)
        new_index = max(0, min(new_index, len(self.groups)))
        self.groups.insert(new_index, g)
        self._notify()

    def set_group_visibility(self, group_id, visible):
        g = next((x for x in self.groups if x.id == group_id), None)
        if not g:
            raise KeyError("group not found")
        g.visible = bool(visible)
        self._notify()

    def set_group_lock(self, group_id, locked):
        g = next((x for x in self.groups if x.id == group_id), None)
        if not g:
            raise KeyError("group not found")
        g.locked = bool(locked)
        self._notify()

    # --- Image Handling ---
    def load_image(self, img, path):
        """Attach image data without replacing the existing scene document."""

        self.image = img
        self.image_path = path
        self.image_path_kind = None
        self.image_sha256 = None
        self._image_reference_loaded = False
        self._notify()

    def replace_with_image(self, img, path):
        """Start a new document from an image without retaining old scene data."""

        self.image = img
        self.image_path = path
        self.image_path_kind = None
        self.image_sha256 = None
        self._image_reference_loaded = False
        self.objects = {}
        self.layers = [
            Layer(
                id="layer_default",
                name="Default",
                visible=True,
                locked=False,
            )
        ]
        self.groups = []
        self.collision_shapes = {}
        self.collision_parts = {}
        self.selected_id = None
        self.selected_ids = []
        self._notify()

    def attach_project_image(self, img):
        """Attach decoded pixels while preserving the saved image reference."""

        self.image = img
        self._notify()

    def get_image(self):
        return self.image

    # --- Persistence ---
    def save_project(self, path: str) -> None:
        """Validate and atomically save the complete persistent scene state."""

        try:
            from src.persistence.project_io import save_scene_project

            save_scene_project(self, path)
        except Exception as exc:
            logger.error(f"Failed to save project {path}: {exc}")
            raise

    def load_project(self, path: str) -> tuple[str, ...]:
        """Load a validated project without leaving partial scene state."""

        try:
            from src.persistence.project_io import load_project_into_scene

            warnings = load_project_into_scene(self, path)
            for warning in warnings:
                logger.warning("Project migration warning: %s", warning)
            return warnings
        except Exception as exc:
            logger.error(f"Failed to load project {path}: {exc}")
            raise

    # --- Bezier ---
    def set_object_beziers(self, oid, beziers, *, steps_per_segment=20):
        obj = self.objects.get(oid)
        if not obj:
            raise KeyError("object not found")
        canonical, polygon = self.prepare_bezier_geometry(
            beziers,
            steps_per_segment=steps_per_segment,
        )
        obj.beziers = canonical
        obj.polygon = polygon
        self._notify()

    def sample_beziers_to_polygon(self, beziers, steps_per_segment=20):
        """Return the normalized polygon accepted by the scene invariant."""

        return self.prepare_bezier_geometry(
            beziers,
            steps_per_segment=steps_per_segment,
        )[1]
