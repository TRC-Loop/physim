"""Output frame dimensions and scene/raster coordinate conversion."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .size import Size
from .vec2 import Vec2, Vec2Like

#: named shorthands accepted by :meth:`Resolution.parse`
PRESETS: dict[str, tuple[int, int]] = {
    "vertical": (1080, 1920),
    "square": (1080, 1080),
    "landscape": (1920, 1080),
    "hd": (1280, 720),
    "fhd": (1920, 1080),
    "4k": (3840, 2160),
}


@dataclass(frozen=True, slots=True)
class Resolution:
    """Frame dimensions in whole pixels."""

    width: int = 1080
    height: int = 1080

    @classmethod
    def parse(cls, value: str | Resolution | tuple[int, int] | list[int]) -> Resolution:
        """Parse a preset name (``"square"``), a ``"1080x1920"`` string, or a pair."""
        if isinstance(value, Resolution):
            return value
        if isinstance(value, (tuple, list)):
            return cls(int(value[0]), int(value[1]))
        key = str(value).strip().lower()
        if key in PRESETS:
            return cls(*PRESETS[key])
        if "x" in key:
            w, h = key.split("x", 1)
            return cls(int(w), int(h))
        raise ValueError(
            f"unknown resolution {value!r}; use WIDTHxHEIGHT or one of {sorted(PRESETS)}"
        )

    def __iter__(self) -> Iterator[int]:
        yield self.width
        yield self.height

    def __str__(self) -> str:
        return f"{self.width}x{self.height}"

    @property
    def size(self) -> Size:
        """This resolution as a float ``Size``."""
        return Size(float(self.width), float(self.height))

    @property
    def aspect(self) -> float:
        """Width divided by height."""
        return self.width / self.height

    def to_raster(self, point: Vec2Like) -> Vec2:
        """Convert a centered y-up scene point into top-left y-down raster space."""
        p = Vec2.of(point)
        return Vec2(p.x + self.width / 2.0, self.height / 2.0 - p.y)

    def to_scene(self, point: Vec2Like) -> Vec2:
        """Convert a top-left y-down raster point back into centered y-up scene space."""
        p = Vec2.of(point)
        return Vec2(p.x - self.width / 2.0, self.height / 2.0 - p.y)
