"""Implementation of :mod:`src.physics.convex_decomp`.

Implementation preserved in the single ``src`` source tree.
"""

import math
from typing import List, Optional, Sequence, Tuple

import numpy as np

try:
    import mapbox_earcut as earcut

    HAS_EARCUT = True
except ImportError:
    HAS_EARCUT = False


Point = Tuple[float, float]
Polygon = List[Point]
_GEOMETRY_EPSILON = 1e-10


def _cross(first: Point, second: Point, third: Point) -> float:
    return (second[0] - first[0]) * (third[1] - first[1]) - (second[1] - first[1]) * (
        third[0] - first[0]
    )


def _signed_area2(polygon: Sequence[Point]) -> float:
    return sum(
        polygon[index][0] * polygon[(index + 1) % len(polygon)][1]
        - polygon[(index + 1) % len(polygon)][0] * polygon[index][1]
        for index in range(len(polygon))
    )


def _canonical_polygon(polygon: Sequence[Sequence[float]]) -> Polygon:
    points: Polygon = []
    for index, point in enumerate(polygon):
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError(f"Polygon point {index} must contain two coordinates")
        x, y = point
        if (
            isinstance(x, bool)
            or isinstance(y, bool)
            or not isinstance(x, (int, float))
            or not isinstance(y, (int, float))
        ):
            raise ValueError(f"Polygon point {index} must be numeric")
        try:
            canonical = (float(x), float(y))
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Polygon point {index} must be finite and representable"
            ) from exc
        if not math.isfinite(canonical[0]) or not math.isfinite(canonical[1]):
            raise ValueError(f"Polygon point {index} must be finite")
        points.append(canonical)

    if len(points) > 1 and points[0] == points[-1]:
        points.pop()
    if len(points) < 3:
        return points
    if len(set(points)) != len(points):
        raise ValueError("Polygon must not contain repeated vertices")

    area2 = _signed_area2(points)
    if not math.isfinite(area2) or abs(area2) <= _GEOMETRY_EPSILON:
        raise ValueError("Polygon must have finite non-zero area")
    if area2 < 0.0:
        points.reverse()
    return points


def _validated_triangulation(
    polygon: Polygon, triangles: List[Polygon]
) -> List[Polygon]:
    expected_area = polygon_area(polygon)
    triangle_area = sum(polygon_area(triangle) for triangle in triangles)
    tolerance = max(_GEOMETRY_EPSILON, expected_area * 1e-9)
    if (
        len(triangles) != len(polygon) - 2
        or any(polygon_area(triangle) <= _GEOMETRY_EPSILON for triangle in triangles)
        or not math.isclose(
            triangle_area,
            expected_area,
            rel_tol=0.0,
            abs_tol=tolerance,
        )
    ):
        raise ValueError("Triangulation did not preserve polygon geometry")
    return triangles


def polygon_area(polygon: List[Tuple[float, float]]) -> float:
    """
    Calculate the area of a polygon using the shoelace formula.

    Args:
        polygon: List of (x, y) vertex coordinates in counter-clockwise order

    Returns:
        Area of the polygon (positive for counter-clockwise,
        negative for clockwise)
    """
    if len(polygon) < 3:
        return 0.0

    area = 0.0
    n = len(polygon)

    for i in range(n):
        j = (i + 1) % n
        area += polygon[i][0] * polygon[j][1]
        area -= polygon[j][0] * polygon[i][1]

    return abs(area) / 2.0


def is_point_in_triangle(
    point: Tuple[float, float], triangle: List[Tuple[float, float]]
) -> bool:
    """
    Check if a point is inside a triangle using cross
    product method.
    This approach checks if the point is on the same side of
    all triangle edges.

    Note: This implementation was rewritten using cross product
    method to ensure
    originality and avoid
    any
    licensing
    concerns
    with
    other implementations.

    Args:
        point: (x, y) coordinates of the point to test
        triangle: List of 3 (x, y) vertices of the triangle

    Returns:
        True if point is inside the triangle (including boundary)
    """
    if len(triangle) != 3:
        return False

    a, b, c = triangle

    # Check if point is on the same side of all edges
    # For a triangle ABC and point P, P should be on the same side of AB as C,
    # on the same side of BC as A, and on the same side of CA as B

    # Check against edge AB (from a to b), reference point is c
    cross_ab = _cross(a, b, c)
    if abs(cross_ab) <= _GEOMETRY_EPSILON:
        return False
    cross_ap = _cross(a, b, point)

    # Check against edge BC (from b to c), reference point is a
    cross_bc = _cross(b, c, a)
    cross_bp = _cross(b, c, point)

    # Check against edge CA (from c to a),
    # reference point is b
    cross_ca = _cross(c, a, b)
    cross_cp = _cross(c, a, point)

    # For point to be inside triangle, all cross products must have
    # the same sign as reference
    # We use a small epsilon for boundary cases
    eps = _GEOMETRY_EPSILON

    same_side_ab = cross_ab * cross_ap >= -eps
    same_side_bc = cross_bc * cross_bp >= -eps
    same_side_ca = cross_ca * cross_cp >= -eps

    return same_side_ab and same_side_bc and same_side_ca


def triangulate_to_convex(
    pol: List[Tuple[float, float]],
) -> List[List[Tuple[float, float]]]:
    """Triangulate one finite polygon independently of the optional backend."""
    if len(pol) < 3:
        return []

    canonical = _canonical_polygon(pol)
    if len(canonical) < 3:
        raise ValueError("Polygon must have finite non-zero area")
    if HAS_EARCUT and len(canonical) > 3:
        triangulate = getattr(earcut, "triangulate_float64", None)
        if callable(triangulate):
            verts = np.array(canonical, dtype=np.float64)
        else:
            triangulate = earcut.triangulate_float32
            verts = np.array(canonical, dtype=np.float32)
        ring_ends = np.array([len(verts)], dtype=np.uint32)
        tris = triangulate(verts, ring_ends)
        if len(tris) % 3:
            raise ValueError("Triangulation backend returned malformed indices")
        if any(index < 0 or index >= len(canonical) for index in tris):
            raise ValueError("Triangulation backend returned out-of-range indices")
        result = []
        for index in range(0, len(tris), 3):
            first = canonical[tris[index]]
            second = canonical[tris[index + 1]]
            third = canonical[tris[index + 2]]
            result.append([first, second, third])
        return _validated_triangulation(canonical, result)
    return ear_clipping_triangulation(canonical)


def is_ear(polygon: List[Tuple[float, float]], vertex_index: int) -> bool:
    """
    Check if a vertex is an ear (the triangle formed by it and its neighbors
    doesn't contain any other polygon vertices).

    Args:
        polygon: List of (x, y) vertex coordinates
        vertex_index: Index of the vertex to check

    Returns:
        True if the vertex is an ear
    """
    n = len(polygon)
    if n < 3:
        return False

    # Get the three vertices of the potential ear triangle
    prev = (vertex_index - 1) % n
    curr = vertex_index
    next_v = (vertex_index + 1) % n

    triangle = [polygon[prev], polygon[curr], polygon[next_v]]
    if _cross(*triangle) <= _GEOMETRY_EPSILON:
        return False

    # Check if any other vertex is inside this triangle
    for i in range(n):
        if i == prev or i == curr or i == next_v:
            continue
        if is_point_in_triangle(polygon[i], triangle):
            return False

    return True


def ear_clipping_triangulation(
    polygon: List[Tuple[float, float]],
) -> List[List[Tuple[float, float]]]:
    """Triangulate a simple polygon through deterministic ear clipping."""
    if len(polygon) < 3:
        return []

    canonical = _canonical_polygon(polygon)
    verts = canonical.copy()
    triangles: List[Polygon] = []

    while len(verts) > 3:
        ear_found = False
        for index in range(len(verts)):
            if is_ear(verts, index):
                previous = (index - 1) % len(verts)
                next_index = (index + 1) % len(verts)
                triangles.append([verts[previous], verts[index], verts[next_index]])
                verts.pop(index)
                ear_found = True
                break

        if not ear_found:
            raise ValueError(
                "No ear found in polygon - may not be simple or may be degenerate"
            )

    if len(verts) == 3:
        triangles.append(verts.copy())

    return _validated_triangulation(canonical, triangles)


def is_convex_polygon(
    polygon: List[Tuple[float, float]], epsilon: float = 1e-10
) -> bool:
    """Return True only when a polygon has a consistent non-zero turn sign."""
    if len(polygon) < 3:
        return False

    turn_sign = 0
    for index in range(len(polygon)):
        a = polygon[index - 1]
        b = polygon[index]
        c = polygon[(index + 1) % len(polygon)]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cross) <= epsilon:
            continue
        current_sign = 1 if cross > 0 else -1
        if turn_sign == 0:
            turn_sign = current_sign
        elif current_sign != turn_sign:
            return False

    return turn_sign != 0


def merge_triangles_to_convex(
    triangles: List[List[Tuple[float, float]]],
) -> List[List[Tuple[float, float]]]:
    """
    Merge adjacent triangles into convex polygons where possible,
    limiting to <=8 vertices for Box2D compatibility.

    Args:
        triangles: List of triangles from
        triangulation

    Returns:
        List of convex polygons with <=8 vertices
    """
    if not triangles:
        return []

    # Start with triangles as initial polygons
    polygons = [list(t) for t in triangles]

    # Simple greedy merging: repeatedly merge pairs that share an edge
    # and result <=8 vertices
    merged = True
    while merged and len(polygons) > 1:
        merged = False
        i = 0
        while i < len(polygons):
            j = i + 1
            while j < len(polygons):
                merged_poly = try_merge_polygons(polygons[i], polygons[j])
                if merged_poly and len(merged_poly) <= 8:
                    polygons[i] = merged_poly
                    del polygons[j]
                    merged = True
                    break
                j += 1
            if merged:
                break
            i += 1

    return polygons


def try_merge_polygons(
    poly1: List[Tuple[float, float]], poly2: List[Tuple[float, float]]
) -> Optional[List[Tuple[float, float]]]:
    """
    Try to merge two convex polygons if they share an edge.
    Returns the merged polygon or None if not possible.
    """
    # Find shared edge
    shared_edge = None
    for a, b in zip(poly1, poly1[1:] + [poly1[0]]):
        for c, d in zip(poly2, poly2[1:] + [poly2[0]]):
            if (a == c and b == d) or (a == d and b == c):
                shared_edge = (a, b)
                break
        if shared_edge:
            break

    if not shared_edge:
        return None

    # Merge by removing shared edge and combining vertices
    # Start from one end of shared edge in poly1, go around, then poly2
    idx1 = poly1.index(shared_edge[0])
    idx2 = poly1.index(shared_edge[1])

    # Determine direction
    if (idx1 + 1) % len(poly1) == idx2:
        # poly1 goes from idx1 to idx2
        part1 = poly1[idx2:] + poly1[: idx1 + 1]
    else:
        # poly1 goes from idx2 to idx1
        part1 = poly1[idx1:] + poly1[: idx2 + 1]

    # For poly2, start from the other end of shared edge
    idx3 = poly2.index(shared_edge[1])
    idx4 = poly2.index(shared_edge[0])

    if (idx3 + 1) % len(poly2) == idx4:
        part2 = poly2[idx4:] + poly2[: idx3 + 1]
    else:
        part2 = poly2[idx3:] + poly2[: idx4 + 1]

    # Combine, removing duplicates at shared edge
    merged = part1[:-1] + part2[:-1]  # Remove last of each as they are shared

    # Remove duplicates
    unique = []
    for p in merged:
        if p not in unique:
            unique.append(p)

    if len(unique) < 3 or not is_convex_polygon(unique):
        return None

    return unique


def convex_decompose_polygon(
    polygon: List[Tuple[float, float]],
) -> List[List[Tuple[float, float]]]:
    """
    Decompose a simple polygon into convex polygons using triangulation
    followed by optional triangle merging.

    Args:
        polygon: List of (x, y) vertex coordinates in counter-clockwise order

    Returns:
        List of convex polygons
    """
    # First triangulate using earcut if available. Degenerate triangles can
    # appear when an input contour contains repeated or overlapping segments;
    # they are never valid collision pieces and must not escape this API.
    triangles = [
        triangle
        for triangle in triangulate_to_convex(polygon)
        if polygon_area(triangle) > 1e-10
    ]

    # Then try to merge triangles into larger convex polygons.
    convex_polygons = merge_triangles_to_convex(triangles)

    return convex_polygons
