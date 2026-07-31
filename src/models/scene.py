"""Implementation of :mod:`src.models.scene`.

Implementation preserved in the single ``src`` source tree.
"""

import time
import uuid
from typing import Callable, Dict, List, Optional, Tuple

from src.core.logger import logger
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


def _normalize_polygon_winding(points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Ensure the polygon is in counter-clockwise order."""
    if len(points) < 3:
        return points
    # Calculate signed area
    area = 0.0
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    # If area is negative, it's clockwise, so reverse
    if area < 0:
        return list(reversed(points))
    return points


def _validate_polygon(points: List[Tuple[int, int]]) -> bool:
    if not isinstance(points, list) or len(points) < 3:
        return False
    for p in points:
        if not isinstance(p, (list, tuple)) or len(p) != 2:
            return False
        x, y = p
        if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
            return False

    if HAS_SHAPELY:
        try:
            poly = Polygon(points)
            if not poly.is_valid:
                return False
            # Check for self-intersections
            if not poly.is_simple:
                return False
            # Ensure counter-clockwise
            if not poly.exterior.is_ccw:
                return False
        except Exception:
            return False
    else:
        # Fallback to basic checks
        # Check winding (counter-clockwise)
        area = 0.0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        if area <= 0:
            return False

        # Check for self-intersections (basic)
        if _has_self_intersections(points):
            return False

    return True


def _has_self_intersections(points: List[Tuple[int, int]]) -> bool:
    """Check if the polygon has self-intersecting edges."""
    n = len(points)
    for i in range(n):
        for j in range(i + 2, n):  # Skip adjacent edges
            if i == 0 and j == n - 1:
                continue  # Skip the closing edge if adjacent
            if _lines_intersect(
                points[i], points[(i + 1) % n], points[j], points[(j + 1) % n]
            ):
                return True
    return False


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

    # Work in floats for intermediate math
    ptsf: List[Tuple[float, float]] = [(float(x), float(y)) for x, y in points]
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


def _lines_intersect(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    p4: Tuple[float, float],
) -> bool:
    """Check if line segments p1-p2 and p3-p4 intersect."""

    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)


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
        self.beziers = None


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
        # Physics collision shapes
        self.collision_shapes: Dict[str, List[Tuple[float, float]]] = {}
        self.selected_id: Optional[str] = None
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

    # --- Physics System (INTEGRAÇÃO DE COLISÃO) ---
    def set_object_collision(self, oid: str, enabled: bool):
        """Ativa/Desativa física para um objeto."""
        if oid not in self.objects:
            return

        if enabled:
            obj = self.objects[oid]
            # Converte para float para o motor de física
            self.collision_shapes[oid] = [
                (float(p[0]), float(p[1])) for p in obj.polygon
            ]
        else:
            if oid in self.collision_shapes:
                del self.collision_shapes[oid]
        self._notify()

    def has_collision(self, oid: str) -> bool:
        """Retorna True se o objeto tem colisão ativa."""
        return oid in self.collision_shapes

    # --- Layers Methods ---
    def create_layer(self, name: str = "Layer") -> Layer:
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
        polygon = _normalize_polygon_winding(polygon)
        if not _validate_polygon(polygon):
            # Do not silently hide errors: attempt repair only when explicitly enabled
            repaired, repaired_flag = _attempt_repair(polygon)
            if repaired_flag and _validate_polygon(repaired) and self.auto_repair:
                logger.warning(f"Auto-repaired polygon for object {oid}")
                polygon = repaired
            else:
                # Provide detailed logging for debugging, but raise the error so callers must handle it.
                logger.warning(
                    f"Invalid polygon for object {oid}; auto_repair={'enabled' if self.auto_repair else 'disabled'}"
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
        self._notify()

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

        self.objects.pop(oid)
        if self.selected_id == oid:
            self.selected_id = None

        # Remove de grupos
        for g in self.groups:
            if oid in g.members:
                g.members.remove(oid)

        logger.debug(f"Removed object {oid}")
        self._notify()

    def update_polygon(self, oid: str, polygon: List[Tuple[int, int]]):
        if oid not in self.objects:
            logger.warning(f"Object {oid} not found for update")
            raise KeyError(oid)
        polygon = _normalize_polygon_winding(polygon)
        self.objects[oid].polygon = polygon

        # Se tiver colisão, atualiza também
        if oid in self.collision_shapes:
            self.collision_shapes[oid] = [(float(p[0]), float(p[1])) for p in polygon]

        logger.debug(f"Updated polygon for object {oid} with {len(polygon)} vertices")
        self._notify()

    def select_object(self, oid: Optional[str]):
        self.selected_id = oid
        self._notify()

    def clear(self):
        """Limpa todos os objetos, grupos e colisões da cena."""
        self.objects.clear()
        self.groups.clear()
        self.collision_shapes.clear()
        self.selected_id = None
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
        self.image = img
        self.image_path = path
        self.image_path_kind = None
        self.image_sha256 = None
        self._image_reference_loaded = False
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
    def set_object_beziers(self, oid, beziers):
        obj = self.objects.get(oid)
        if not obj:
            raise KeyError("object not found")
        obj.beziers = beziers
        obj.polygon = self.sample_beziers_to_polygon(beziers)
        self._notify()

    def sample_beziers_to_polygon(self, beziers, steps_per_segment=20):
        # Placeholder simples para evitar erro se beziers forem usados
        pts = []
        for seg in beziers:
            pts.append((int(seg[0][0]), int(seg[0][1])))
        return pts
