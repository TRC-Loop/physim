"""Quadratic curves."""

from ..base import register


@register("ease_in_quad")
def ease_in_quad(t: float) -> float:
    """Accelerate from zero velocity."""
    return t * t


@register("ease_out_quad")
def ease_out_quad(t: float) -> float:
    """Decelerate to zero velocity."""
    return 1.0 - (1.0 - t) ** 2


@register("ease_in_out_quad")
def ease_in_out_quad(t: float) -> float:
    """Accelerate, then decelerate."""
    return 2 * t * t if t < 0.5 else 1.0 - (-2 * t + 2) ** 2 / 2
