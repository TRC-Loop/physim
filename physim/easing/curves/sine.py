"""Sinusoidal curves."""

import math

from ..base import register


@register("ease_in_sine")
def ease_in_sine(t: float) -> float:
    """Gentle acceleration."""
    return 1.0 - math.cos((t * math.pi) / 2)


@register("ease_out_sine")
def ease_out_sine(t: float) -> float:
    """Gentle deceleration."""
    return math.sin((t * math.pi) / 2)


@register("ease_in_out_sine")
def ease_in_out_sine(t: float) -> float:
    """Gentle in and out, the softest of the standard curves."""
    return -(math.cos(math.pi * t) - 1) / 2
