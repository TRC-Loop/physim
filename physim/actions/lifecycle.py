"""Actions that create, remove or end things."""

from __future__ import annotations

from collections.abc import Callable

from ..events import Event
from ..types import Vec2, Vec2Like
from .base import Action


class Clone(Action):
    """Duplicates the object that triggered the event.

    Clones don't inherit event handlers, so a clone-on-bounce rule can't
    cascade into an unbounded chain. Give them a fresh random direction to get
    the "one ball becomes hundreds" effect.
    """

    def __init__(
        self,
        count: int = 1,
        *,
        spread: float = 360.0,
        speed: float | None = None,
        max_objects: int = 2000,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.count = count
        self.spread = spread
        """Angular spread in degrees the clones are launched across."""

        self.speed = speed
        """Speed for the clones, or ``None`` to keep the original's."""

        self.max_objects = max_objects
        """Safety ceiling so a runaway rule can't exhaust memory."""

    def apply(self, event: Event) -> None:
        """Spawn the configured number of copies."""
        scene, source = event.scene, event.source
        if scene is None or len(scene.objects) >= self.max_objects:
            return
        rng = scene.random
        base = source.velocity.angle
        speed = self.speed if self.speed is not None else source.speed
        for _ in range(self.count):
            angle = base + rng.uniform(-self.spread / 2.0, self.spread / 2.0)
            twin = source.clone()
            twin.velocity = Vec2.polar(angle, speed)
            scene.spawn(twin)


class Spawn(Action):
    """Creates new objects from a factory when the event fires."""

    def __init__(
        self,
        factory: Callable[[Event], object],
        count: int = 1,
        max_objects: int = 2000,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.factory = factory
        self.count = count
        self.max_objects = max_objects

    def apply(self, event: Event) -> None:
        """Build and add the new objects."""
        scene = event.scene
        if scene is None:
            return
        for _ in range(self.count):
            if len(scene.objects) >= self.max_objects:
                return
            scene.spawn(self.factory(event))


class Destroy(Action):
    """Removes an object: the event's source, or a specific one you name."""

    def __init__(self, target=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.target = target
        """The object to remove, or ``None`` to remove the event's source."""

    def apply(self, event: Event) -> None:
        """Mark the target for removal."""
        target = self.target if self.target is not None else event.source
        if target is not None:
            target.destroy()


class PopRing(Action):
    """Removes the innermost live ring of a :class:`RingStack`.

    This is the multi-ring escape effect: each escape opens up the next layer.
    """

    def __init__(self, stack, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stack = stack

    def apply(self, event: Event) -> None:
        """Pop one ring off the stack."""
        self.stack.pop()


class Stop(Action):
    """Ends the render."""

    def __init__(self, immediate: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.immediate = immediate

    def apply(self, event: Event) -> None:
        """Ask the scene to stop."""
        if event.scene is not None:
            event.scene.stop(immediate=self.immediate)


class Emit(Action):
    """Fires another event, so rules can be chained together."""

    def __init__(self, name: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.name = name

    def apply(self, event: Event) -> None:
        """Emit the named event on the same source."""
        if event.source is not None:
            event.source.emit(self.name, origin=event.name)


class MoveTo(Action):
    """Repositions an object, useful for resetting after an escape."""

    def __init__(self, position: Vec2Like = (0.0, 0.0), target=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.position = Vec2.of(position)
        self.target = target

    def apply(self, event: Event) -> None:
        """Move the target to the configured position."""
        obj = self.target if self.target is not None else event.source
        obj.transform.position = self.position
