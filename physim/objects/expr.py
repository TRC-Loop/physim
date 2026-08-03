"""Shapes defined by math expressions.

Needs the expr extra::

    pip install physim[expr]

Two forms are supported. A parametric shape traces ``x(t)``/``y(t)`` over a
range of ``t``; an implicit shape samples ``f(x, y) = 0`` on a grid and traces
the boundary where the sign flips.
"""

from __future__ import annotations

import numpy as np

from ..types import Vec2, Vec2Like
from .base import SceneObject
from .body import Body

_HINT = "math-expression shapes need sympy; install it with: pip install physim[expr]"


def _compile(expression: str, variables: tuple[str, ...]):
    """Turn an expression string into a fast numpy callable."""
    try:
        import sympy
    except ImportError as exc:
        raise ImportError(_HINT) from exc

    symbols = sympy.symbols(variables)
    parsed = sympy.sympify(expression)
    return sympy.lambdify(symbols, parsed, "numpy")


class ParametricShape(Body):
    """A curve traced by ``x(t)`` and ``y(t)``.

    >>> ParametricShape("100*cos(t)", "100*sin(t)", t_range=(0, 2*pi))
    """

    def __init__(
        self,
        x: str = "100*cos(t)",
        y: str = "100*sin(t)",
        pos: Vec2Like = (0.0, 0.0),
        *,
        t_range: tuple[float, float] = (0.0, 6.283185307179586),
        samples: int = 200,
        closed: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(pos, **kwargs)
        self.x_expr = x
        self.y_expr = y
        self.t_range = t_range
        self.samples = samples
        self.closed = closed
        self._points: list[Vec2] | None = None

    def points(self) -> list[Vec2]:
        """Sample the curve, caching the result."""
        if self._points is None:
            fx = _compile(self.x_expr, ("t",))
            fy = _compile(self.y_expr, ("t",))
            ts = np.linspace(self.t_range[0], self.t_range[1], self.samples)
            xs = np.broadcast_to(np.asarray(fx(ts), dtype=float), ts.shape)
            ys = np.broadcast_to(np.asarray(fy(ts), dtype=float), ts.shape)
            self._points = [Vec2(float(a), float(b)) for a, b in zip(xs, ys, strict=False)]
        return self._points

    @property
    def collision_radius(self) -> float:
        """Distance to the furthest sampled point."""
        pts = self.points()
        scale = self.transform.uniform_scale
        return max((p.length for p in pts), default=0.0) * scale

    def draw(self, canvas, ctx) -> None:
        """Draw the traced curve."""
        scale = self.transform.uniform_scale
        world = [self.pos + p * scale for p in self.points()]
        ctx.draw_polygon(canvas, self, world, 0.0)


class ImplicitShape(SceneObject):
    """A shape defined by ``f(x, y) = 0``, sampled on a grid.

    >>> ImplicitShape("x**2 + y**2 - 200**2")
    """

    def __init__(
        self,
        expression: str = "x**2 + y**2 - 200**2",
        pos: Vec2Like = (0.0, 0.0),
        *,
        bounds: float = 300.0,
        resolution: int = 200,
        **kwargs,
    ) -> None:
        super().__init__(pos, **kwargs)
        self.expression = expression
        self.bounds = bounds
        """Half-width of the sampled square region, in pixels."""

        self.resolution = resolution
        self._mask: np.ndarray | None = None

    def mask(self) -> np.ndarray:
        """Sample the expression into a boolean inside/outside grid."""
        if self._mask is None:
            fn = _compile(self.expression, ("x", "y"))
            axis = np.linspace(-self.bounds, self.bounds, self.resolution)
            grid_x, grid_y = np.meshgrid(axis, axis)
            values = np.asarray(fn(grid_x, grid_y), dtype=float)
            self._mask = values <= 0.0
        return self._mask

    def contains(self, point: Vec2Like) -> bool:
        """Whether a scene point lies inside the shape."""
        p = Vec2.of(point) - self.pos
        if abs(p.x) > self.bounds or abs(p.y) > self.bounds:
            return False
        step = (2 * self.bounds) / (self.resolution - 1)
        col = int((p.x + self.bounds) / step)
        row = int((p.y + self.bounds) / step)
        return bool(self.mask()[row, col])

    def draw(self, canvas, ctx) -> None:
        """Draw the sampled region as a filled grid."""
        ctx.draw_mask(canvas, self, self.mask(), self.pos, self.bounds)
