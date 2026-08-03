"""Circular curves."""

import math

from ..base import register


@register("ease_in_circ")
def ease_in_circ(t: float) -> float:
    """Follows a quarter circle, slow start with a hard finish."""
    return 1.0 - math.sqrt(max(0.0, 1.0 - t * t))


@register("ease_out_circ")
def ease_out_circ(t: float) -> float:
    """Follows a quarter circle, hard start with a slow finish."""
    return math.sqrt(max(0.0, 1.0 - (t - 1) ** 2))


@register("ease_in_out_circ")
def ease_in_out_circ(t: float) -> float:
    """Circular in and out."""
    if t < 0.5:
        return (1.0 - math.sqrt(max(0.0, 1.0 - (2 * t) ** 2))) / 2
    return (math.sqrt(max(0.0, 1.0 - (-2 * t + 2) ** 2)) + 1) / 2
