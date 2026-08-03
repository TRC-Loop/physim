"""The scene: holds objects, steps the simulation, and drives rendering."""

from __future__ import annotations

import random
from collections.abc import Callable, Iterable, Iterator

from .config import AudioConfig, DebugConfig, RenderConfig
from .events import FRAME, Event, EventBus, Handler
from .objects import Body, SceneObject
from .physics import Engine, PhysicsParams
from .stats import Stats

#: a predicate that ends a run when it returns true
StopCondition = Callable[["Scene"], bool]

#: renders never run longer than this unless told otherwise
DEFAULT_MAX_SECONDS = 120.0


class Scene:
    """A simulation and everything in it.

    Subclass it and build your objects in :meth:`construct`, the way the CLI
    expects, or instantiate it directly and drive it yourself.

    >>> class Bounce(Scene):
    ...     def construct(self):
    ...         self.add(HollowCircle(radius=400), Circle(radius=20))
    ...         self.run(seconds=10)
    """

    def __init__(
        self,
        config: RenderConfig | None = None,
        *,
        physics: PhysicsParams | str | None = None,
        debug: DebugConfig | bool | None = None,
        audio: AudioConfig | None = None,
        seed: int | None = 42,
    ) -> None:
        self.config = config or RenderConfig()
        self.debug = self._coerce_debug(debug)
        self.audio_config = audio or AudioConfig()
        self.objects: list[SceneObject] = []
        self.events = EventBus()
        self.stats = Stats()

        self.seed = seed
        self.random = random.Random(seed)
        """Seeded generator. Use it instead of the global one to stay reproducible."""

        self.engine = Engine(self._coerce_physics(physics))
        self.time = 0.0
        """Scene time in seconds."""

        self.frame = 0
        self._stopping = False
        self._pending: list[SceneObject] = []
        self._frames_target: int | None = None
        self._on_frame: list[Callable[[Scene, float], None]] = []
        self._sounds: list = []

    @staticmethod
    def _coerce_debug(debug: DebugConfig | bool | None) -> DebugConfig:
        """Accept a bool as a shorthand for enabling the defaults."""
        if isinstance(debug, DebugConfig):
            return debug
        return DebugConfig(enabled=bool(debug))

    @staticmethod
    def _coerce_physics(physics: PhysicsParams | str | None) -> PhysicsParams:
        """Accept a preset name, a params object, or nothing."""
        if isinstance(physics, PhysicsParams):
            return physics
        if isinstance(physics, str):
            from .presets import physics as load

            return load(physics)
        return PhysicsParams()

    @property
    def params(self) -> PhysicsParams:
        """The physics parameters in use."""
        return self.engine.params

    @property
    def bodies(self) -> list[Body]:
        """Every object the engine simulates."""
        return [o for o in self.objects if isinstance(o, Body) and o.alive]

    @property
    def boundaries(self) -> list:
        """Every object acting as a wall."""
        return [o for o in self.objects if o.is_boundary and o.alive]

    def construct(self) -> None:
        """Build the scene. Subclasses override this."""

    def add(self, *objects: SceneObject | Iterable[SceneObject]) -> Scene:
        """Add objects to the scene, returning self so calls can chain."""
        for item in objects:
            if isinstance(item, SceneObject):
                self._attach(item)
            else:
                for obj in item:
                    self._attach(obj)
        return self

    def _attach(self, obj: SceneObject) -> None:
        """Bind an object to this scene and announce it."""
        obj.scene = self
        self.objects.append(obj)
        obj.emit("spawn")

    def spawn(self, obj: SceneObject) -> SceneObject:
        """Queue an object to be added after the current frame finishes.

        Safe to call from inside an event handler, where mutating the object
        list directly would disturb the iteration in progress.
        """
        self._pending.append(obj)
        return obj

    def remove(self, obj: SceneObject) -> None:
        """Mark an object for removal at the end of the frame."""
        obj.destroy()

    def clear(self) -> None:
        """Remove every object."""
        for obj in list(self.objects):
            obj.alive = False
        self.objects.clear()

    def on(self, event: str, handler: Handler) -> Handler:
        """Attach a handler to a scene-wide event."""
        return self.events.on(event, handler)

    def emit(self, name: str, **data) -> Event:
        """Fire a scene-wide event."""
        event = Event(name=name, source=self, scene=self, time=self.time, data=data)
        self.events.emit(event)
        return event

    def each_frame(self, fn: Callable[[Scene, float], None]) -> Callable:
        """Register a callback invoked once per frame with the scene and dt."""
        self._on_frame.append(fn)
        return fn

    def play_sound(self, sound) -> None:
        """Queue a sound to be mixed into the audio track at the current time."""
        self._sounds.append((self.time, sound))

    def stop(self, immediate: bool = False) -> None:
        """End the run.

        Callable from anywhere, including event handlers. The current frame is
        finished first unless ``immediate`` is set.
        """
        self._stopping = True
        if immediate:
            raise StopIteration

    @property
    def stopping(self) -> bool:
        """Whether something has asked the run to end."""
        return self._stopping

    def step(self, dt: float) -> None:
        """Advance the simulation by ``dt`` seconds without rendering."""
        import time as _time

        started = _time.perf_counter()
        bodies, boundaries = self.bodies, self.boundaries
        self.engine.step(bodies, boundaries, dt)

        for obj in list(self.objects):
            obj.update(dt)
        for fn in list(self._on_frame):
            fn(self, dt)

        self.time += dt
        self.frame += 1
        self._flush()

        self.stats.physics_time = _time.perf_counter() - started
        self.stats.object_count = len(self.objects)
        self.stats.collision_count = self.engine.collisions_this_step
        self.stats.total_collisions += self.engine.collisions_this_step
        self.stats.scene_time = self.time
        self.stats.events_fired = self.events.fired

    def _flush(self) -> None:
        """Apply queued additions and drop dead objects."""
        if self._pending:
            for obj in self._pending:
                self._attach(obj)
            self._pending.clear()
        if any(not o.alive for o in self.objects):
            self.objects = [o for o in self.objects if o.alive]

    def run(self, seconds: float = 10.0) -> Scene:
        """Set the run length in seconds. The renderer performs the work."""
        self._frames_target = max(1, round(seconds * self.config.fps))
        self._stop_condition: StopCondition | None = None
        return self

    def run_until(
        self,
        condition: StopCondition | str,
        max_seconds: float = DEFAULT_MAX_SECONDS,
    ) -> Scene:
        """Run until a predicate returns true or an event fires.

        ``condition`` is either a callable taking the scene, or an event name
        that ends the run the first time it fires.
        """
        self._frames_target = max(1, round(max_seconds * self.config.fps))
        if isinstance(condition, str):
            self.on(condition, lambda _event: self.stop())
            self._stop_condition = None
        else:
            self._stop_condition = condition
        return self

    @property
    def total_frames(self) -> int | None:
        """Planned frame count, or ``None`` when :meth:`run` was never called."""
        return self._frames_target

    def frames(self) -> Iterator[int]:
        """Yield frame indices, stepping the simulation between each one."""
        target = self._frames_target or round(10 * self.config.fps)
        dt = self.config.frame_duration
        condition = getattr(self, "_stop_condition", None)
        self.stats.total_frames = target
        for index in range(target):
            self.step(dt)
            self.emit(FRAME, index=index)
            yield index
            if self._stopping or (condition is not None and condition(self)):
                break

    def build(self) -> Scene:
        """Load any installed addons, then run :meth:`construct` once."""
        if not getattr(self, "_constructed", False):
            from .plugins import load

            load()
            self.construct()
            self._constructed = True
        return self

    def render(self, **overrides):
        """Render this scene to a file and return the output path."""
        from .export import render_scene

        return render_scene(self, **overrides)

    def preview(self, **overrides) -> None:
        """Play this scene in a live preview window."""
        from .export import preview_scene

        preview_scene(self, **overrides)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} objects={len(self.objects)} t={self.time:.2f}s>"
