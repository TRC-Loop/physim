"""Quintic curves."""

from ..base import register


@register("ease_in_quint")
def ease_in_quint(t: float) -> float:
    """Very steep acceleration from zero velocity."""
    return t**5


@register("ease_out_quint")
def ease_out_quint(t: float) -> float:
    """Very steep deceleration to zero velocity."""
    return 1.0 - (1.0 - t) ** 5


@register("ease_in_out_quint")
def ease_in_out_quint(t: float) -> float:
    """Very steep accelerate-then-decelerate."""
    return 16 * t**5 if t < 0.5 else 1.0 - (-2 * t + 2) ** 5 / 2
