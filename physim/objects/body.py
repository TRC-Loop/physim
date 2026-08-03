"""Base class for objects the physics engine moves."""

from __future__ import annotations

from ..color import Paint
from ..types import Vec2, Vec2Like
from .base import SceneObject


class Body(SceneObject):
    """A scene object with mass and velocity that the engine simulates.

    Per-object ``restitution``, ``mass`` and ``gravity_scale`` override the
    scene-wide physics parameters when set.
    """

    physical = True

    def __init__(
        self,
        pos: Vec2Like = (0.0, 0.0),
        *,
        velocity: Vec2Like = (0.0, 0.0),
        mass: float = 1.0,
        restitution: float | None = None,
        gravity_scale: float = 1.0,
        fixed: bool = False,
        fill: Paint | None = "#ffffff",
        **kwargs,
    ) -> None:
        super().__init__(pos, fill=fill, **kwargs)
        self.velocity = Vec2.of(velocity)
        self.mass = mass
        self.restitution = restitution
        """Bounciness override, or ``None`` to use the scene's value."""

        self.gravity_scale = gravity_scale
        """Multiplier on gravity for this object alone."""

        self.fixed = fixed
        """When true the object never moves but still blocks others."""

        self.bounces = 0
        """How many times this object has bounced, readable from handlers."""

        self.trail: list[Vec2] = []
        """Recent positions, populated when a trail effect is attached."""

    @property
    def speed(self) -> float:
        """Current speed in pixels per second."""
        return self.velocity.length

    @speed.setter
    def speed(self, value: float) -> None:
        direction = self.velocity.normalized()
        if direction.length == 0.0:
            direction = Vec2(1.0, 0.0)
        self.velocity = direction * value

    @property
    def direction(self) -> Vec2:
        """Unit vector the object is travelling along."""
        return self.velocity.normalized()

    @property
    def inverse_mass(self) -> float:
        """Reciprocal mass, zero for fixed objects."""
        if self.fixed or self.mass <= 0.0:
            return 0.0
        return 1.0 / self.mass

    def apply_impulse(self, impulse: Vec2Like) -> None:
        """Add an instantaneous velocity change, scaled by inverse mass."""
        self.velocity = self.velocity + Vec2.of(impulse) * self.inverse_mass

    def apply_force(self, force: Vec2Like, dt: float) -> None:
        """Apply a continuous force over ``dt`` seconds."""
        self.velocity = self.velocity + Vec2.of(force) * (self.inverse_mass * dt)

    def stop(self) -> None:
        """Zero the object's velocity."""
        self.velocity = Vec2()
