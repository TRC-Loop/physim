# physim for AI agents

Everything an agent needs to write a physim animation that renders correctly on
the first try. Read this end to end before writing a scene.

## What physim is

A Python library that renders "bouncing ball" style animations frame by frame,
offline, to MP4 or MKV. It is not real time: the whole timeline is simulated and
rasterized ahead of encoding, so output never drops frames regardless of object
count.

## Install

```bash
pip install physim[all]
```

If a feature errors with an install hint, that extra is missing. Check what is
available with `physim info`.

| Extra | Needed for |
| --- | --- |
| `cli` | the `physim` command |
| `preview` | `scene.preview()` and `physim preview` |
| `audio` | `Melody.from_midi()` only; tones and wav/mp3 need nothing extra |
| `expr` | `ParametricShape`, `ImplicitShape` |
| `presets` | `physim.colors`, named physics presets |
| `examples` | `python -m physim_examples` |
| `gpu` | `--backend gpu` |

## The mental model

1. Subclass `Scene`, build objects in `construct()`, end with `self.run(...)`.
2. Objects react to **events** by running **actions**.
3. Physics presets hold only physical constants. Anything that changes over
   time (growing, speeding up, cloning) is an action, never a preset.
4. Render with `scene.render()` or `physim render file.py SceneName`.

## Coordinates

**Centered and y-up, in pixels.** `(0, 0)` is the middle of the frame, `(0, 400)`
is 400px above center. This is the single most common source of mistakes: it is
not top-left, and y is not inverted.

Anywhere a point is expected, a plain tuple works: `pos=(0, 300)` and
`pos=Vec2(0, 300)` are identical.

Default frame is 1080x1080 at 30fps.

## Minimal correct scene

```python
from physim import Circle, HollowCircle, Scene


class Bouncy(Scene):
    """One ball bouncing inside a ring."""

    def construct(self) -> None:
        self.add(HollowCircle(radius=420, stroke="#ffffff"))
        self.add(Circle(radius=20, fill="#ff006e", velocity=(280, 60)))
        self.run(seconds=10)


if __name__ == "__main__":
    Bouncy().render()
```

```bash
physim render scene.py Bouncy
```

## Rule: size objects to the frame

Hardcoded radii break at other resolutions. Derive them:

```python
def construct(self) -> None:
    radius = min(self.config.width, self.config.height) * 0.42
    self.add(HollowCircle(radius=radius, stroke="#ffffff"))
```

## Objects

Physics bodies (they move and collide):

```python
Circle(radius=20, pos=(0, 0), velocity=(200, 50), fill="#ff006e")
Triangle(radius=25)          # Polygon with sides=3
Square(radius=25)
Pentagon(radius=25)
Hexagon(radius=25)
Polygon(radius=25, sides=7, corner_radius=4)
Star(radius=30, points=5, inner_ratio=0.5)
Rect(width=40, height=40, corner_radius=6)
```

Common body arguments: `velocity`, `mass`, `restitution` (per-object bounciness
override), `gravity_scale`, `fixed=True` (never moves but still blocks others).

Boundaries (walls, they do not move):

```python
HollowCircle(radius=420, thickness=8)
HollowCircle(radius=420, gap_degrees=30, gap_angle=90, rotation_speed=45)
HollowRect(width=800, height=800, corner_radius=20)
RingStack(count=6, inner_radius=120, spacing=55, gap_degrees=38,
          gap_step=55, rotation_speed=45)
```

Text:

```python
Text("hello", pos=(0, 300), size=90, bold=True, italic=False,
     underline=False, strikethrough=False, color="#ffffff",
     background="#16161f", background_opacity=0.85, align="center")
```

Update text with `text.set_text("new")`, which fires a `change` event.

Every object takes `z` (draw order, higher on top), `visible`, `opacity`,
`rotation`, `scale` and `name`.

## Fills

A fill is a color, a gradient, a texture, or a color that animates.

```python
from physim import Color, Gradient, RGBCycle, Texture, Fade, ColorSequence

fill="#ff0055"                                  # hex
fill=Color.rgb(255, 0, 85)
fill=Color.oklch(0.7, 0.2, 20)                  # also hsl, cmyk, lab, lch, oklab
fill=RGBCycle(speed=90)                         # cycles hue, perceptually even
fill=Fade(start="#000", end="#fff", duration=2)
fill=ColorSequence(colors=["#f00", "#0f0"], interval=0.5)
fill=Gradient(colors=["#ff0055", "#5500ff"], kind="linear", end=(0, 120))
fill=Texture("marble.png", fit="cover")         # tile, stretch, cover, contain
```

Objects also take `stroke` and `stroke_width`. For a hollow outline, set
`fill=None` and give a `stroke`.

Named colors need the presets extra:

```python
from physim import colors
colors.NEON_PINK
colors.palette("neon")     # list of Color
```

## Effects

Purely visual, they do not affect physics. Attach with `add_effect`.

```python
from physim.effects import Trail, Glow, Pulse, Spin, FadeIn

ball.add_effect(Trail(length=28, fade=0.6), Glow(strength=0.6))
ring.add_effect(Spin(speed=45))
```

`Trail` costs one draw call per recorded point. Above a few hundred objects,
drop it.

## Events

Attach handlers with `obj.on(event, handler)`. Events are plain strings, so
`Bounce` and `"bounce"` are the same.

| Event | Fires when | Payload |
| --- | --- | --- |
| `Bounce` | a body hits a boundary | `boundary`, `impact`, `normal`, `point` |
| `Collision` | two bodies hit each other | `other`, `impact` |
| `Escape` | a body leaves through a gap | `boundary` |
| `Spawn` | an object is added | |
| `Destroy` | an object is removed | |
| `Frame` | once per frame | `index` |

A handler is either an action or a plain callable taking the event:

```python
ball.on(Bounce, Grow(2))
ball.on(Bounce, lambda event: print(event["impact"]))
```

Fire your own events with `obj.emit("my_event", value=1)`.

## Actions

```python
from physim.actions import (
    Grow, Shrink, SpeedUp, SlowDown, SetSpeed, Impulse, Reverse, Teleport,
    Clone, Spawn, Destroy, PopRing, Stop, Emit, MoveTo,
    ChangeColor, RandomColor, Flash, SetOpacity, SetText,
    PlaySound, PlayNote, PlayMelody, PitchByImpact,
    Sequence, After, Custom,
)
```

Every action accepts `every=N` (run on every nth trigger) and `chance=0.0-1.0`
(run probabilistically, using the scene's seeded RNG).

```python
ball.on(Bounce, Grow(3, max_size=380))
ball.on(Bounce, SpeedUp(1.02, max_speed=2200))
ball.on(Bounce, Clone(1, spread=90, max_objects=400, every=3))
ball.on(Escape, Destroy())
ball.on(Escape, Stop())
```

`Clone` deliberately does not copy event handlers, so a clone-on-bounce rule
cannot cascade without bound. To give clones behavior, use a factory instead:

```python
def make_ball(self):
    ball = Circle(radius=16, fill=RGBCycle())
    ball.on(Bounce, self.melody.next_note())
    return ball

ball.on(Escape, Custom(lambda e: e.scene.spawn(self.make_ball())))
```

**Always use `scene.spawn(obj)` from inside a handler**, never `scene.add(obj)`.
`spawn` queues the object until the frame finishes; `add` mutates the list being
iterated.

## Physics

```python
Scene(physics="classic")
Scene(physics=PhysicsParams(gravity=900, restitution=1.0, damping=1.0))
```

Presets (need the presets extra): `classic`, `bouncy`, `zero_g`, `chaos`,
`floaty`, `heavy`, `orbit`, `jelly`, `molasses`, `pinball`. `default` and
`custom` always work without it.

`PhysicsParams` fields: `gravity`, `gravity_direction`, `restitution`,
`damping`, `friction`, `attraction`, `attraction_point`, `max_speed`,
`min_speed`, `substeps`, `ball_collisions`.

`ball_collisions` defaults to **off**. Turn it on only when you want pile-ups;
it costs real time at high counts.

## Ending a run

```python
self.run(seconds=10)                                     # fixed length
self.run_until(Escape, max_seconds=60)                   # until an event
self.run_until(lambda s: len(s.bodies) > 500, max_seconds=30)
scene.stop()                                             # from anywhere
```

`run_until` always needs `max_seconds` so a render cannot hang. `stop()`
finishes the current frame, so the triggering frame is still written.

## Sound

Audio is synthesized into a track and muxed into the video, sample-accurate to
the physics regardless of render speed.

```python
from physim.audio import Melody, note, Tone
from physim.actions import PlayNote, PitchByImpact

melody = Melody.from_notes("C4 E4 G4 C5", duration=0.25, waveform="triangle")
melody = Melody.from_midi("tune.mid")          # needs the audio extra
ball.on(Bounce, melody.next_note())            # next note per bounce

ball.on(Bounce, PlayNote("C4", duration=0.2))
ball.on(Bounce, PitchByImpact(base="C3", span=24))   # harder hit, higher note
```

Share **one** `Melody` across every ball so the tune advances in sequence rather
than each ball restarting it.

Waveforms: `sine`, `square`, `triangle`, `saw`, `noise`.

## Debugging

```python
scene = MyScene(debug=True)
scene.stats.fps, scene.stats.frametime_ms, scene.stats.object_count
scene.stats.as_dict()
```

`--debug` overlays frametime, fps, objects, collisions, timings and ETA, and
prints a summary table when the render finishes.

## CLI

```bash
physim render scene.py [Scene]
physim list scene.py
physim preview scene.py
physim info
```

| Flag | Meaning |
| --- | --- |
| `-o, --output` | output path |
| `-f, --format` | `mp4` or `mkv` |
| `-r, --resolution` | `square`, `vertical`, `landscape`, `hd`, `fhd`, `4k`, or `1080x1920` |
| `--fps` | framerate |
| `-s, --seconds` | override scene length |
| `-p, --physics` | physics preset |
| `--seed` | random seed |
| `--motion-blur N` | sub-frame samples |
| `-b, --backend` | `auto`, `cpu`, `gpu` |
| `--hardware-encode` | platform hardware encoder |
| `-d, --debug` | stats overlay |
| `--audio-file` | also write audio separately |
| `--audio-only` / `--no-audio` | audio handling |
| `-q, --quiet` | hide the progress bar |

The scene name is optional when the file defines exactly one scene.

## Reproducibility

Scenes are seeded (`seed=42` by default), so a render is repeatable. Use
`self.random` inside scenes, never the global `random` module, or renders stop
being reproducible.

## Performance guide

Per frame at 1080x1980, roughly:

| balls | frame time |
| --- | --- |
| 1,000 | ~19 ms |
| 5,000 | ~76 ms |
| 16,000 | ~266 ms |

If a render is slow: drop `Trail` at high object counts, leave
`ball_collisions` off, lower `substeps`, avoid `motion_blur` (it multiplies
render cost per frame), and render a short `--seconds` while iterating.

Growth mechanics compound. If each escape spawns more than it destroys, the
count grows exponentially and a long `max_seconds` can produce an enormous
render. Always cap with `max_objects` on `Clone`, or a `run_until` predicate.

## Mistakes to avoid

- Using top-left coordinates. Origin is the center and y points up.
- `scene.add()` inside an event handler. Use `scene.spawn()`.
- Hardcoding radii instead of deriving them from `self.config`.
- Expecting `Clone` to copy handlers. It does not, by design.
- Creating a `Melody` per ball. Share one.
- Putting growth or speed-up into a physics preset. Those are actions.
- `run_until` without `max_seconds`.
- Trails on thousands of objects.

## Complete example

```python
"""Balls escaping a ring through a spinning gap, playing a melody."""

from physim import Circle, Color, HollowCircle, Scene
from physim.actions import Custom
from physim.audio import Melody
from physim.effects import Trail
from physim.events import Bounce, Escape

MAX_BALLS = 200


class Escaping(Scene):
    """Each escape replaces one ball with two, so the swarm grows."""

    def construct(self) -> None:
        self.melody = Melody.from_notes(
            "E5 D#5 E5 D#5 E5 B4 D5 C5 A4", duration=0.25, waveform="triangle"
        )
        self.spawned = 0

        radius = min(self.config.width, self.config.height) * 0.42
        self.add(
            HollowCircle(
                radius=radius,
                stroke="#ffffff",
                thickness=9,
                gap_degrees=30,
                rotation_speed=50,
            )
        )
        self.add(self.new_ball(velocity=(300, 120)))
        self.run_until(lambda s: len(s.bodies) >= MAX_BALLS, max_seconds=120)

    def new_ball(self, velocity=None) -> Circle:
        """Build a ball with its own color and the shared melody."""
        from physim import Vec2

        self.spawned += 1
        ball = Circle(
            radius=18,
            velocity=velocity
            or Vec2.polar(self.random.uniform(0, 360), self.random.uniform(260, 380)),
            fill=Color.oklch(0.75, 0.2, (self.spawned * 47) % 360),
        )
        if self.spawned <= 300:
            ball.add_effect(Trail(length=30, fade=0.55))
        ball.on(Bounce, self.melody.next_note())
        ball.on(Escape, Custom(self.on_escape))
        return ball

    def on_escape(self, event) -> None:
        """Replace the escaped ball with two new ones."""
        event.source.destroy()
        for _ in range(2):
            self.spawn(self.new_ball())


if __name__ == "__main__":
    Escaping(physics="classic").render()
```

## Extending physim

Addons register through the `physim.plugins` entry point:

```toml
[project.entry-points."physim.plugins"]
sparkles = "physim_sparkles:setup"
```

```python
from physim.plugins import register_action, register_easing

def setup(registry):
    register_easing("sparkle", lambda t: t**0.5)
    register_action("Sparkle", Sparkle)
```

## Verifying output

Do not assume a render is correct because it did not crash. Check it:

```python
import av, numpy as np

with av.open("out.mp4") as container:
    frames = [f.to_ndarray(format="rgb24") for f in container.decode(video=0)]
    print("frames:", len(frames))

with av.open("out.mp4") as container:
    print("audio streams:", len(container.streams.audio))

moved = sum(
    1 for i in range(1, len(frames)) if not np.array_equal(frames[i], frames[i - 1])
)
print("frames that changed:", moved)
```

An all-black output usually means objects were placed outside the frame, which
almost always traces back to the coordinate system.
