"""Gradient fills and the resolver that normalizes any fill value."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Union

from ..types import Vec2, Vec2Like
from .base import Color, ColorLike
from .dynamic import DynamicColor
from .texture import Texture

#: anything accepted wherever the public API asks for a fill
Paint = Union[ColorLike, DynamicColor, "Gradient", Texture]

#: gradient geometries the renderer understands
GRADIENT_KINDS = ("linear", "radial", "sweep")


@dataclass
class Gradient:
    """A multi-stop gradient fill.

    Coordinates are in scene space. ``start``/``end`` define the axis of a
    linear gradient, while ``start``/``radius`` define a radial or sweep one.
    """

    colors: Sequence[ColorLike] = ("#ff0055", "#5500ff")
    kind: str = "linear"
    """One of ``"linear"``, ``"radial"`` or ``"sweep"``."""

    start: Vec2Like = (0.0, 0.0)
    end: Vec2Like = (0.0, 100.0)
    radius: float = 100.0
    stops: Sequence[float] | None = None
    """Optional 0-1 positions, one per color. Evenly spaced when omitted."""

    relative: bool = True
    """When true the axis is scaled to the bounds of the shape being filled."""

    rotation: float = 0.0
    """Rotation of the gradient axis in degrees."""

    def __post_init__(self) -> None:
        if self.kind not in GRADIENT_KINDS:
            raise ValueError(f"kind must be one of {GRADIENT_KINDS}, got {self.kind!r}")

    def resolved_colors(self) -> list[Color]:
        """Colors as concrete ``Color`` values."""
        return [Color.of(c) for c in self.colors]

    def resolved_stops(self) -> list[float]:
        """Stop positions, filled in evenly when not supplied."""
        if self.stops is not None:
            return list(self.stops)
        count = len(self.colors)
        if count < 2:
            return [0.0]
        return [i / (count - 1) for i in range(count)]

    @property
    def start_vec(self) -> Vec2:
        """Gradient axis start as a ``Vec2``."""
        return Vec2.of(self.start)

    @property
    def end_vec(self) -> Vec2:
        """Gradient axis end as a ``Vec2``."""
        return Vec2.of(self.end)


def resolve_paint(value: Paint | None, time: float) -> Color | Gradient | Texture | None:
    """Resolve any accepted fill into a concrete color, gradient or texture.

    Dynamic colors are sampled at ``time``; everything else passes through.
    """
    if value is None or isinstance(value, (Gradient, Texture)):
        return value
    if isinstance(value, DynamicColor):
        return value.at(time)
    return Color.of(value)
