"""Runnable example scenes for physim.

Every example is a module you can run directly::

    python -m physim_examples.bouncing_ball
    python -m physim_examples.escape_ring --debug
    python -m physim_examples.growing_ball --seconds 5 -o out.mp4

List them all with ``python -m physim_examples``.
"""

__version__ = "0.0.0"

#: every example module and a one-line description
EXAMPLES: dict[str, str] = {
    "bouncing_ball": "one color-cycling ball bouncing inside a ring",
    "growing_ball": "a ball that grows and speeds up on every bounce",
    "escape_ring": "a ball escaping through a spinning gap",
    "ring_stack": "working outward through concentric rings",
    "cloning_balls": "one ball splits into hundreds",
    "melody_bounce": "each bounce plays the next note of a tune",
    "styled_text": "text styling, gradients and backgrounds",
    "expr_shape": "shapes traced from math expressions",
}

__all__ = ["EXAMPLES", "__version__"]
