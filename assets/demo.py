"""The three scenes stitched together into the README demo.

Each runs for five seconds and shows off a different part of the library.

    physim render assets/demo.py Bouncing
    python assets/demo.py          # renders all three and builds demo.gif
"""

from physim import Circle, Color, HollowCircle, RGBCycle, RingStack, Scene
from physim.actions import Clone, Grow, PopRing, SpeedUp
from physim.effects import Glow, Trail
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
        self.run(seconds=SECONDS)


DEMOS = (Bouncing, Growing, Escaping)


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


def build_gif(path="assets/demo.gif", size=380, fps=16) -> str:
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
