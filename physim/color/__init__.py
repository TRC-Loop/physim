"""Color values, gradients, textures and animated colors.

Named preset colors live in the optional ``physim-presets`` package, reachable
through :mod:`physim.colors`.
"""

from .base import DEFAULT_INTERPOLATION_SPACE, Color, ColorLike
from .dynamic import ColorSequence, DynamicColor, Fade, RGBCycle
from .gradient import GRADIENT_KINDS, Gradient, Paint, resolve_paint
from .texture import FIT_MODES, Texture, clear_cache, load_image

__all__ = [
    "DEFAULT_INTERPOLATION_SPACE",
    "FIT_MODES",
    "GRADIENT_KINDS",
    "Color",
    "ColorLike",
    "ColorSequence",
    "DynamicColor",
    "Fade",
    "Gradient",
    "Paint",
    "RGBCycle",
    "Texture",
    "clear_cache",
    "load_image",
    "resolve_paint",
]
