"""Uniform spatial hash for broad-phase collision culling.

Keeps object-to-object collision usable at high counts by only testing pairs
that share a grid cell, instead of every pair in the scene.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator, Sequence
from typing import TypeVar

T = TypeVar("T")


class SpatialGrid:
    """Buckets objects into fixed-size cells keyed by integer coordinates."""

    def __init__(self, cell_size: float = 100.0) -> None:
        self.cell_size = max(1.0, cell_size)
        self._cells: dict[tuple[int, int], list[int]] = defaultdict(list)

    def clear(self) -> None:
        """Drop every bucketed object."""
        self._cells.clear()

    def _cells_for(self, x: float, y: float, radius: float) -> Iterator[tuple[int, int]]:
        """Yield every cell coordinate a circle overlaps."""
        size = self.cell_size
        min_x, max_x = int((x - radius) // size), int((x + radius) // size)
        min_y, max_y = int((y - radius) // size), int((y + radius) // size)
        for cx in range(min_x, max_x + 1):
            for cy in range(min_y, max_y + 1):
                yield cx, cy

    def insert(self, index: int, x: float, y: float, radius: float) -> None:
        """Add an object's index to every cell its circle overlaps."""
        for cell in self._cells_for(x, y, radius):
            self._cells[cell].append(index)

    def build(self, bodies: Sequence) -> None:
        """Rebuild the grid from a sequence of objects with position and radius."""
        self.clear()
        for i, body in enumerate(bodies):
            pos = body.transform.position
            self.insert(i, pos.x, pos.y, body.collision_radius)

    def candidate_pairs(self) -> set[tuple[int, int]]:
        """Every unique index pair sharing at least one cell."""
        pairs: set[tuple[int, int]] = set()
        for bucket in self._cells.values():
            count = len(bucket)
            if count < 2:
                continue
            for i in range(count):
                for j in range(i + 1, count):
                    a, b = bucket[i], bucket[j]
                    pairs.add((a, b) if a < b else (b, a))
        return pairs
