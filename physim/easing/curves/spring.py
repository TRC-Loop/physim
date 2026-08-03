"""Damped spring curve.

Unlike ``ease_out_elastic`` this models an actual damped harmonic oscillator,
so its wobble decays the way a physical spring would.
"""

import math

from ..base import register


def spring_with(stiffness: float = 8.0, damping: float = 4.0):
    """Build a spring curve with custom stiffness and damping."""

    def curve(t: float) -> float:
        if t <= 0.0:
            return 0.0
        if t >= 1.0:
            return 1.0
        return 1.0 - math.exp(-damping * t) * math.cos(stiffness * t)

    return curve


@register("spring")
def spring(t: float) -> float:
    """A softly damped spring settling onto the target."""
    return spring_with()(t)


@register("spring_tight")
def spring_tight(t: float) -> float:
    """A stiffer, faster-settling spring."""
    return spring_with(stiffness=14.0, damping=8.0)(t)
