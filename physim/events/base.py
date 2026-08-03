"""Event objects and the dispatcher that routes them to handlers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Union

#: a handler is either a plain callable or an Action instance
Handler = Union[Callable[["Event"], Any], "ActionLike"]


class ActionLike:
    """Anything with a ``run`` method can be attached to an event."""

    def run(self, event: Event) -> None:
        """Perform this action in response to ``event``."""
        raise NotImplementedError


@dataclass
class Event:
    """Something that happened during the simulation.

    Handlers receive the event itself, which carries the object it happened to,
    the scene, and whatever payload the event type provides.
    """

    name: str
    source: Any = None
    """The object the event happened to."""

    scene: Any = None
    time: float = 0.0
    """Scene time in seconds when the event fired."""

    data: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Read a payload value with a fallback."""
        return self.data.get(key, default)


class EventBus:
    """Routes events to the handlers registered for them.

    Handlers may be plain callables taking the event, or objects with a ``run``
    method such as the built-in actions.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}
        self.fired: int = 0
        """Total events dispatched, surfaced in the debug stats."""

    def on(self, name: str, handler: Handler) -> Handler:
        """Register ``handler`` for events called ``name``."""
        self._handlers.setdefault(name, []).append(handler)
        return handler

    def off(self, name: str, handler: Handler | None = None) -> None:
        """Remove one handler, or every handler for ``name``."""
        if handler is None:
            self._handlers.pop(name, None)
            return
        handlers = self._handlers.get(name)
        if handlers and handler in handlers:
            handlers.remove(handler)

    def has(self, name: str) -> bool:
        """Whether anything is listening for ``name``."""
        return bool(self._handlers.get(name))

    def emit(self, event: Event) -> None:
        """Dispatch an event to every handler registered for its name."""
        self.fired += 1
        handlers = self._handlers.get(event.name)
        if not handlers:
            return
        for handler in list(handlers):
            if isinstance(handler, ActionLike):
                handler.run(event)
            elif callable(handler):
                handler(event)
            else:
                raise TypeError(f"handler for {event.name!r} is neither callable nor an action")

    def clear(self) -> None:
        """Drop every registered handler."""
        self._handlers.clear()
