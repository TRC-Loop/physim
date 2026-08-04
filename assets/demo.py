"""The three scenes stitched together into the README demo.

Each runs for five seconds and shows off a different part of the library.

    physim render assets/demo.py Bouncing
    python assets/demo.py          # renders all three and builds demo.gif
"""

from physim import (
    Circle,
    Color,
    HollowCircle,
    PhysicsParams,
    Polygon,
    RGBCycle,
    RingStack,
    Scene,
    Text,
    Vec2,
)
from physim.actions import Clone, Custom, Grow, PopRing, SpeedUp
from physim.effects import Glow, Spin, Trail
from physim.events import Bounce, Escape

SECONDS = 5.0


class Bouncing(Scene):
    """A colour-cycling ball with a trail, bouncing in a ring."""

    def construct(self) -> None:
        """Build the scene."""
        radius = min(self.config.width, self.config.height) * 0.42
        self.add(HollowCircle(radius=radius, stroke="#ffffff", thickness=7))

        ball = Circle(radius=radius * 0.09, fill=RGBCycle(speed=140), velocity=(320, 140))
        ball.add_effect(Trail(length=26, fade=0.6), Glow(strength=0.5))
        self.add(ball)
        self.run(seconds=SECONDS)


class Growing(Scene):
    """A ball that grows and speeds up on every bounce."""

    def construct(self) -> None:
        """Build the scene."""
        radius = min(self.config.width, self.config.height) * 0.42
        self.add(HollowCircle(radius=radius, stroke="#ffffff", thickness=7))

        ball = Circle(radius=radius * 0.05, fill="#39ff14", velocity=(340, 120))
        ball.add_effect(Trail(length=22, fade=0.45), Glow(strength=0.3))
        ball.on(Bounce, Grow(radius * 0.028, max_size=radius * 0.34))
        ball.on(Bounce, SpeedUp(1.04, max_speed=1600))
        self.add(ball)
        self.run(seconds=SECONDS)


class Escaping(Scene):
    """Balls working outward through rings with spinning gaps, multiplying."""

    def construct(self) -> None:
        """Build the scene."""
        radius = min(self.config.width, self.config.height) * 0.42
        stack = RingStack(
            count=4,
            inner_radius=radius * 0.34,
            spacing=radius * 0.22,
            gap_degrees=44,
            gap_step=70,
            rotation_speed=110,
            thickness=6,
            stroke="#ffffff",
        )
        self.add(stack)

        ball = Circle(radius=radius * 0.055, fill="#ff006e", velocity=(300, 180))
        ball.add_effect(Trail(length=20, fade=0.6), Glow(strength=0.6))
        ball.on(Bounce, Clone(1, spread=120, max_objects=60, every=6))
        ball.on(Escape, PopRing(stack))
        self.add(ball)

        counter = Text(
            "1",
            pos=(0, -radius * 1.1),
            size=self.config.width * 0.09,
            bold=True,
            color="#ffffff",
            opacity=0.55,
            z=100,
        )
        self.add(counter)

        @self.each_frame
        def update_counter(scene, _dt) -> None:
            """Keep the label in step with the ball count."""
            counter.set_text(str(len(scene.bodies)))

        self.run(seconds=SECONDS)


class Tiny(Scene):
    """A tiny ball in a big ring, growing slowly, with a faint watermark.

    Sizes are proportional to the frame so it looks the same at any resolution.
    """

    #: a ball in a round arena sheds vertical motion and starts rolling along
    #: the wall, so every bounce is topped back up to at least this speed
    MIN_SPEED = 620.0

    def construct(self) -> None:
        """Build the scene."""
        # fully elastic, so bounces never decay into a roll
        self.engine.params = PhysicsParams(gravity=850, restitution=1.0, damping=1.0)

        radius = min(self.config.width, self.config.height) * 0.46
        self.add(HollowCircle(radius=radius, stroke="#ffffff", thickness=5))

        colour = Color("#ff006e")
        ball = Circle(
            radius=radius * 0.015,
            velocity=(240, 90),
            fill=colour,
            stroke=colour.lighten(0.25),
            stroke_width=2,
        )
        ball.add_effect(Trail(length=34, fade=0.5))
        ball.on(Bounce, Grow(radius * 0.02, max_size=radius * 0.75))
        ball.on(Bounce, Custom(self.keep_it_lively))
        self.add(ball)

        self.add(
            Text(
                "@trcloop",
                pos=(0, -radius * 1.12),
                size=self.config.width * 0.05,
                font="Safiro",
                color="#ffffff",
                opacity=0.18,
                z=100,
            )
        )
        self.run(seconds=SECONDS)

    @classmethod
    def keep_it_lively(cls, event) -> None:
        """Top a bounce back up to a minimum speed, and nudge it off the wall."""
        ball = event.source
        if ball.speed < cls.MIN_SPEED:
            ball.speed = cls.MIN_SPEED
        normal = event.get("normal")
        if normal is not None and ball.velocity.dot(normal) < cls.MIN_SPEED * 0.35:
            ball.velocity = (ball.velocity + normal * (cls.MIN_SPEED * 0.45)).clamped(
                cls.MIN_SPEED * 1.3
            )


class Bloom(Scene):
    """Three bodies orbiting a central attractor, drawing spirograph trails.

    No walls and no bouncing: gravity points inward instead of down, so each
    body falls around the centre forever and its trail traces the orbit.
    """

    def construct(self) -> None:
        """Build the scene."""
        short = min(self.config.width, self.config.height)
        self.engine.params = PhysicsParams(
            gravity=0,
            damping=1.0,
            attraction=short**2 * 30,
            substeps=8,
        )

        # a still mandala for the orbits to move against; fixed so the
        # attractor does not pull the decoration into the middle
        for i in range(6):
            ring = Polygon(
                radius=short * (0.14 + i * 0.055),
                sides=3 + i,
                fill=None,
                stroke=Color.oklch(0.72, 0.17, i * 47),
                stroke_width=2,
                rotation=i * 11,
                fixed=True,
            )
            ring.add_effect(Spin(speed=16 if i % 2 else -16))
            self.add(ring)

        # each body gets a different orbit radius, so the trails interleave
        for i, (distance, speed, hue) in enumerate(
            ((0.20, 1.06, 20), (0.29, 0.94, 150), (0.38, 0.88, 285))
        ):
            offset = short * distance
            # circular orbit speed for this attractor, nudged off round
            orbital = (self.engine.params.attraction / offset) ** 0.5 * speed
            body = Circle(
                radius=short * 0.018,
                pos=Vec2.polar(i * 120, offset),
                velocity=Vec2.polar(i * 120 + 90, orbital),
                fill=Color.oklch(0.8, 0.2, hue),
            )
            body.add_effect(Trail(length=110, fade=0.85, every=1), Glow(strength=0.7))
            self.add(body)

        self.run(seconds=SECONDS)


DEMOS = (Bouncing, Growing, Escaping, Tiny, Bloom)


def render_frames(size: int, fps: int) -> list:
    """Render every demo scene and return one flat list of RGB frames."""
    from physim import RenderConfig
    from physim.render import Renderer

    frames = []
    for scene_class in DEMOS:
        config = RenderConfig(resolution=(size, size), fps=fps, background="#0b0b12")
        scene = scene_class(config, seed=7)
        scene.build()
        renderer = Renderer(config)
        for _ in scene.frames():
            frames.append(renderer.render(scene).copy())
        print(f"  {scene_class.__name__}: {len(frames)} frames so far")
    return frames


def build_gif(path="assets/demo.gif", size=380, fps=20) -> str:
    """Render every demo and stitch the frames into one looping gif.

    Two passes over the frames: the first builds a palette across the whole
    animation, the second maps every frame onto it. A gif written without that
    is several times larger and dithers badly on the gradients.
    """
    from fractions import Fraction
    from itertools import count

    import av
    import numpy as np

    frames = render_frames(size, fps)

    counter = count()

    def to_av(frame):
        """Wrap an RGB array as a timestamped av frame."""
        video = av.VideoFrame.from_ndarray(np.ascontiguousarray(frame), format="rgb24")
        video.time_base = Fraction(1, fps)
        video.pts = next(counter)
        return video

    time_base = Fraction(1, fps)
    palette_graph = av.filter.Graph()
    src = palette_graph.add_buffer(width=size, height=size, format="rgb24", time_base=time_base)
    gen = palette_graph.add("palettegen", "max_colors=128:stats_mode=diff")
    sink = palette_graph.add("buffersink")
    src.link_to(gen)
    gen.link_to(sink)
    palette_graph.configure()

    for frame in frames:
        src.push(to_av(frame))
    src.push(None)
    palette = sink.pull()

    use_graph = av.filter.Graph()
    frames_in = use_graph.add_buffer(
        width=size, height=size, format="rgb24", name="in0", time_base=time_base
    )
    # palettegen emits a small image holding the palette entries
    palette_in = use_graph.add_buffer(
        width=palette.width,
        height=palette.height,
        format=palette.format.name,
        name="in1",
        time_base=time_base,
    )
    use = use_graph.add("paletteuse", "dither=bayer:bayer_scale=3")
    out = use_graph.add("buffersink")
    frames_in.link_to(use, 0, 0)
    palette_in.link_to(use, 0, 1)
    use.link_to(out)
    use_graph.configure()

    with av.open(path, mode="w") as container:
        stream = container.add_stream("gif", rate=fps)
        stream.width, stream.height = size, size
        stream.pix_fmt = "pal8"

        palette_in.push(palette)
        palette_in.push(None)
        for frame in frames:
            frames_in.push(to_av(frame))
            while True:
                try:
                    mapped = out.pull()
                except (av.BlockingIOError, av.EOFError):
                    break
                for packet in stream.encode(mapped):
                    container.mux(packet)
        frames_in.push(None)
        while True:
            try:
                mapped = out.pull()
            except (av.BlockingIOError, av.EOFError):
                break
            for packet in stream.encode(mapped):
                container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)
    return path


if __name__ == "__main__":
    print("wrote", build_gif())
