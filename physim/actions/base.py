"""The action protocol and helpers shared by every built-in action."""

from __future__ import annotations

from collections.abc import Callable

from ..events import ActionLike, Event


class Action(ActionLike):
    """Something that happens in response to an event.

    Actions are composable: attach as many as you like to the same event, and
    they run in the order they were attached.

    >>> ball.on(Bounce, Grow(2))
    >>> ball.on(Bounce, SpeedUp(1.05))
    """

    #: only run every nth time the event fires
    every: int = 1

    def __init__(self, every: int = 1, chance: float = 1.0) -> None:
        self.every = max(1, every)
        self.chance = chance
        """Probability from 0 to 1 that the action runs when triggered."""

        self._count = 0

    def run(self, event: Event) -> None:
        """Apply rate limiting and randomness, then perform the action."""
        self._count += 1
        if self._count % self.every:
            return
        if self.chance < 1.0:
            rng = event.scene.random if event.scene else None
            roll = rng.random() if rng else 1.0
            if roll > self.chance:
                return
        self.apply(event)

    def apply(self, event: Event) -> None:
        """Perform the action. Subclasses implement this."""
        raise NotImplementedError


class Custom(Action):
    """Wraps a plain callable so it gains ``every`` and ``chance`` support."""

    def __init__(self, fn: Callable[[Event], None], **kwargs) -> None:
        super().__init__(**kwargs)
        self.fn = fn

    def apply(self, event: Event) -> None:
        """Call the wrapped function with the event."""
        self.fn(event)


class Sequence(Action):
    """Runs several actions in order as one."""

    def __init__(self, *actions: Action, **kwargs) -> None:
        super().__init__(**kwargs)
        self.actions = list(actions)

    def apply(self, event: Event) -> None:
        """Run each action in turn."""
        for action in self.actions:
            action.run(event)


class After(Action):
    """Runs an action only once a number of triggers have gone by."""

    def __init__(self, count: int, action: Action, **kwargs) -> None:
        super().__init__(**kwargs)
        self.count = count
        self.action = action
        self._seen = 0

    def apply(self, event: Event) -> None:
        """Count triggers and delegate once the threshold is passed."""
        self._seen += 1
        if self._seen >= self.count:
            self.action.run(event)
