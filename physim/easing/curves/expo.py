"""Exponential curves."""

from ..base import register


@register("ease_in_expo")
def ease_in_expo(t: float) -> float:
    """Exponential ramp up from a near standstill."""
    return 0.0 if t == 0.0 else 2 ** (10 * t - 10)


@register("ease_out_expo")
def ease_out_expo(t: float) -> float:
    """Exponential ramp down to a near standstill."""
    return 1.0 if t == 1.0 else 1.0 - 2 ** (-10 * t)


@register("ease_in_out_expo")
def ease_in_out_expo(t: float) -> float:
    """Exponential in and out."""
    if t in (0.0, 1.0):
        return t
    if t < 0.5:
        return 2 ** (20 * t - 10) / 2
    return (2 - 2 ** (-20 * t + 10)) / 2
