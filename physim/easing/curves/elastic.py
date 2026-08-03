"""Springy curves that oscillate into place."""

import math

from ..base import register


@register("ease_in_elastic")
def ease_in_elastic(t: float) -> float:
    """Winds up with growing oscillation, then snaps to the target."""
    if t in (0.0, 1.0):
        return t
    c4 = (2 * math.pi) / 3
    return -(2 ** (10 * t - 10)) * math.sin((t * 10 - 10.75) * c4)


@register("ease_out_elastic")
def ease_out_elastic(t: float) -> float:
    """Overshoots and oscillates with decaying amplitude into the target."""
    if t in (0.0, 1.0):
        return t
    c4 = (2 * math.pi) / 3
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


@register("ease_in_out_elastic")
def ease_in_out_elastic(t: float) -> float:
    """Elastic wind-up and elastic settle."""
    if t in (0.0, 1.0):
        return t
    c5 = (2 * math.pi) / 4.5
    if t < 0.5:
        return -(2 ** (20 * t - 10) * math.sin((20 * t - 11.125) * c5)) / 2
    return (2 ** (-20 * t + 10) * math.sin((20 * t - 11.125) * c5)) / 2 + 1
