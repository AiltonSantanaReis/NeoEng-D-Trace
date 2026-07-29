"""Implementation of :mod:`src.utils.packing`.

Implementation preserved in the single ``src`` source tree.
"""

from typing import List, Optional, Any


class Rect:
    """Represents a rectangle in the packing area."""

    def __init__(
        self, x: int, y: int, w: int, h: int, id: Optional[Any] = None
    ) -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.id = id

    def __repr__(self) -> str:
        return f"Rect(id={self.id}, x={self.x}, y={self.y}, w={self.w}, h={self.h})"


class Packer:
    """
    Simple 2D bin packer for texture atlases.
    Uses a heuristic to split free space into new rectangles after placement.
    """

    def __init__(self, w: int, h: int, padding: int = 2) -> None:
        self.w = w
        self.h = h
        self.padding = padding
        # Initial free space is the entire area
        self.free: List[Rect] = [Rect(0, 0, w, h)]
        self.used: List[Rect] = []

    def insert(
        self, wid: int, hei: int, id: Optional[Any] = None
    ) -> Optional[Rect]:
        """
        Try to insert a rectangle of size (wid, hei).
        Returns the placed Rect or None if no space.
        """
        # Find the first free rect that fits
        for i, fr in enumerate(self.free):
            # Check if fits considering padding
            if wid + self.padding <= fr.w and hei + self.padding <= fr.h:
                # Place the new rect at the top-left of the free space
                node = Rect(fr.x, fr.y, wid, hei, id)
                self.used.append(node)

                # Remove the current free rect as we are splitting it
                self.free.pop(i)

                # Split the remaining space into two new free rectangles
                # 1. Right side (remaining width, same height as placed obj)
                # Note: This strategy helps creating "rows"
                if fr.w - wid - self.padding > 0:
                    self.free.append(
                        Rect(
                            fr.x + wid + self.padding,
                            fr.y,
                            fr.w - wid - self.padding,
                            hei + self.padding, # Extend padding to match row height logic
                        )
                    )

                # 2. Bottom side (full original width, remaining height)
                if fr.h - hei - self.padding > 0:
                    self.free.append(
                        Rect(
                            fr.x,
                            fr.y + hei + self.padding,
                            fr.w,
                            fr.h - hei - self.padding,
                        )
                    )

                return node
        
        return None
