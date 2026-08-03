"""Position, scale, rotation and opacity applied to any scene object."""

from __future__ import annotations

from dataclasses import dataclass, field

from .types import Vec2, Vec2Like


@dataclass
class Transform:
    """How an object is placed and oriented in scene space.

    Position is the object's center in centered y-up pixels. Scale multiplies
    the object's own size, and rotation is counter-clockwise degrees.
    """

    position: Vec2 = field(default_factory=Vec2)
    scale: Vec2 = field(default_factory=lambda: Vec2(1.0, 1.0))
    rotation: float = 0.0
    opacity: float = 1.0
    anchor: Vec2 = field(default_factory=Vec2)
    """Offset of the rotation/scale pivot from the object's center."""

    def __post_init__(self) -> None:
        self.position = Vec2.of(self.position)
        self.anchor = Vec2.of(self.anchor)
        self.scale = self._coerce_scale(self.scale)

    @staticmethod
    def _coerce_scale(value: Vec2Like | float) -> Vec2:
        """Accept a single number as a uniform scale."""
        if isinstance(value, (int, float)):
            return Vec2(float(value), float(value))
        return Vec2.of(value)

    @property
    def uniform_scale(self) -> float:
        """Average of the x and y scale, for radius-style sizing."""
        return (self.scale.x + self.scale.y) / 2.0

    def translated(self, offset: Vec2Like) -> Transform:
        """Return a copy moved by ``offset``."""
        return self.replace(position=self.position + offset)

    def scaled(self, factor: Vec2Like | float) -> Transform:
        """Return a copy with its scale multiplied by ``factor``."""
        f = self._coerce_scale(factor)
        return self.replace(scale=Vec2(self.scale.x * f.x, self.scale.y * f.y))

    def rotated(self, degrees: float) -> Transform:
        """Return a copy rotated by an additional ``degrees``."""
        return self.replace(rotation=self.rotation + degrees)

    def replace(self, **changes) -> Transform:
        """Return a copy with the given fields replaced."""
        data = {
            "position": self.position,
            "scale": self.scale,
            "rotation": self.rotation,
            "opacity": self.opacity,
            "anchor": self.anchor,
        }
        data.update(changes)
        return Transform(**data)

    def apply(self, point: Vec2Like) -> Vec2:
        """Map a point from the object's local space into scene space."""
        p = Vec2.of(point) - self.anchor
        p = Vec2(p.x * self.scale.x, p.y * self.scale.y)
        if self.rotation:
            p = p.rotated(self.rotation)
        return p + self.anchor + self.position

    def lerp(self, other: Transform, t: float) -> Transform:
        """Blend toward another transform by ``t`` in 0-1."""
        return Transform(
            position=self.position.lerp(other.position, t),
            scale=self.scale.lerp(other.scale, t),
            rotation=self.rotation + (other.rotation - self.rotation) * t,
            opacity=self.opacity + (other.opacity - self.opacity) * t,
            anchor=self.anchor.lerp(other.anchor, t),
        )
