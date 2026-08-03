"""Discrete, non-continuous curves."""

from ..base import register


@register("step")
def step(t: float) -> float:
    """Jumps from 0 to 1 at the halfway point, with no interpolation."""
    return 0.0 if t < 0.5 else 1.0


@register("step_start")
def step_start(t: float) -> float:
    """Snaps to the target immediately."""
    return 0.0 if t <= 0.0 else 1.0


@register("step_end")
def step_end(t: float) -> float:
    """Holds at the start until the very end, then snaps."""
    return 1.0 if t >= 1.0 else 0.0
