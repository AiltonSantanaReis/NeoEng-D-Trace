"""Implementation of :mod:`src.physics.sat2d`.

Implementation preserved in the single ``src`` source tree.
"""

import numpy as np
from typing import Tuple, List, Optional


def project(
    polygon: List[Tuple[float, float]],
    axis: Tuple[float, float],
) -> Tuple[float, float]:
    """Compatibility wrapper for the historical public SAT API."""
    if not polygon:
        return 0.0, 0.0

    axis_array = np.asarray(axis, dtype=float)
    norm = float(np.linalg.norm(axis_array))
    if norm == 0.0:
        return 0.0, 0.0

    vertices = np.asarray(polygon, dtype=float)
    return project_polygon(axis_array / norm, vertices)


def polygon_edges(
    polygon: List[Tuple[float, float]],
) -> List[Tuple[float, float]]:
    """Return each polygon edge as a ``(dx, dy)`` vector."""
    if not polygon:
        return []

    edges: List[Tuple[float, float]] = []
    for index, first in enumerate(polygon):
        second = polygon[(index + 1) % len(polygon)]
        edges.append(
            (float(second[0] - first[0]), float(second[1] - first[1]))
        )
    return edges


def project_polygon(
    axis: np.ndarray, verts: np.ndarray
) -> Tuple[float, float]:
    """
    Projeta um polígono 2D em um eixo e retorna o intervalo escalar [min, max].

    axis:
        Vetor 2D normalizado (shape (2,)).
    verts:
        Array de vértices Nx2.
    """
    dots = verts.dot(axis)
    return float(np.min(dots)), float(np.max(dots))


def overlap_intervals(
    a_min: float, a_max: float, b_min: float, b_max: float
) -> float:
    """
    Retorna a sobreposição entre [a_min, a_max] e [b_min, b_max].
    Valor > 0 indica interseção; 0 ou negativo -> sem interseção.
    """
    return min(a_max, b_max) - max(a_min, b_min)


def sat_polygon_vs_polygon(
    poly1: List[Tuple[float, float]],
    poly2: List[Tuple[float, float]],
    epsilon: float = 1e-7,
) -> Tuple[bool, Optional[Tuple[float, float]]]:
    """
    Verifica colisão entre dois polígonos convexos em 2D usando SAT.

    poly1, poly2:
        Listas de (x, y) vértices em ordem (clockwise/ccw).
    epsilon:
        Tolerância numérica para considerar sobreposição == 0 como contato.
    Retorna:
        (collides, mtv) onde:
            collides: True se há sobreposição (ou contato,
            dependendo de epsilon).
            mtv: vetor mínimo de translação (x, y) para mover poly1
            para fora de poly2,
                 ou None se não há colisão.
    """
    verts_a = np.array(poly1, dtype=float)
    verts_b = np.array(poly2, dtype=float)

    if verts_a.shape[0] < 3 or verts_b.shape[0] < 3:
        # Historical callers treat incomplete geometry as non-colliding.
        # Valid polygons retain the same SAT/MTV behavior.
        return False, None

    axes = []
    for verts in (verts_a, verts_b):
        for i in range(len(verts)):
            p1 = verts[i]
            p2 = verts[(i + 1) % len(verts)]
            edge = p2 - p1
            axis = np.array([-edge[1], edge[0]], dtype=float)
            norm = np.linalg.norm(axis)
            if norm == 0.0:
                continue
            axis /= norm
            axes.append(axis)

    if not axes:
        # Em teoria não deveria acontecer se há >=3 vértices válidos.
        return False, None

    mtv_depth = float("inf")
    mtv_axis = None

    for axis in axes:
        a_min, a_max = project_polygon(axis, verts_a)
        b_min, b_max = project_polygon(axis, verts_b)
        o = overlap_intervals(a_min, a_max, b_min, b_max)

        # usa epsilon para tolerar erro numérico e contato
        if o < -epsilon:
            return False, None

        if o < mtv_depth:
            mtv_depth = o
            mtv_axis = axis

    if mtv_axis is None:
        return False, None

    center_a = np.mean(verts_a, axis=0)
    center_b = np.mean(verts_b, axis=0)
    direction = center_b - center_a
    if np.dot(direction, mtv_axis) < 0.0:
        mtv_axis = -mtv_axis

    mtv = mtv_axis * mtv_depth
    return True, (float(mtv[0]), float(mtv[1]))
