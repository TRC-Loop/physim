"""Visual effects that change how objects look without changing the physics.

Attach one to any object; the renderer picks it up automatically.

>>> ball.effects.append(Trail(length=30))
>>> ball.effects.append(Glow(strength=0.6))
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .types import Vec2


class Effect:
    """Base class for per-object visual effects."""

    def update(self, obj, dt: float) -> None:
        """Advance any state the effect keeps."""

    def draw_before(self, canvas, ctx, obj) -> None:
        """Draw underneath the object."""

    def draw_after(self, canvas, ctx, obj) -> None:
        """Draw on top of the object."""


@dataclass
class Trail(Effect):
    """A fading path behind a moving object."""

    length: int = 24
    """How many past positions to keep."""

    fade: float = 0.6
    """Opacity of the newest trail segment."""

    every: int = 1
    """Record a position every nth frame, for longer and sparser trails."""

    points: list[Vec2] = field(default_factory=list)
    _tick: int = 0

    def update(self, obj, dt: float) -> None:
        """Record the object's current position."""
        self._tick += 1
        if self._tick % self.every:
            return
        self.points.append(obj.pos)
        if len(self.points) > self.length:
            del self.points[: len(self.points) - self.length]

    def draw_before(self, canvas, ctx, obj) -> None:
        """Draw the recorded path underneath the object."""
        radius = getattr(obj, "collision_radius", 10.0)
        ctx.draw_trail(canvas, obj, self.points, radius, self.fade)


@dataclass
class Glow(Effect):
    """A soft halo underneath the object, for a neon look on dark backgrounds."""

    strength: float = 0.5
    """Blur radius as a fraction of the object's own radius."""

    scale: float = 1.4
    """How much larger than the object the halo is drawn."""

    def draw_before(self, canvas, ctx, obj) -> None:
        """Draw the blurred halo."""
        radius = getattr(obj, "collision_radius", 10.0)
        ctx.draw_glow(canvas, obj, obj.pos, radius * self.scale, self.strength)


@dataclass
class Pulse(Effect):
    """Scales the object rhythmically, independent of its physics size."""

    amount: float = 0.12
    speed: float = 4.0

    def update(self, obj, dt: float) -> None:
        """Apply the current pulse to the object's transform scale."""
        import math

        factor = 1.0 + self.amount * math.sin(obj.age * self.speed)
        obj.transform.scale = Vec2(factor, factor)


@dataclass
class Spin(Effect):
    """Rotates the object at a constant rate."""

    speed: float = 90.0
    """Degrees per second."""

    def update(self, obj, dt: float) -> None:
        """Advance the object's rotation."""
        obj.transform.rotation = (obj.transform.rotation + self.speed * dt) % 360.0


@dataclass
class FadeIn(Effect):
    """Fades an object in over its first moments."""

    duration: float = 0.4

    def update(self, obj, dt: float) -> None:
        """Ramp opacity up until the duration has passed."""
        if obj.age < self.duration:
            obj.transform.opacity = min(1.0, obj.age / self.duration)


__all__ = ["Effect", "FadeIn", "Glow", "Pulse", "Spin", "Trail"]
