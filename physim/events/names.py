"""Built-in event names.

These are plain strings, so ``ball.on(Bounce, ...)`` and
``ball.on("bounce", ...)`` are equivalent. Any other string works too and
becomes a custom event you can emit yourself.
"""

from __future__ import annotations

#: an object hit a boundary wall
BOUNCE = "bounce"

#: two objects hit each other
COLLISION = "collision"

#: an object left the playfield through a gap or cutout
ESCAPE = "escape"

#: an object was added to the scene
SPAWN = "spawn"

#: an object was removed from the scene
DESTROY = "destroy"

#: fires once per rendered frame
FRAME = "frame"

#: fires when a scheduled timer elapses
TIMER = "timer"

#: an object moved fully outside the frame
OFFSCREEN = "offscreen"

#: an animation reached its end
ANIMATION_END = "animation_end"

# aliases matching the capitalized style used in scene files
Bounce = BOUNCE
Collision = COLLISION
Escape = ESCAPE
Spawn = SPAWN
Destroy = DESTROY
Frame = FRAME
Timer = TIMER
Offscreen = OFFSCREEN
AnimationEnd = ANIMATION_END

#: every built-in name, for validation and docs
BUILTIN = (
    BOUNCE,
    COLLISION,
    ESCAPE,
    SPAWN,
    DESTROY,
    FRAME,
    TIMER,
    OFFSCREEN,
    ANIMATION_END,
)
