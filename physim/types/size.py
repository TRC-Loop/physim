"""Width/height pair."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Union

SizeLike = Union["Size", tuple[float, float], list[float], float]


@dataclass(frozen=True, slots=True)
class Size:
    """A width and height in pixels."""

    width: float = 0.0
    height: float = 0.0

    @classmethod
    def of(cls, value: SizeLike) -> Size:
        """Coerce a tuple, list, ``Size`` or single number (square) into a ``Size``."""
        if isinstance(value, Size):
            return value
        if isinstance(value, (int, float)):
            return cls(float(value), float(value))
        w, h = value
        return cls(float(w), float(h))

    def __iter__(self) -> Iterator[float]:
        yield self.width
        yield self.height

    def __mul__(self, scalar: float) -> Size:
        return Size(self.width * scalar, self.height * scalar)

    __rmul__ = __mul__

    @property
    def aspect(self) -> float:
        """Width divided by height, or zero when height is zero."""
        return self.width / self.height if self.height else 0.0

    @property
    def half(self) -> Size:
        """Half extents, handy for centered rectangles."""
        return Size(self.width / 2.0, self.height / 2.0)
