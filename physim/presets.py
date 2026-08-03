"""Access to the optional ``physim-presets`` package.

Presets live in a separate dependency-free distribution, so core physim works
without them. Anything here raises a clear install hint when the package is
missing, and :data:`DEFAULT` is always available regardless.

    pip install physim[presets]
"""

from __future__ import annotations

from typing import Any

from .color import Color

_HINT = "presets are optional; install them with: pip install physim[presets]"


def available() -> bool:
    """Whether the ``physim-presets`` package is importable."""
    try:
        import physim_presets  # noqa: F401
    except ImportError:
        return False
    return True


def _data() -> Any:
    """Import the presets package, or explain how to install it."""
    try:
        import physim_presets
    except ImportError as exc:
        raise ImportError(_HINT) from exc
    return physim_presets


def physics(name: str):
    """Look up a named physics preset as a ``PhysicsParams``.

    ``"custom"`` and ``"default"`` resolve to core defaults and never require
    the presets package.
    """
    from .physics import PhysicsParams

    if name in ("custom", "default"):
        return PhysicsParams()
    table = _data().PRESETS
    try:
        raw = dict(table[name])
    except KeyError:
        raise ValueError(
            f"unknown physics preset {name!r}; available: {', '.join(sorted(table))}"
        ) from None
    raw.pop("description", None)
    return PhysicsParams(**raw)


def physics_names() -> list[str]:
    """Names of every available physics preset, core defaults included."""
    names = ["custom", "default"]
    if available():
        names += sorted(_data().PRESETS)
    return names


def describe(name: str) -> str:
    """One-line description of a physics preset."""
    if name in ("custom", "default"):
        return "core defaults, tune every value yourself"
    entry = _data().PRESETS.get(name)
    if entry is None:
        raise ValueError(f"unknown physics preset {name!r}")
    return str(entry.get("description", ""))


def color(name: str) -> Color:
    """Look up a named preset color, e.g. ``"NEON_PINK"``."""
    table = _data().COLORS
    try:
        return Color(table[name.upper()])
    except KeyError:
        raise ValueError(f"unknown color {name!r}; available: {', '.join(sorted(table))}") from None


def palette(name: str) -> list[Color]:
    """Look up a named palette as a list of colors."""
    table = _data().PALETTES
    try:
        return [Color(c) for c in table[name]]
    except KeyError:
        raise ValueError(
            f"unknown palette {name!r}; available: {', '.join(sorted(table))}"
        ) from None


def palette_names() -> list[str]:
    """Sorted names of every available palette."""
    return sorted(_data().PALETTES) if available() else []


def color_names() -> list[str]:
    """Sorted names of every available preset color."""
    return sorted(_data().COLORS) if available() else []
