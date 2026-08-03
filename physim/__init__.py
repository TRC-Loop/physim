"""physim: offline-rendered physics animations.

Builds the bouncing/growing object videos common on social media, rendering
every frame offline instead of capturing a live simulation, so the exported
file never stutters or drops frames however many objects are on screen.

>>> from physim import Scene, Circle, HollowCircle, RGBCycle
>>> class Bounce(Scene):
...     def construct(self):
...         self.add(HollowCircle(radius=400))
...         self.add(Circle(radius=20, fill=RGBCycle(), velocity=(220, 80)))
...         self.run(seconds=10)

Then render it::

    physim render scene.py Bounce
"""

from importlib.metadata import PackageNotFoundError, version

from . import easing, events, plugins, presets
from .color import (
    Color,
    ColorSequence,
    DynamicColor,
    Fade,
    Gradient,
    Paint,
    RGBCycle,
    Texture,
)
from .config import AudioConfig, DebugConfig, RenderConfig
from .events import (
    ANIMATION_END,
    BOUNCE,
    COLLISION,
    ESCAPE,
    FRAME,
    OFFSCREEN,
    SPAWN,
    TIMER,
    Bounce,
    Collision,
    Event,
    EventBus,
    Frame,
    Offscreen,
    Timer,
)
from .events import Escape as Escape
from .objects import (
    Body,
    Boundary,
    Circle,
    Hexagon,
    HollowCircle,
    HollowRect,
    Pentagon,
    Polygon,
    Rect,
    RingStack,
    SceneObject,
    Square,
    Star,
    Text,
    Triangle,
)
from .physics import Engine, PhysicsParams
from .scene import Scene
from .stats import Stats
from .transform import Transform
from .types import Resolution, Size, Vec2

try:
    __version__ = version("physim")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "ANIMATION_END",
    "BOUNCE",
    "COLLISION",
    "ESCAPE",
    "FRAME",
    "OFFSCREEN",
    "SPAWN",
    "TIMER",
    "AudioConfig",
    "Body",
    "Boundary",
    "Bounce",
    "Circle",
    "Collision",
    "Color",
    "ColorSequence",
    "DebugConfig",
    "DynamicColor",
    "Engine",
    "Escape",
    "Event",
    "EventBus",
    "Fade",
    "Frame",
    "Gradient",
    "Hexagon",
    "HollowCircle",
    "HollowRect",
    "Offscreen",
    "Paint",
    "Pentagon",
    "PhysicsParams",
    "Polygon",
    "RGBCycle",
    "Rect",
    "RenderConfig",
    "Resolution",
    "RingStack",
    "Scene",
    "SceneObject",
    "Size",
    "Square",
    "Star",
    "Stats",
    "Text",
    "Texture",
    "Timer",
    "Transform",
    "Triangle",
    "Vec2",
    "__version__",
    "easing",
    "events",
    "plugins",
    "presets",
]


def __getattr__(name: str):
    """Expose optional submodules lazily so importing physim stays cheap."""
    if name in ("colors", "actions", "audio", "effects"):
        import importlib

        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
