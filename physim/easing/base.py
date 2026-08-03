"""Easing registry and lookup.

An easing maps a normalized time ``t`` in 0-1 to an eased 0-1 value. Register
your own with :func:`register`, then use it by name anywhere an easing is
accepted.
"""

from __future__ import annotations

from collections.abc import Callable

Easing = Callable[[float], float]

#: every registered curve, keyed by name
EASINGS: dict[str, Easing] = {}


def register(name: str) -> Callable[[Easing], Easing]:
    """Decorator that registers a custom curve under ``name``.

    >>> @register("my_curve")
    ... def my_curve(t: float) -> float:
    ...     return t**0.5
    """

    def _apply(func: Easing) -> Easing:
        EASINGS[name] = func
        return func

    return _apply


def add(name: str, fn: Easing) -> Easing:
    """Register an existing callable as a curve, without decorator syntax."""
    EASINGS[name] = fn
    return fn


def get(easing: str | Easing | None) -> Easing:
    """Resolve an easing by name, pass a callable through, or default to linear."""
    if easing is None:
        return EASINGS["linear"]
    if callable(easing):
        return easing
    try:
        return EASINGS[easing]
    except KeyError:
        raise ValueError(
            f"unknown easing {easing!r}; available: {', '.join(sorted(EASINGS))}"
        ) from None


def names() -> list[str]:
    """Sorted names of every registered curve."""
    return sorted(EASINGS)


def lerp(a: float, b: float, t: float) -> float:
    """Linearly interpolate between two numbers."""
    return a + (b - a) * t
