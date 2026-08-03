"""Curves that bounce to a stop, like a ball dropped on a floor."""

from ..base import register


@register("ease_out_bounce")
def ease_out_bounce(t: float) -> float:
    """Bounces with decreasing height until it rests at the target."""
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1:
        return n1 * t * t
    if t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    if t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    t -= 2.625 / d1
    return n1 * t * t + 0.984375


@register("ease_in_bounce")
def ease_in_bounce(t: float) -> float:
    """The bounce curve reversed, gathering height toward the target."""
    return 1.0 - ease_out_bounce(1.0 - t)


@register("ease_in_out_bounce")
def ease_in_out_bounce(t: float) -> float:
    """Bounces in at the start and out at the end."""
    if t < 0.5:
        return (1.0 - ease_out_bounce(1 - 2 * t)) / 2
    return (1.0 + ease_out_bounce(2 * t - 1)) / 2
