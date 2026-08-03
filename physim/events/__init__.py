"""The event system.

Attach handlers to any object or to the scene itself. A handler is either a
plain callable receiving the :class:`Event`, or one of the built-in actions
from :mod:`physim.actions`.

>>> ball.on(Bounce, SpeedUp(1.05))
>>> ball.on(Bounce, lambda e: print(e.time))
"""

from .base import ActionLike, Event, EventBus, Handler
from .names import (
    ANIMATION_END,
    BOUNCE,
    BUILTIN,
    COLLISION,
    DESTROY,
    ESCAPE,
    FRAME,
    OFFSCREEN,
    SPAWN,
    TIMER,
    AnimationEnd,
    Bounce,
    Collision,
    Frame,
    Offscreen,
    Timer,
)
from .names import Destroy as DestroyEvent
from .names import Escape as Escape
from .names import Spawn as SpawnEvent

__all__ = [
    "ANIMATION_END",
    "BOUNCE",
    "BUILTIN",
    "COLLISION",
    "DESTROY",
    "ESCAPE",
    "FRAME",
    "OFFSCREEN",
    "SPAWN",
    "TIMER",
    "ActionLike",
    "AnimationEnd",
    "Bounce",
    "Collision",
    "DestroyEvent",
    "Escape",
    "Event",
    "EventBus",
    "Frame",
    "Handler",
    "Offscreen",
    "SpawnEvent",
    "Timer",
]
