"""Colors that change over the course of a scene."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import Color, ColorLike


class DynamicColor:
    """Base class for colors that change over time.

    Anywhere the renderer accepts a color it also accepts a ``DynamicColor``,
    which is resolved once per frame through :meth:`at`.
    """

    def at(self, time: float) -> Color:
        """Return the concrete color at ``time`` seconds into the scene."""
        raise NotImplementedError


@dataclass
class RGBCycle(DynamicColor):
    """A color that continuously cycles through hues.

    Cycling in ``oklch`` holds perceived brightness steady, avoiding the
    dark-blue/bright-yellow flicker of a naive HSV sweep.
    """

    speed: float = 60.0
    """Degrees of hue per second."""

    offset: float = 0.0
    """Starting hue in degrees."""

    space: str = "oklch"
    """Either ``"oklch"`` (perceptual, recommended) or ``"hsl"``."""

    lightness: float = 0.72
    chroma: float = 0.19
    saturation: float = 1.0
    alpha: float = 1.0

    def at(self, time: float) -> Color:
        """Resolve the hue for ``time`` seconds."""
        hue = (self.offset + self.speed * time) % 360.0
        if self.space == "hsl":
            return Color.hsl(hue, self.saturation, 0.5, self.alpha)
        return Color.oklch(self.lightness, self.chroma, hue, self.alpha)


@dataclass
class ColorSequence(DynamicColor):
    """Steps through a fixed list of colors, on a timer or on demand.

    With ``interval`` set the sequence advances by itself; otherwise it only
    moves when :meth:`advance` is called, which is how the ``ChangeColor``
    action drives per-bounce color changes.
    """

    colors: list[ColorLike] = field(default_factory=list)
    interval: float | None = None
    """Seconds per color. ``None`` means manual advance only."""

    loop: bool = True
    index: int = 0

    def __post_init__(self) -> None:
        self.colors = [Color.of(c) for c in self.colors] or [Color("#ffffff")]

    def advance(self) -> Color:
        """Move to the next color and return it."""
        self.index += 1
        if self.index >= len(self.colors):
            self.index = 0 if self.loop else len(self.colors) - 1
        return Color.of(self.colors[self.index])

    def at(self, time: float) -> Color:
        """Resolve the active color for ``time`` seconds."""
        if self.interval:
            step = int(time / self.interval)
            idx = step % len(self.colors) if self.loop else min(step, len(self.colors) - 1)
            return Color.of(self.colors[idx])
        return Color.of(self.colors[self.index])


@dataclass
class Fade(DynamicColor):
    """Blends between two colors over a fixed duration, optionally ping-ponging."""

    start: ColorLike = "#ffffff"
    end: ColorLike = "#ff0055"
    duration: float = 1.0
    loop: bool = True
    pingpong: bool = True
    space: str = "oklch"

    def at(self, time: float) -> Color:
        """Resolve the blended color for ``time`` seconds."""
        if self.duration <= 0:
            return Color.of(self.end)
        t = time / self.duration
        if self.loop:
            t = t % 2.0 if self.pingpong else t % 1.0
            if self.pingpong and t > 1.0:
                t = 2.0 - t
        else:
            t = min(1.0, t)
        return Color.of(self.start).interpolate(self.end, t, space=self.space)
