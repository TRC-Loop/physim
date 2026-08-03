"""Named physics presets as plain parameter dicts.

These describe only *physical* behavior. Anything that changes over time
(growing on bounce, speeding up, cloning) belongs to physim's event actions,
not to a preset.

Keys map one-to-one onto ``physim.physics.PhysicsParams``.
"""

from __future__ import annotations

#: every built-in preset, keyed by name
PRESETS: dict[str, dict[str, float | bool | str]] = {
    "classic": {
        "gravity": 1200.0,
        "restitution": 0.98,
        "damping": 0.999,
        "friction": 0.0,
        "description": "the default social-media look: firm gravity, lively bounces",
    },
    "bouncy": {
        "gravity": 900.0,
        "restitution": 1.0,
        "damping": 1.0,
        "friction": 0.0,
        "description": "perfectly elastic, never loses energy",
    },
    "zero_g": {
        "gravity": 0.0,
        "restitution": 1.0,
        "damping": 1.0,
        "friction": 0.0,
        "description": "no gravity, constant-speed billiards",
    },
    "chaos": {
        "gravity": 1600.0,
        "restitution": 1.02,
        "damping": 1.0,
        "friction": 0.0,
        "max_speed": 4000.0,
        "description": "gains energy on every bounce, capped so it stays renderable",
    },
    "floaty": {
        "gravity": 300.0,
        "restitution": 0.9,
        "damping": 0.99,
        "friction": 0.01,
        "description": "low gravity and gentle damping, slow drifting motion",
    },
    "heavy": {
        "gravity": 2600.0,
        "restitution": 0.55,
        "damping": 0.995,
        "friction": 0.1,
        "description": "strong gravity and dead bounces, thuddy and grounded",
    },
    "orbit": {
        "gravity": 0.0,
        "restitution": 1.0,
        "damping": 1.0,
        "friction": 0.0,
        "attraction": 900_000.0,
        "description": "central attraction instead of downward gravity",
    },
    "jelly": {
        "gravity": 1000.0,
        "restitution": 0.8,
        "damping": 0.997,
        "friction": 0.02,
        "softness": 0.35,
        "wobble": 0.25,
        "description": "soft, squishy collision response with a visible wobble",
    },
    "molasses": {
        "gravity": 1400.0,
        "restitution": 0.3,
        "damping": 0.96,
        "friction": 0.2,
        "description": "heavily damped, everything settles fast",
    },
    "pinball": {
        "gravity": 1800.0,
        "restitution": 1.01,
        "damping": 1.0,
        "friction": 0.0,
        "max_speed": 3000.0,
        "description": "fast and snappy with a slight energy gain",
    },
}
