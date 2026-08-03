"""The core :class:`Color` value type.

Backed by :mod:`coloraide`, so any CSS color space is available: hex, rgb, hsl,
cmyk, lab, lch, oklab and oklch.
"""

from __future__ import annotations

from typing import Union

from coloraide import Color as _Color

ColorLike = Union["Color", str, tuple[float, ...]]

#: default space used when blending two colors, chosen for perceptual evenness
DEFAULT_INTERPOLATION_SPACE = "oklch"


class Color:
    """A color in any supported space, convertible to 8-bit sRGB.

    Accepts CSS syntax directly (``Color("#ff0055")``, ``Color("red")``,
    ``Color("oklch(70% 0.2 20)")``) or via the space-named constructors.
    """

    # _rgba8 caches the gamut-mapped result; converting through coloraide is by
    # far the most expensive thing a frame does, and a color never changes once
    # built (every mutating method returns a new one)
    __slots__ = ("_c", "_rgba8")

    def __init__(self, value: ColorLike = "#ffffff", alpha: float | None = None) -> None:
        self._rgba8: tuple[int, int, int, int] | None = None
        if isinstance(value, Color):
            self._c = value._c.clone()
            if alpha is None:
                self._rgba8 = value._rgba8
        elif isinstance(value, (tuple, list)):
            self._c = Color.rgb(*value)._c
        else:
            self._c = _Color(value)
        if alpha is not None:
            self._c["alpha"] = alpha

    @classmethod
    def of(cls, value: ColorLike) -> Color:
        """Coerce a string, tuple or ``Color`` into a ``Color``."""
        return value if isinstance(value, Color) else cls(value)

    @classmethod
    def rgb(cls, r: float, g: float, b: float, a: float = 1.0) -> Color:
        """Build from 0-255 sRGB channels, or 0-1 floats if every value is <= 1."""
        scale = 1.0 if max(r, g, b) <= 1.0 else 255.0
        return cls(_Color("srgb", [r / scale, g / scale, b / scale], a).to_string())

    @classmethod
    def hsl(cls, h: float, s: float, lightness: float, a: float = 1.0) -> Color:
        """Build from hue in degrees plus 0-1 saturation and lightness."""
        return cls(_Color("hsl", [h, s, lightness], a).to_string())

    @classmethod
    def cmyk(cls, c: float, m: float, y: float, k: float, a: float = 1.0) -> Color:
        """Build from 0-1 CMYK channels using a naive device conversion."""
        r = (1.0 - min(1.0, c + k)) * 255.0
        g = (1.0 - min(1.0, m + k)) * 255.0
        b = (1.0 - min(1.0, y + k)) * 255.0
        return cls.rgb(r, g, b, a)

    @classmethod
    def lab(cls, lightness: float, a_axis: float, b_axis: float, a: float = 1.0) -> Color:
        """Build from CIE Lab: lightness 0-100 plus the two opponent axes."""
        return cls(_Color("lab", [lightness, a_axis, b_axis], a).to_string())

    @classmethod
    def lch(cls, lightness: float, chroma: float, hue: float, a: float = 1.0) -> Color:
        """Build from CIE LCh: lightness 0-100, chroma, hue in degrees."""
        return cls(_Color("lch", [lightness, chroma, hue], a).to_string())

    @classmethod
    def oklch(cls, lightness: float, chroma: float, hue: float, a: float = 1.0) -> Color:
        """Build from OkLCh: lightness 0-1, chroma roughly 0-0.4, hue in degrees."""
        return cls(_Color("oklch", [lightness, chroma, hue], a).to_string())

    @classmethod
    def oklab(cls, lightness: float, a_axis: float, b_axis: float, a: float = 1.0) -> Color:
        """Build from OkLab: lightness 0-1 plus the two opponent axes."""
        return cls(_Color("oklab", [lightness, a_axis, b_axis], a).to_string())

    @classmethod
    def hex(cls, value: str) -> Color:
        """Build from a hex string, with or without a leading ``#``."""
        return cls(value if value.startswith("#") else f"#{value}")

    @property
    def alpha(self) -> float:
        """Opacity from 0 to 1."""
        return float(self._c["alpha"])

    def with_alpha(self, alpha: float) -> Color:
        """Return a copy with the given opacity."""
        return Color(self, alpha=alpha)

    def convert(self, space: str) -> Color:
        """Return this color converted into another color space."""
        return Color(self._c.convert(space).to_string())

    def coords(self, space: str | None = None) -> tuple[float, ...]:
        """Channel values in ``space``, or in this color's own space by default."""
        c = self._c if space is None else self._c.convert(space)
        return tuple(float(v) for v in c[:-1])

    def to_rgba8(self) -> tuple[int, int, int, int]:
        """Convert to gamut-mapped 8-bit RGBA, the form the renderer consumes.

        Cached, since this runs once per object per frame and the conversion
        dominates render time otherwise.
        """
        if self._rgba8 is None:
            srgb = self._c.convert("srgb").fit()
            r, g, b = (max(0.0, min(1.0, float(v))) for v in srgb[:-1])
            self._rgba8 = (
                round(r * 255),
                round(g * 255),
                round(b * 255),
                round(self.alpha * 255),
            )
        return self._rgba8

    def to_argb32(self) -> int:
        """Pack into the 0xAARRGGBB integer Skia expects."""
        r, g, b, a = self.to_rgba8()
        return (a << 24) | (r << 16) | (g << 8) | b

    def interpolate(
        self, other: ColorLike, t: float, space: str = DEFAULT_INTERPOLATION_SPACE
    ) -> Color:
        """Blend toward ``other`` by ``t`` (0-1) through the given color space."""
        target = Color.of(other)
        mixed = self._c.mix(target._c, max(0.0, min(1.0, t)), space=space, out_space="srgb")
        return Color(mixed.to_string())

    def lighten(self, amount: float) -> Color:
        """Return a perceptually lighter color, ``amount`` in 0-1."""
        c = self._c.convert("oklch")
        c["lightness"] = min(1.0, float(c["lightness"]) + amount)
        return Color(c.to_string())

    def darken(self, amount: float) -> Color:
        """Return a perceptually darker color, ``amount`` in 0-1."""
        return self.lighten(-amount)

    def to_string(self) -> str:
        """CSS representation of this color."""
        return self._c.to_string()

    def __repr__(self) -> str:
        return f"Color({self.to_string()!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Color):
            return NotImplemented
        return self.to_rgba8() == other.to_rgba8()

    def __hash__(self) -> int:
        return hash(self.to_rgba8())
