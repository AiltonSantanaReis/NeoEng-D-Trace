"""Implementation of :mod:`src.collision.sat2d`.

Implementation preserved in the single ``src`` source tree.
"""

# Unified SAT implementation backed by src.physics.sat2d.
# This module provides numpy-based interface for compatibility

from ..physics.sat2d import sat_polygon_vs_polygon
import numpy as np
from typing import Tuple, Optional

Array2D = np.ndarray  # Nx2


def polygon_collision_sat(
    verts_a: Array2D,
    verts_b: Array2D,
    epsilon: float = 1e-7,
) -> Tuple[bool, Optional[np.ndarray]]:
    """
    Verifica colisão entre dois polígonos convexos em 2D usando SAT.
    Wrapper para sat_polygon_vs_polygon com interface numpy.

    verts_a, verts_b:
        Arrays Nx2 de floats, vértices em ordem (clockwise/ccw).
    epsilon:
        Tolerância numérica para considerar sobreposição == 0 como contato.
    Retorna:
        (collides, mtv) onde:
            collides: True se há sobreposição (ou contato,
            dependendo de epsilon).
            mtv: MTV (2,) para mover A para fora de B,
                 ou None se não há colisão.
    """
    # Convert numpy to list of tuples
    poly1 = [(float(x), float(y)) for x, y in verts_a]
    poly2 = [(float(x), float(y)) for x, y in verts_b]

    collides, mtv_tuple = sat_polygon_vs_polygon(poly1, poly2, epsilon)

    if mtv_tuple is None:
        return collides, None
    else:
        return collides, np.array(mtv_tuple, dtype=float)
