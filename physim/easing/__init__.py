"""Easing curves for animations.

Curves map a normalized time in 0-1 to an eased 0-1 value, and are referenced
by name anywhere an easing is accepted. Add your own with :func:`register`.
"""

from . import curves as _curves  # noqa: F401  (importing registers the built-ins)
from .base import EASINGS, Easing, add, get, lerp, names, register
from .curves.back import ease_in_back, ease_in_out_back, ease_out_back
from .curves.bounce import ease_in_bounce, ease_in_out_bounce, ease_out_bounce
from .curves.circ import ease_in_circ, ease_in_out_circ, ease_out_circ
from .curves.cubic import ease_in_cubic, ease_in_out_cubic, ease_out_cubic
from .curves.elastic import ease_in_elastic, ease_in_out_elastic, ease_out_elastic
from .curves.expo import ease_in_expo, ease_in_out_expo, ease_out_expo
from .curves.linear import linear
from .curves.quad import ease_in_out_quad, ease_in_quad, ease_out_quad
from .curves.quart import ease_in_out_quart, ease_in_quart, ease_out_quart
from .curves.quint import ease_in_out_quint, ease_in_quint, ease_out_quint
from .curves.sine import ease_in_out_sine, ease_in_sine, ease_out_sine
from .curves.smooth import smootherstep, smoothstep
from .curves.spring import spring, spring_tight, spring_with
from .curves.step import step, step_end, step_start

__all__ = [
    "EASINGS",
    "Easing",
    "add",
    "ease_in_back",
    "ease_in_bounce",
    "ease_in_circ",
    "ease_in_cubic",
    "ease_in_elastic",
    "ease_in_expo",
    "ease_in_out_back",
    "ease_in_out_bounce",
    "ease_in_out_circ",
    "ease_in_out_cubic",
    "ease_in_out_elastic",
    "ease_in_out_expo",
    "ease_in_out_quad",
    "ease_in_out_quart",
    "ease_in_out_quint",
    "ease_in_out_sine",
    "ease_in_quad",
    "ease_in_quart",
    "ease_in_quint",
    "ease_in_sine",
    "ease_out_back",
    "ease_out_bounce",
    "ease_out_circ",
    "ease_out_cubic",
    "ease_out_elastic",
    "ease_out_expo",
    "ease_out_quad",
    "ease_out_quart",
    "ease_out_quint",
    "ease_out_sine",
    "get",
    "lerp",
    "linear",
    "names",
    "register",
    "smootherstep",
    "smoothstep",
    "spring",
    "spring_tight",
    "spring_with",
    "step",
    "step_end",
    "step_start",
]
