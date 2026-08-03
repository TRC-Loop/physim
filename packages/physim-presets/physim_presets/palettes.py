"""Named preset colors and palettes as plain hex strings.

Kept dependency-free on purpose: physim adapts these into ``Color`` values, so
this package never has to import physim.
"""

from __future__ import annotations

#: individual named colors, keyed by uppercase name
COLORS: dict[str, str] = {
    # basics
    "WHITE": "#ffffff",
    "BLACK": "#000000",
    "TRANSPARENT": "#00000000",
    "GRAY": "#808080",
    "LIGHT_GRAY": "#c8c8c8",
    "DARK_GRAY": "#3c3c3c",
    # saturated
    "RED": "#ff3b30",
    "ORANGE": "#ff9500",
    "YELLOW": "#ffcc00",
    "GREEN": "#34c759",
    "MINT": "#00c7be",
    "TEAL": "#30b0c7",
    "CYAN": "#32ade6",
    "BLUE": "#007aff",
    "INDIGO": "#5856d6",
    "PURPLE": "#af52de",
    "PINK": "#ff2d55",
    "BROWN": "#a2845e",
    # neon, where these videos usually live
    "NEON_PINK": "#ff006e",
    "NEON_BLUE": "#3a86ff",
    "NEON_GREEN": "#39ff14",
    "NEON_YELLOW": "#faff00",
    "NEON_ORANGE": "#ff6b00",
    "NEON_PURPLE": "#b100ff",
    "NEON_CYAN": "#00fff5",
    "NEON_RED": "#ff1744",
    # muted backgrounds
    "MIDNIGHT": "#0b0b12",
    "CHARCOAL": "#16161f",
    "SLATE": "#1f2430",
    "CREAM": "#f5f0e6",
    "PAPER": "#fdfcf8",
}

#: ordered color sets, handy for spawning many objects at once
PALETTES: dict[str, list[str]] = {
    "neon": ["#ff006e", "#3a86ff", "#39ff14", "#faff00", "#b100ff", "#00fff5"],
    "rainbow": ["#ff3b30", "#ff9500", "#ffcc00", "#34c759", "#007aff", "#5856d6", "#af52de"],
    "pastel": ["#ffd6e0", "#ffefcf", "#d6f5e3", "#d6e8ff", "#e8d6ff"],
    "sunset": ["#ff5f6d", "#ff8a5c", "#ffc371", "#ffe29a"],
    "ocean": ["#012a4a", "#01497c", "#2a6f97", "#61a5c2", "#a9d6e5"],
    "mono": ["#ffffff", "#c8c8c8", "#808080", "#3c3c3c"],
    "fire": ["#ffec5c", "#ffa62b", "#ff5722", "#c1121f"],
    "ice": ["#caf0f8", "#90e0ef", "#00b4d8", "#0077b6"],
    "vaporwave": ["#ff71ce", "#01cdfe", "#05ffa1", "#b967ff", "#fffb96"],
    "earth": ["#606c38", "#283618", "#fefae0", "#dda15e", "#bc6c25"],
}
