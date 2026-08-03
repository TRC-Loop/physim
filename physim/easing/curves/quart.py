"""Quartic curves."""

from ..base import register


@register("ease_in_quart")
def ease_in_quart(t: float) -> float:
    """Steep acceleration from zero velocity."""
    return t**4


@register("ease_out_quart")
def ease_out_quart(t: float) -> float:
    """Steep deceleration to zero velocity."""
    return 1.0 - (1.0 - t) ** 4


@register("ease_in_out_quart")
def ease_in_out_quart(t: float) -> float:
    """Steep accelerate-then-decelerate."""
    return 8 * t**4 if t < 0.5 else 1.0 - (-2 * t + 2) ** 4 / 2
