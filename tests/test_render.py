"""Rendering, encoding and the debug overlay."""

import av
import numpy as np
import pytest

from physim import (
    Circle,
    DebugConfig,
    Gradient,
    HollowCircle,
    PhysicsParams,
    RenderConfig,
    RGBCycle,
    Scene,
    Text,
)
from physim.render import Renderer
from physim.stats import Stats


def tiny(**kwargs) -> RenderConfig:
    """A small, fast config for tests."""
    kwargs.setdefault("resolution", (160, 160))
    kwargs.setdefault("fps", 10)
    return RenderConfig(**kwargs)


def build(objects=(), **kwargs) -> Scene:
    """A scene with no gravity and the given objects."""
    scene = Scene(tiny(**kwargs), physics=PhysicsParams(gravity=0))
    scene.add(*objects)
    return scene


def test_renders_an_rgb_frame():
    scene = build([Circle(radius=20, fill="#ff0000")])
    frame = Renderer(scene.config).render(scene)
    assert frame.shape == (160, 160, 3)
    assert frame.dtype == np.uint8


def test_background_is_applied():
    scene = build(config_background := ())
    scene.config.background = "#ff0000"
    frame = Renderer(scene.config).render(scene)
    assert frame[0, 0, 0] > 200 and frame[0, 0, 1] < 50
    assert config_background == ()


def test_object_is_actually_drawn():
    empty = Renderer(tiny()).render(build())
    with_ball = build([Circle(radius=40, fill="#ffffff")])
    drawn = Renderer(with_ball.config).render(with_ball)
    assert not np.array_equal(empty, drawn)


def test_object_lands_at_the_center():
    scene = build([Circle(radius=30, fill="#ffffff")])
    frame = Renderer(scene.config).render(scene)
    assert frame[80, 80].mean() > 200


def test_positive_y_draws_above_center():
    scene = build([Circle(radius=10, fill="#ffffff", pos=(0, 50))])
    frame = Renderer(scene.config).render(scene)
    assert frame[30, 80].mean() > frame[130, 80].mean()


def test_hidden_objects_are_skipped():
    scene = build([Circle(radius=40, fill="#ffffff")])
    scene.objects[0].visible = False
    frame = Renderer(scene.config).render(scene)
    assert frame[80, 80].mean() < 50


def test_z_order_puts_later_objects_on_top():
    scene = build(
        [
            Circle(radius=40, fill="#ff0000", z=1),
            Circle(radius=40, fill="#0000ff", z=0),
        ]
    )
    frame = Renderer(scene.config).render(scene)
    assert frame[80, 80][0] > frame[80, 80][2]


def test_gradient_fill_renders():
    scene = build([Circle(radius=60, fill=Gradient(colors=["#ff0000", "#0000ff"]))])
    frame = Renderer(scene.config).render(scene)
    assert frame[80, 80].sum() > 0


def test_dynamic_color_follows_scene_time():
    scene = build([Circle(radius=50, fill=RGBCycle(speed=180))])
    renderer = Renderer(scene.config)
    first = renderer.render(scene).copy()
    scene.time = 1.0
    assert not np.array_equal(first, renderer.render(scene))


def test_text_renders_pixels():
    scene = build([Text("hello", size=40, color="#ffffff")])
    frame = Renderer(scene.config).render(scene)
    assert frame.max() > 200


def test_ring_renders():
    scene = build([HollowCircle(radius=60, stroke="#ffffff", thickness=4)])
    frame = Renderer(scene.config).render(scene)
    assert frame.max() > 200


def test_ring_gap_removes_pixels():
    closed = build([HollowCircle(radius=60, stroke="#ffffff", thickness=4)])
    open_ring = build([HollowCircle(radius=60, stroke="#ffffff", thickness=4, gap_degrees=120)])
    lit_closed = (Renderer(closed.config).render(closed) > 128).sum()
    lit_open = (Renderer(open_ring.config).render(open_ring) > 128).sum()
    assert lit_open < lit_closed


def test_cpu_backend_is_the_default():
    assert Renderer(tiny()).backend == "cpu"


def test_debug_overlay_changes_the_frame():
    scene = build([Circle(radius=20)])
    plain = Renderer(scene.config, DebugConfig(enabled=False)).render(scene).copy()
    scene.stats.total_frames = 10
    overlaid = Renderer(scene.config, DebugConfig(enabled=True)).render(scene)
    assert not np.array_equal(plain, overlaid)


def test_overlay_can_be_disabled_while_debugging():
    scene = build([Circle(radius=20)])
    plain = Renderer(scene.config, DebugConfig(enabled=False)).render(scene).copy()
    no_overlay = Renderer(scene.config, DebugConfig(enabled=True, overlay=False)).render(scene)
    assert np.array_equal(plain, no_overlay)


def test_motion_blur_still_produces_a_frame():
    scene = build([Circle(radius=20, fill="#ffffff")], motion_blur=4)
    assert Renderer(scene.config).render(scene).shape == (160, 160, 3)


def test_stats_report_fps_and_progress():
    stats = Stats(total_frames=10)
    stats.begin_frame()
    stats.end_frame()
    assert stats.frame_index == 1
    assert stats.fps > 0
    assert stats.progress == pytest.approx(0.1)


def test_stats_eta_is_unknown_without_a_total():
    assert Stats().eta is None


def test_stats_snapshot_has_every_key():
    snapshot = Stats().as_dict()
    for key in ("fps", "frametime_ms", "object_count", "render_ms", "encode_ms"):
        assert key in snapshot


def test_overlay_lines_respect_the_config():
    stats = Stats(total_frames=10)
    stats.begin_frame()
    stats.end_frame()
    lines = "\n".join(stats.overlay_lines(DebugConfig(enabled=True)))
    assert "frametime" in lines and "objects" in lines


def test_render_writes_a_playable_mp4(tmp_path):
    scene = build([HollowCircle(radius=60), Circle(radius=10, velocity=(50, 20))])
    scene.run(seconds=0.5)
    path = scene.render(output=tmp_path / "out.mp4", quiet=True)

    assert path.exists() and path.stat().st_size > 0
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        assert (stream.width, stream.height) == (160, 160)
        assert len(list(container.decode(video=0))) == 5


def test_render_writes_mkv(tmp_path):
    scene = build([Circle(radius=10)], format="mkv")
    scene.run(seconds=0.3)
    path = scene.render(output=tmp_path / "out.mkv", quiet=True)
    with av.open(str(path)) as container:
        assert container.streams.video[0].codec_context.name == "h264"


def test_rendered_video_actually_moves(tmp_path):
    scene = build([HollowCircle(radius=70), Circle(radius=12, velocity=(120, 60))])
    scene.run(seconds=1.0)
    path = scene.render(output=tmp_path / "move.mp4", quiet=True)

    with av.open(str(path)) as container:
        frames = [f.to_ndarray(format="rgb24") for f in container.decode(video=0)]
    changed = sum(1 for i in range(1, len(frames)) if not np.array_equal(frames[i], frames[i - 1]))
    assert changed >= len(frames) - 2


def test_cached_paints_do_not_bleed_between_objects():
    # flat-color paints are shared, so a per-object effect must not mutate one
    from physim.effects import Glow

    scene = build(
        [
            Circle(radius=25, fill="#ff0000", pos=(-40, 0)),
            Circle(radius=25, fill="#0000ff", pos=(40, 0)),
        ]
    )
    scene.objects[0].add_effect(Glow(strength=0.8))
    frame = Renderer(scene.config).render(scene)

    left, right = frame[80, 40], frame[80, 120]
    assert left[0] > left[2], "left ball should stay red"
    assert right[2] > right[0], "right ball should stay blue"


def test_glow_does_not_blur_the_next_object():
    from physim.effects import Glow

    plain = build([Circle(radius=25, fill="#00ff00", pos=(40, 0))])
    reference = Renderer(plain.config).render(plain).copy()

    with_glow = build(
        [
            Circle(radius=25, fill="#ff0000", pos=(-40, 0)),
            Circle(radius=25, fill="#00ff00", pos=(40, 0)),
        ]
    )
    with_glow.objects[0].add_effect(Glow(strength=0.8))
    frame = Renderer(with_glow.config).render(with_glow)
    assert np.array_equal(frame[80, 120], reference[80, 120])


def test_color_cache_survives_alpha_changes():
    from physim.color import Color

    base = Color("#ff0055")
    assert base.to_rgba8() == (255, 0, 85, 255)
    faded = base.with_alpha(0.5)
    assert faded.to_rgba8()[3] == 128
    assert base.to_rgba8()[3] == 255, "the original must keep its own alpha"


def test_repeated_conversion_is_stable():
    from physim.color import Color

    c = Color.oklch(0.7, 0.2, 20)
    assert c.to_rgba8() == c.to_rgba8()


def test_default_output_path_uses_the_scene_name():
    assert RenderConfig().output_path("MyScene").name == "MyScene.mp4"
