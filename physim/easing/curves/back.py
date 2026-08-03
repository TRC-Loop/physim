"""Curves that overshoot the target and settle back."""

from ..base import register

#: standard overshoot constant, roughly a 10% overshoot
OVERSHOOT = 1.70158


@register("ease_in_back")
def ease_in_back(t: float) -> float:
    """Pull back slightly before moving toward the target."""
    c3 = OVERSHOOT + 1
    return c3 * t**3 - OVERSHOOT * t * t


@register("ease_out_back")
def ease_out_back(t: float) -> float:
    """Overshoot past the target, then settle back onto it."""
    c3 = OVERSHOOT + 1
    return 1 + c3 * (t - 1) ** 3 + OVERSHOOT * (t - 1) ** 2


@register("ease_in_out_back")
def ease_in_out_back(t: float) -> float:
    """Pull back at the start and overshoot at the end."""
    c2 = OVERSHOOT * 1.525
    if t < 0.5:
        return ((2 * t) ** 2 * ((c2 + 1) * 2 * t - c2)) / 2
    return ((2 * t - 2) ** 2 * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2
