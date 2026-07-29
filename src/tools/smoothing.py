# src/tools/smoothing.py
"""Smoothing utilities for polylines."""

from typing import List, Tuple

try:
    from src.core.logger import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

Point = Tuple[float, float]


def chaikin_smooth(points: List[Point], iterations: int = 2) -> List[Point]:
    """
    Applies Chaikin's corner cutting algorithm to smooth a polyline.
    """
    try:
        if len(points) < 2 or iterations <= 0:
            return points[:]
            
        pts = [(float(x), float(y)) for x, y in points]
        
        for _ in range(iterations):
            new_pts = []
            n = len(pts)
            # Note: This treats the line as open. For closed shapes, 
            # the caller should ensure start==end or handle wrapping.
            for i in range(n - 1):
                p0 = pts[i]
                p1 = pts[i + 1]
                
                # Q = 0.75*P0 + 0.25*P1
                q = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
                # R = 0.25*P0 + 0.75*P1
                r = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])
                
                new_pts.append(q)
                new_pts.append(r)
            
            # Keep the first and last points for open polylines
            new_pts.insert(0, pts[0])
            new_pts.append(pts[-1])
            
            pts = new_pts
            
        logger.debug(f"Chaikin smoothing applied, result: {len(pts)} points")
        return pts
    except Exception as e:
        logger.error(f"Error in chaikin_smooth: {e}")
        return points  # Return original on failure


def catmull_rom_to_beziers(
    points: List[Point], closed: bool = False
) -> List[Tuple[Point, Point, Point, Point]]:
    """
    Converts a sequence of points into Cubic Bezier segments using 
    Catmull-Rom spline tangents.
    """
    try:
        if len(points) < 2:
            return []
            
        pts = [(float(x), float(y)) for x, y in points]
        beziers = []
        n = len(pts)

        def get_pt(i):
            if closed:
                return pts[i % n]
            else:
                # Clamp to boundary
                if i < 0:
                    return pts[0]
                if i >= n:
                    return pts[-1]
                return pts[i]

        # Iterate through segments
        for i in range(n - (0 if closed else 1)):
            p0 = get_pt(i)      # Current Point
            p1 = get_pt(i + 1)  # Next Point
            
            p_minus = get_pt(i - 1) # Previous
            p_plus = get_pt(i + 2)  # Next Next

            # Calculate Control Points (C1, C2) derived from Catmull-Rom tangents
            # Tangent = (Next - Prev) / 2
            # Bezier Control = Point + Tangent / 3
            # Combined: C = P + (Next - Prev) / 6
            
            c1 = (
                p0[0] + (p1[0] - p_minus[0]) / 6.0,
                p0[1] + (p1[1] - p_minus[1]) / 6.0,
            )
            c2 = (
                p1[0] - (p_plus[0] - p0[0]) / 6.0,
                p1[1] - (p_plus[1] - p0[1]) / 6.0,
            )
            
            beziers.append((p0, c1, c2, p1))
            
        logger.debug(
            f"Catmull-Rom to Bezier conversion, {len(beziers)} segments"
        )
        return beziers
    except Exception as e:
        logger.error(f"Error in catmull_rom_to_beziers: {e}")
        return []