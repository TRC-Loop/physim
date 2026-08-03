"""Actions that change how an object moves or how big it is."""

from __future__ import annotations

from ..events import Event
from ..types import Vec2, Vec2Like
from .base import Action


class SpeedUp(Action):
    """Multiplies the object's speed, optionally up to a ceiling.

    This is how the escalating videos are built: each bounce makes the next
    one faster.
    """

    def __init__(self, factor: float = 1.05, max_speed: float | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.factor = factor
        self.max_speed = max_speed

    def apply(self, event: Event) -> None:
        """Scale the source object's velocity."""
        body = event.source
        speed = body.speed * self.factor
        if self.max_speed is not None:
            speed = min(speed, self.max_speed)
        body.speed = speed


class SlowDown(SpeedUp):
    """Multiplies the object's speed by a factor below one."""

    def __init__(self, factor: float = 0.95, min_speed: float = 0.0, **kwargs) -> None:
        super().__init__(factor=factor, **kwargs)
        self.min_speed = min_speed

    def apply(self, event: Event) -> None:
        """Scale the velocity down, never below the floor."""
        body = event.source
        body.speed = max(self.min_speed, body.speed * self.factor)


class SetSpeed(Action):
    """Sets the object's speed to an exact value, keeping its direction."""

    def __init__(self, speed: float, **kwargs) -> None:
        super().__init__(**kwargs)
        self.speed = speed

    def apply(self, event: Event) -> None:
        """Assign the configured speed."""
        event.source.speed = self.speed


class Impulse(Action):
    """Adds a one-off velocity kick."""

    def __init__(self, impulse: Vec2Like = (0.0, 300.0), **kwargs) -> None:
        super().__init__(**kwargs)
        self.impulse = Vec2.of(impulse)

    def apply(self, event: Event) -> None:
        """Apply the impulse to the source object."""
        event.source.apply_impulse(self.impulse)


class Grow(Action):
    """Increases the object's size, optionally up to a maximum.

    Objects expose ``grow``, so this works for circles, polygons and rects.
    """

    def __init__(self, amount: float = 2.0, max_size: float | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.amount = amount
        self.max_size = max_size

    def apply(self, event: Event) -> None:
        """Grow the source object."""
        obj = event.source
        new_size = obj.grow(self.amount)
        if self.max_size is not None and new_size > self.max_size:
            obj.grow(self.max_size - new_size)


class Shrink(Grow):
    """Decreases the object's size, never below a floor."""

    def __init__(self, amount: float = 2.0, min_size: float = 1.0, **kwargs) -> None:
        super().__init__(amount=-abs(amount), **kwargs)
        self.min_size = min_size

    def apply(self, event: Event) -> None:
        """Shrink the source object."""
        obj = event.source
        new_size = obj.grow(self.amount)
        if new_size < self.min_size:
            obj.grow(self.min_size - new_size)


class Reverse(Action):
    """Flips the object's direction of travel."""

    def apply(self, event: Event) -> None:
        """Negate the velocity."""
        event.source.velocity = -event.source.velocity


class Teleport(Action):
    """Moves the object to a fixed position."""

    def __init__(self, position: Vec2Like = (0.0, 0.0), **kwargs) -> None:
        super().__init__(**kwargs)
        self.position = Vec2.of(position)

    def apply(self, event: Event) -> None:
        """Place the object at the target position."""
        event.source.transform.position = self.position
