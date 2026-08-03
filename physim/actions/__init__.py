"""Built-in actions you can attach to any event.

Actions are composable and can be rate-limited or made probabilistic::

    ball.on(Bounce, Grow(2, max_size=120))
    ball.on(Bounce, SpeedUp(1.05, max_speed=3000))
    ball.on(Bounce, Clone(1, chance=0.25))
    ball.on(Escape, Stop())

Plain callables work too, so nothing here is mandatory.
"""

from .base import Action, After, Custom, Sequence
from .lifecycle import Clone, Destroy, Emit, MoveTo, PopRing, Spawn, Stop
from .motion import Grow, Impulse, Reverse, SetSpeed, Shrink, SlowDown, SpeedUp, Teleport
from .sound import PitchByImpact, PlayMelody, PlayNote, PlaySound
from .visual import ChangeColor, Flash, RandomColor, SetOpacity, SetText

__all__ = [
    "Action",
    "After",
    "ChangeColor",
    "Clone",
    "Custom",
    "Destroy",
    "Emit",
    "Flash",
    "Grow",
    "Impulse",
    "MoveTo",
    "PitchByImpact",
    "PlayMelody",
    "PlayNote",
    "PlaySound",
    "PopRing",
    "RandomColor",
    "Reverse",
    "Sequence",
    "SetOpacity",
    "SetSpeed",
    "SetText",
    "Shrink",
    "SlowDown",
    "Spawn",
    "SpeedUp",
    "Stop",
    "Teleport",
]
