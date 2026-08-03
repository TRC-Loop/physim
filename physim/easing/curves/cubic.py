"""Cubic curves."""

from ..base import register


@register("ease_in_cubic")
def ease_in_cubic(t: float) -> float:
    """Sharper acceleration from zero velocity."""
    return t**3


@register("ease_out_cubic")
def ease_out_cubic(t: float) -> float:
    """Sharper deceleration to zero velocity."""
    return 1.0 - (1.0 - t) ** 3


@register("ease_in_out_cubic")
def ease_in_out_cubic(t: float) -> float:
    """Sharper accelerate-then-decelerate."""
    return 4 * t**3 if t < 0.5 else 1.0 - (-2 * t + 2) ** 3 / 2
