"""Font lookup with a graceful fallback.

Named fonts are resolved through the system font manager. When a name isn't
installed the platform default is used and a warning is issued once, so a scene
still renders identically enough on a bare CI container.
"""

from __future__ import annotations

import warnings

import skia

_cache: dict[tuple, object] = {}
_warned: set[str] = set()


def typeface(name: str | None, bold: bool = False, italic: bool = False):
    """Resolve a typeface by name, weight and slant."""
    key = (name, bold, italic)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    style = skia.FontStyle(
        weight=skia.FontStyle.kBold_Weight if bold else skia.FontStyle.kNormal_Weight,
        width=skia.FontStyle.kNormal_Width,
        slant=(skia.FontStyle.kItalic_Slant if italic else skia.FontStyle.kUpright_Slant),
    )

    face = skia.Typeface(name, style) if name else skia.Typeface("", style)
    if name and face is not None and face.getFamilyName() != name and name not in _warned:
        _warned.add(name)
        warnings.warn(
            f"font {name!r} not found, falling back to {face.getFamilyName()!r}",
            stacklevel=2,
        )
    if face is None:
        face = skia.Typeface("")
    _cache[key] = face
    return face


def font(name: str | None, size: float, bold: bool = False, italic: bool = False):
    """Build a Skia font at a given size."""
    return skia.Font(typeface(name, bold, italic), size)


def measure(text: str, skia_font) -> tuple[float, float]:
    """Return the width and height of a single line of text."""
    width = skia_font.measureText(text)
    metrics = skia_font.getMetrics()
    return width, metrics.fDescent - metrics.fAscent


def clear_cache() -> None:
    """Drop every cached typeface."""
    _cache.clear()
    _warned.clear()
