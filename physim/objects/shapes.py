"""Physics shapes that bounce around the playfield.

All of them collide as circles: it keeps hundreds of objects fast, and at the
sizes these animations use the difference is not visible.
"""

from __future__ import annotations

import math

from ..types import Vec2, Vec2Like
from .body import Body


class Circle(Body):
    """A filled circle, the default bouncing object."""

    def __init__(self, radius: float = 20.0, pos: Vec2Like = (0.0, 0.0), **kwargs) -> None:
        super().__init__(pos, **kwargs)
        self.radius = radius

    @property
    def collision_radius(self) -> float:
        """Radius scaled by the object's transform."""
        return self.radius * self.transform.uniform_scale

    def grow(self, amount: float) -> float:
        """Add to the radius and return the new value."""
        self.radius = max(0.0, self.radius + amount)
        return self.radius

    def draw(self, canvas, ctx) -> None:
        """Draw the circle."""
        ctx.draw_circle(canvas, self, self.pos, self.collision_radius)


class Polygon(Body):
    """A regular polygon with a configurable number of sides."""

    def __init__(
        self,
        radius: float = 20.0,
        sides: int = 3,
        pos: Vec2Like = (0.0, 0.0),
        *,
        corner_radius: float = 0.0,
        **kwargs,
    ) -> None:
        if sides < 3:
            raise ValueError("a polygon needs at least 3 sides")
        super().__init__(pos, **kwargs)
        self.radius = radius
        self.sides = sides
        self.corner_radius = corner_radius
        """Rounds the corners, in pixels."""

    @property
    def collision_radius(self) -> float:
        """Circumscribed radius scaled by the object's transform."""
        return self.radius * self.transform.uniform_scale

    def vertices(self) -> list[Vec2]:
        """Corner positions in scene space, including rotation."""
        r = self.collision_radius
        start = math.radians(self.transform.rotation + 90.0)
        step = 2.0 * math.pi / self.sides
        return [
            self.pos + Vec2(math.cos(start + step * i) * r, math.sin(start + step * i) * r)
            for i in range(self.sides)
        ]

    def grow(self, amount: float) -> float:
        """Add to the radius and return the new value."""
        self.radius = max(0.0, self.radius + amount)
        return self.radius

    def draw(self, canvas, ctx) -> None:
        """Draw the polygon."""
        ctx.draw_polygon(canvas, self, self.vertices(), self.corner_radius)


class Triangle(Polygon):
    """A three-sided polygon."""

    def __init__(self, radius: float = 20.0, pos: Vec2Like = (0.0, 0.0), **kwargs) -> None:
        super().__init__(radius, sides=3, pos=pos, **kwargs)


class Square(Polygon):
    """A four-sided polygon."""

    def __init__(self, radius: float = 20.0, pos: Vec2Like = (0.0, 0.0), **kwargs) -> None:
        super().__init__(radius, sides=4, pos=pos, **kwargs)


class Pentagon(Polygon):
    """A five-sided polygon."""

    def __init__(self, radius: float = 20.0, pos: Vec2Like = (0.0, 0.0), **kwargs) -> None:
        super().__init__(radius, sides=5, pos=pos, **kwargs)


class Hexagon(Polygon):
    """A six-sided polygon."""

    def __init__(self, radius: float = 20.0, pos: Vec2Like = (0.0, 0.0), **kwargs) -> None:
        super().__init__(radius, sides=6, pos=pos, **kwargs)


class Star(Body):
    """A star with alternating outer and inner points."""

    def __init__(
        self,
        radius: float = 20.0,
        points: int = 5,
        pos: Vec2Like = (0.0, 0.0),
        *,
        inner_ratio: float = 0.5,
        **kwargs,
    ) -> None:
        super().__init__(pos, **kwargs)
        self.radius = radius
        self.points = points
        self.inner_ratio = inner_ratio

    @property
    def collision_radius(self) -> float:
        """Outer radius scaled by the object's transform."""
        return self.radius * self.transform.uniform_scale

    def vertices(self) -> list[Vec2]:
        """Alternating outer and inner corner positions in scene space."""
        outer = self.collision_radius
        inner = outer * self.inner_ratio
        start = math.radians(self.transform.rotation + 90.0)
        step = math.pi / self.points
        result = []
        for i in range(self.points * 2):
            r = outer if i % 2 == 0 else inner
            angle = start + step * i
            result.append(self.pos + Vec2(math.cos(angle) * r, math.sin(angle) * r))
        return result

    def grow(self, amount: float) -> float:
        """Add to the outer radius and return the new value."""
        self.radius = max(0.0, self.radius + amount)
        return self.radius

    def draw(self, canvas, ctx) -> None:
        """Draw the star."""
        ctx.draw_polygon(canvas, self, self.vertices(), 0.0)


class Rect(Body):
    """An axis-aligned rectangle that still collides as a circle."""

    def __init__(
        self,
        width: float = 40.0,
        height: float = 40.0,
        pos: Vec2Like = (0.0, 0.0),
        *,
        corner_radius: float = 0.0,
        **kwargs,
    ) -> None:
        super().__init__(pos, **kwargs)
        self.width = width
        self.height = height
        self.corner_radius = corner_radius

    @property
    def collision_radius(self) -> float:
        """Half the diagonal, scaled by the object's transform."""
        return math.hypot(self.width, self.height) / 2.0 * self.transform.uniform_scale

    def grow(self, amount: float) -> float:
        """Grow both dimensions and return the new width."""
        self.width = max(0.0, self.width + amount * 2)
        self.height = max(0.0, self.height + amount * 2)
        return self.width

    def draw(self, canvas, ctx) -> None:
        """Draw the rectangle."""
        ctx.draw_rect(canvas, self, self.pos, self.width, self.height, self.corner_radius)
