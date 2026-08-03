"""The base class every scene object derives from."""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Any

from ..color import Paint
from ..events import Event, EventBus, Handler
from ..transform import Transform
from ..types import Vec2, Vec2Like

if TYPE_CHECKING:
    from ..scene import Scene

_ids = itertools.count(1)


class SceneObject:
    """Anything that can live in a scene and be drawn.

    Subclasses implement :meth:`draw` and, when they take part in the
    simulation, set :attr:`physical` and provide a :attr:`collision_radius`.
    """

    #: whether the physics engine moves this object
    physical: bool = False

    #: whether this object acts as a wall for others
    is_boundary: bool = False

    def __init__(
        self,
        pos: Vec2Like = (0.0, 0.0),
        *,
        fill: Paint | None = "#ffffff",
        stroke: Paint | None = None,
        stroke_width: float = 0.0,
        opacity: float = 1.0,
        rotation: float = 0.0,
        scale: float | Vec2Like = 1.0,
        z: int = 0,
        visible: bool = True,
        name: str | None = None,
    ) -> None:
        self.id = next(_ids)
        self.name = name or f"{type(self).__name__}{self.id}"
        self.transform = Transform(position=Vec2.of(pos), rotation=rotation, opacity=opacity)
        self.transform.scale = Transform._coerce_scale(scale)
        self.fill = fill
        self.stroke = stroke
        self.stroke_width = stroke_width
        self.z = z
        """Draw order. Higher values are drawn on top."""

        self.visible = visible
        self.scene: Scene | None = None
        self.events = EventBus()
        self.alive = True
        self.age = 0.0
        """Seconds this object has existed."""

        self.data: dict[str, Any] = {}
        """Free-form storage for your own per-object state."""

        self.effects: list = []
        """Visual effects drawn around this object, see :mod:`physim.effects`."""

    @property
    def pos(self) -> Vec2:
        """Shorthand for the object's position."""
        return self.transform.position

    @pos.setter
    def pos(self, value: Vec2Like) -> None:
        self.transform.position = Vec2.of(value)

    @property
    def opacity(self) -> float:
        """Shorthand for the object's opacity."""
        return self.transform.opacity

    @opacity.setter
    def opacity(self, value: float) -> None:
        self.transform.opacity = value

    @property
    def collision_radius(self) -> float:
        """Radius used for broad-phase culling. Zero for non-colliding objects."""
        return 0.0

    def on(self, event: str, handler: Handler) -> Handler:
        """Attach a handler to one of this object's events."""
        return self.events.on(event, handler)

    def off(self, event: str, handler: Handler | None = None) -> None:
        """Detach a handler, or every handler for an event."""
        self.events.off(event, handler)

    def emit(self, name: str, **data) -> Event:
        """Fire an event on this object, then bubble it up to the scene."""
        event = Event(
            name=name,
            source=self,
            scene=self.scene,
            time=self.scene.time if self.scene else 0.0,
            data=data,
        )
        self.events.emit(event)
        if self.scene is not None:
            self.scene.events.emit(event)
        return event

    def update(self, dt: float) -> None:
        """Advance any non-physics state by ``dt`` seconds."""
        self.age += dt
        for effect in self.effects:
            effect.update(self, dt)

    def render(self, canvas, ctx) -> None:
        """Draw this object together with its effects."""
        for effect in self.effects:
            effect.draw_before(canvas, ctx, self)
        self.draw(canvas, ctx)
        for effect in self.effects:
            effect.draw_after(canvas, ctx, self)

    def draw(self, canvas, ctx) -> None:
        """Draw this object. ``ctx`` carries the renderer and current scene time."""
        raise NotImplementedError

    def add_effect(self, *effects) -> SceneObject:
        """Attach one or more visual effects, returning self so calls can chain."""
        self.effects.extend(effects)
        return self

    def destroy(self) -> None:
        """Mark this object for removal at the end of the current frame."""
        if self.alive:
            self.alive = False
            self.emit("destroy")

    def clone(self, **overrides) -> SceneObject:
        """Return an independent copy, with optional attribute overrides.

        Event handlers are intentionally not copied, so a cloned object doesn't
        inherit a clone-on-bounce rule and multiply without bound.
        """
        import copy

        twin = copy.copy(self)
        twin.id = next(_ids)
        twin.name = f"{self.name}_clone{twin.id}"
        twin.transform = self.transform.replace()
        twin.events = EventBus()
        twin.data = dict(self.data)
        twin.age = 0.0
        twin.alive = True
        for key, value in overrides.items():
            setattr(twin, key, value)
        return twin

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.name} at {self.pos}>"
