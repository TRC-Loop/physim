"""The fake physics engine and its tunable parameters.

Named presets live in the optional ``physim-presets`` package and are reached
through :func:`physim.presets.physics`.
"""

from .collision import Contact, resolve_pair, resolve_wall
from .engine import Engine
from .params import PhysicsParams
from .spatial import SpatialGrid

__all__ = [
    "Contact",
    "Engine",
    "PhysicsParams",
    "SpatialGrid",
    "resolve_pair",
    "resolve_wall",
]
