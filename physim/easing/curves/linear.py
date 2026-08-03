"""Linear curve."""

from ..base import register


@register("linear")
def linear(t: float) -> float:
    """No easing at all."""
    return t
