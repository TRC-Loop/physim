"""2D vector in scene space."""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Union

Vec2Like = Union["Vec2", tuple[float, float], list[float]]


@dataclass(frozen=True, slots=True, eq=False)
class Vec2:
    """An immutable 2D vector in scene space, measured in pixels with y pointing up."""

    x: float = 0.0
    y: float = 0.0

    @classmethod
    def of(cls, value: Vec2Like) -> Vec2:
        """Coerce a tuple, list or ``Vec2`` into a ``Vec2``."""
        if isinstance(value, Vec2):
            return value
        x, y = value
        return cls(float(x), float(y))

    @classmethod
    def polar(cls, angle_deg: float, length: float = 1.0) -> Vec2:
        """Build a vector from an angle in degrees and a length."""
        rad = math.radians(angle_deg)
        return cls(math.cos(rad) * length, math.sin(rad) * length)

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y

    def __eq__(self, other: object) -> bool:
        """Compare equal to another vector or to any 2-item sequence."""
        if isinstance(other, Vec2):
            return self.x == other.x and self.y == other.y
        if isinstance(other, (tuple, list)) and len(other) == 2:
            return self.x == other[0] and self.y == other[1]
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __add__(self, other: Vec2Like) -> Vec2:
        o = Vec2.of(other)
        return Vec2(self.x + o.x, self.y + o.y)

    __radd__ = __add__

    def __sub__(self, other: Vec2Like) -> Vec2:
        o = Vec2.of(other)
        return Vec2(self.x - o.x, self.y - o.y)

    def __rsub__(self, other: Vec2Like) -> Vec2:
        return Vec2.of(other) - self

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> Vec2:
        return Vec2(self.x / scalar, self.y / scalar)

    def __neg__(self) -> Vec2:
        return Vec2(-self.x, -self.y)

    @property
    def length(self) -> float:
        """Euclidean length of the vector."""
        return math.hypot(self.x, self.y)

    @property
    def length_squared(self) -> float:
        """Squared length, for comparisons that don't need the square root."""
        return self.x * self.x + self.y * self.y

    @property
    def angle(self) -> float:
        """Direction in degrees, counter-clockwise from +x."""
        return math.degrees(math.atan2(self.y, self.x))

    def normalized(self) -> Vec2:
        """Return a unit vector with the same direction, or zero if length is zero."""
        length = self.length
        return Vec2(self.x / length, self.y / length) if length else Vec2()

    def dot(self, other: Vec2Like) -> float:
        """Dot product with another vector."""
        o = Vec2.of(other)
        return self.x * o.x + self.y * o.y

    def cross(self, other: Vec2Like) -> float:
        """Scalar cross product, positive when ``other`` is counter-clockwise."""
        o = Vec2.of(other)
        return self.x * o.y - self.y * o.x

    def rotated(self, degrees: float) -> Vec2:
        """Return this vector rotated counter-clockwise by an angle in degrees."""
        rad = math.radians(degrees)
        cos, sin = math.cos(rad), math.sin(rad)
        return Vec2(self.x * cos - self.y * sin, self.x * sin + self.y * cos)

    def perpendicular(self) -> Vec2:
        """Return the vector rotated 90 degrees counter-clockwise."""
        return Vec2(-self.y, self.x)

    def distance_to(self, other: Vec2Like) -> float:
        """Distance between this point and another."""
        return (self - other).length

    def reflected(self, normal: Vec2Like) -> Vec2:
        """Reflect this vector about a surface normal."""
        n = Vec2.of(normal).normalized()
        return self - n * (2.0 * self.dot(n))

    def clamped(self, max_length: float) -> Vec2:
        """Return this vector shortened to ``max_length`` if it is longer."""
        length = self.length
        if length <= max_length or length == 0.0:
            return self
        return self * (max_length / length)

    def lerp(self, other: Vec2Like, t: float) -> Vec2:
        """Linearly interpolate toward another vector."""
        return self + (Vec2.of(other) - self) * t
