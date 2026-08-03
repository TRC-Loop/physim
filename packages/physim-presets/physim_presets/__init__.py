"""Preset data for physim: color palettes and physics parameter sets.

This package is deliberately dependency-free and contains only plain data, so
physim can adapt it without either package importing the other.
"""

from .palettes import COLORS, PALETTES
from .physics import PRESETS

__version__ = "0.0.0"

__all__ = ["COLORS", "PALETTES", "PRESETS", "__version__"]
