"""Tunable parameters for the physics engine.

These describe purely physical behavior. Anything that changes over time, such
as growing on bounce or speeding up, is an event action rather than a physics
parameter.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from ..types import Vec2, Vec2Like


@dataclass
class PhysicsParams:
    """Physical constants for a simulation.

    Defaults are the sensible middle ground used when no preset is chosen:
    firm downward gravity with lively but slightly lossy bounces.
    """

    gravity: float = 850.0
    """Downward acceleration in pixels per second squared."""

    gravity_direction: Vec2 = Vec2(0.0, -1.0)
    """Unit direction gravity pulls toward. Default points down in y-up space."""

    restitution: float = 0.98
    """Fraction of speed kept after a bounce. Above 1 gains energy."""

    damping: float = 0.999
    """Velocity retained per second of simulated time, applied continuously."""

    friction: float = 0.0
    """Tangential velocity lost on contact, from 0 to 1."""

    attraction: float = 0.0
    """Strength of a pull toward the scene center, used by orbit-style setups."""

    attraction_point: Vec2 = Vec2(0.0, 0.0)
    """Where :attr:`attraction` pulls toward."""

    max_speed: float | None = None
    """Optional speed ceiling in pixels per second."""

    min_speed: float = 0.0
    """Speed below which an object is treated as at rest."""

    softness: float = 0.0
    """Collision softness from 0 (rigid) to 1 (very squishy)."""

    wobble: float = 0.0
    """Visual deformation applied on impact, from 0 to 1."""

    substeps: int = 4
    """Maximum physics iterations per rendered frame. Higher is more stable and slower."""

    adaptive_substeps: bool = True
    """Use fewer substeps when nothing is moving fast enough to need them.

    Substeps exist so a fast object cannot tunnel through a wall in one jump.
    When the fastest object travels well under its own radius per frame the
    extra iterations change nothing, so they are skipped. Set to false for a
    fixed :attr:`substeps` count.
    """

    ball_collisions: bool = False
    """Whether objects collide with each other as well as with boundaries."""

    def __post_init__(self) -> None:
        self.gravity_direction = Vec2.of(self.gravity_direction).normalized()
        self.attraction_point = Vec2.of(self.attraction_point)
        if self.substeps < 1:
            raise ValueError("substeps must be at least 1")
        if not 0.0 <= self.friction <= 1.0:
            raise ValueError("friction must be between 0 and 1")

    @property
    def gravity_vector(self) -> Vec2:
        """Gravity as an acceleration vector."""
        return self.gravity_direction * self.gravity

    def with_(self, **changes) -> PhysicsParams:
        """Return a copy with the given fields replaced.

        >>> PhysicsParams().with_(gravity=0, restitution=1.0)
        """
        return replace(self, **changes)

    def pointing(self, direction: Vec2Like) -> PhysicsParams:
        """Return a copy with gravity pulling in a different direction."""
        return self.with_(gravity_direction=Vec2.of(direction))
