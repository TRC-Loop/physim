"""Attribute-style access to preset colors.

Requires the optional presets package::

    pip install physim[presets]

>>> from physim import colors
>>> colors.NEON_PINK
Color('rgb(255 0 110)')
>>> colors.palette("neon")
[Color(...), ...]
"""

from __future__ import annotations

from .color import Color
from .presets import color as _color
from .presets import color_names, palette, palette_names


def __getattr__(name: str) -> Color:
    """Resolve an uppercase color name lazily, so importing costs nothing."""
    if name.isupper():
        return _color(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """List available color names for autocomplete."""
    return [*color_names(), "palette", "palette_names"]


__all__ = ["palette", "palette_names"]
