"""Geometry value types.

Every public entry point accepts plain tuples where one of these is expected,
so ``Circle(pos=(0, 300))`` and ``Circle(pos=Vec2(0, 300))`` are equivalent.

Scene coordinates are centered and y-up: ``(0, 0)`` is the middle of the frame
and positive y points toward the top.
"""

from .resolution import PRESETS, Resolution
from .size import Size, SizeLike
from .vec2 import Vec2, Vec2Like

__all__ = ["PRESETS", "Resolution", "Size", "SizeLike", "Vec2", "Vec2Like"]
