"""Smoothstep-family curves with zero derivatives at both ends."""

from ..base import register


@register("smoothstep")
def smoothstep(t: float) -> float:
    """Classic Hermite smoothstep, flat at both ends."""
    return t * t * (3.0 - 2.0 * t)


@register("smootherstep")
def smootherstep(t: float) -> float:
    """Ken Perlin's smootherstep, with a zero second derivative at both ends."""
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
