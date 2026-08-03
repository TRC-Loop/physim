"""Actions that change how an object looks."""

from __future__ import annotations

from ..color import Color, ColorSequence, Paint
from ..events import Event
from .base import Action


class ChangeColor(Action):
    """Sets an object's fill to a new color.

    Passing a :class:`ColorSequence` steps to its next entry on every trigger,
    which is how per-bounce color changes are built.
    """

    def __init__(self, color: Paint | ColorSequence, target=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.color = color
        self.target = target

    def apply(self, event: Event) -> None:
        """Assign the next color to the target."""
        obj = self.target if self.target is not None else event.source
        if isinstance(self.color, ColorSequence):
            obj.fill = self.color.advance()
        else:
            obj.fill = self.color


class RandomColor(Action):
    """Picks a random color, either from a list or anywhere on the hue wheel."""

    def __init__(self, choices: list[Paint] | None = None, target=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.choices = choices
        self.target = target

    def apply(self, event: Event) -> None:
        """Assign a random color to the target."""
        obj = self.target if self.target is not None else event.source
        rng = event.scene.random if event.scene else None
        if self.choices:
            obj.fill = rng.choice(self.choices) if rng else self.choices[0]
        else:
            hue = rng.uniform(0.0, 360.0) if rng else 0.0
            obj.fill = Color.oklch(0.72, 0.19, hue)


class Flash(Action):
    """Briefly brightens an object, fading back over a short window."""

    def __init__(self, duration: float = 0.12, amount: float = 0.35, **kwargs) -> None:
        super().__init__(**kwargs)
        self.duration = duration
        self.amount = amount

    def apply(self, event: Event) -> None:
        """Swap in a brightened fill and schedule the restore."""
        obj, scene = event.source, event.scene
        if scene is None:
            return
        original = obj.fill
        try:
            obj.fill = Color.of(original).lighten(self.amount)
        except (TypeError, ValueError):
            return
        deadline = scene.time + self.duration

        def restore(s, _dt) -> None:
            if s.time >= deadline:
                obj.fill = original
                s._on_frame.remove(restore)

        scene.each_frame(restore)


class SetOpacity(Action):
    """Sets an object's opacity."""

    def __init__(self, opacity: float = 1.0, target=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.opacity = opacity
        self.target = target

    def apply(self, event: Event) -> None:
        """Assign the opacity to the target."""
        obj = self.target if self.target is not None else event.source
        obj.transform.opacity = self.opacity


class SetText(Action):
    """Replaces a text object's contents, optionally from a counter."""

    def __init__(
        self, text: str | None = None, target=None, template: str | None = None, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.text = text
        self.template = template
        """A format string receiving ``event``, ``scene`` and ``count``."""

        self.target = target
        self._count = 0

    def apply(self, event: Event) -> None:
        """Update the target text object."""
        obj = self.target if self.target is not None else event.source
        self._count += 1
        if self.template is not None:
            obj.set_text(self.template.format(event=event, scene=event.scene, count=self._count))
        elif self.text is not None:
            obj.set_text(self.text)
