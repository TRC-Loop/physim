"""Scene lifecycle, objects, boundaries and configuration."""

import pytest

from physim import (
    Circle,
    DebugConfig,
    HollowCircle,
    HollowRect,
    PhysicsParams,
    Polygon,
    Rect,
    RenderConfig,
    RingStack,
    Scene,
    Star,
    Text,
    Triangle,
)
from physim.types import Resolution, Vec2


def test_construct_runs_once():
    calls = []

    class Once(Scene):
        def construct(self):
            calls.append(1)

    scene = Once()
    scene.build()
    scene.build()
    assert calls == [1]


def test_add_returns_the_scene_for_chaining():
    scene = Scene()
    assert scene.add(Circle(radius=5)) is scene


def test_add_accepts_iterables():
    scene = Scene()
    scene.add([Circle(radius=5), Circle(radius=6)])
    assert len(scene.objects) == 2


def test_objects_know_their_scene():
    scene, ball = Scene(), Circle(radius=5)
    scene.add(ball)
    assert ball.scene is scene


def test_bodies_and_boundaries_are_separated():
    scene = Scene()
    scene.add(Circle(radius=5), HollowCircle(radius=100))
    assert len(scene.bodies) == 1 and len(scene.boundaries) == 1


def test_spawn_defers_until_the_frame_ends():
    scene = Scene()
    scene.spawn(Circle(radius=5))
    assert len(scene.objects) == 0
    scene.step(0.01)
    assert len(scene.objects) == 1


def test_destroyed_objects_are_dropped():
    scene = Scene()
    ball = Circle(radius=5)
    scene.add(ball)
    ball.destroy()
    scene.step(0.01)
    assert scene.objects == []


def test_seed_makes_runs_reproducible():
    a, b = Scene(seed=99), Scene(seed=99)
    assert [a.random.random() for _ in range(5)] == [b.random.random() for _ in range(5)]


def test_different_seeds_diverge():
    a, b = Scene(seed=1), Scene(seed=2)
    assert a.random.random() != b.random.random()


def test_run_sets_the_frame_count():
    scene = Scene(RenderConfig(fps=30))
    scene.run(seconds=2)
    assert scene.total_frames == 60


def test_frames_advance_scene_time():
    scene = Scene(RenderConfig(fps=10), physics=PhysicsParams(gravity=0))
    scene.run(seconds=1)
    list(scene.frames())
    assert scene.time == pytest.approx(1.0)


def test_run_until_stops_on_a_predicate():
    scene = Scene(RenderConfig(fps=30), physics=PhysicsParams(gravity=0))
    scene.run_until(lambda s: s.frame >= 5, max_seconds=10)
    assert len(list(scene.frames())) == 5


def test_run_until_stops_on_an_event():
    scene = Scene(RenderConfig(fps=30), physics=PhysicsParams(gravity=1200))
    scene.add(HollowCircle(radius=120, gap_degrees=360, thickness=4))
    scene.add(Circle(radius=10, velocity=(600, 0)))
    scene.run_until("escape", max_seconds=5)
    assert len(list(scene.frames())) < 150


def test_stop_from_a_frame_callback():
    # stop() finishes the frame in progress, so the triggering frame still renders
    scene = Scene(RenderConfig(fps=30), physics=PhysicsParams(gravity=0))
    scene.run(seconds=10)
    scene.each_frame(lambda s, dt: s.stop() if s.frame >= 3 else None)
    assert len(list(scene.frames())) == 4


def test_each_frame_receives_dt():
    scene = Scene(RenderConfig(fps=20), physics=PhysicsParams(gravity=0))
    seen = []
    scene.each_frame(lambda s, dt: seen.append(dt))
    scene.run(seconds=0.5)
    list(scene.frames())
    assert seen and seen[0] == pytest.approx(0.05)


def test_stats_track_objects_and_time():
    scene = Scene(RenderConfig(fps=10), physics=PhysicsParams(gravity=0))
    scene.add(Circle(radius=5), Circle(radius=5))
    scene.run(seconds=0.5)
    list(scene.frames())
    assert scene.stats.object_count == 2
    assert scene.stats.scene_time == pytest.approx(0.5)


def test_physics_preset_by_name():
    scene = Scene(physics="zero_g")
    assert scene.params.gravity == 0


def test_unknown_physics_preset_is_rejected():
    with pytest.raises(ValueError, match="unknown physics preset"):
        Scene(physics="nonsense")


def test_debug_bool_shorthand():
    assert Scene(debug=True).debug.enabled is True
    assert Scene(debug=False).debug.enabled is False


def test_render_config_defaults_to_square_30fps():
    config = RenderConfig()
    assert config.resolution == Resolution(1080, 1080)
    assert config.fps == 30
    assert config.frame_duration == pytest.approx(1 / 30)


def test_render_config_validates():
    with pytest.raises(ValueError, match="fps"):
        RenderConfig(fps=0)
    with pytest.raises(ValueError, match="backend"):
        RenderConfig(backend="quantum")
    with pytest.raises(ValueError, match="format"):
        RenderConfig(format="avi")


def test_debug_config_validates_corner():
    with pytest.raises(ValueError, match="corner"):
        DebugConfig(corner="middle")


def test_hollow_circle_gap_detection():
    ring = HollowCircle(radius=100, gap_degrees=90, gap_angle=0)
    assert ring.angle_in_gap(45) is True
    assert ring.angle_in_gap(180) is False


def test_gap_wraps_past_360():
    ring = HollowCircle(radius=100, gap_degrees=40, gap_angle=350)
    assert ring.angle_in_gap(355) is True
    assert ring.angle_in_gap(10) is True
    assert ring.angle_in_gap(100) is False


def test_closed_ring_has_no_gap():
    assert HollowCircle(radius=100).angle_in_gap(0) is False


def test_gap_rotates_over_time():
    ring = HollowCircle(radius=100, gap_degrees=30, rotation_speed=90)
    start = ring.gap_angle
    ring.update(1.0)
    assert ring.gap_angle == pytest.approx((start + 90) % 360)


def test_escape_fires_once_per_object():
    ring = HollowCircle(radius=100, gap_degrees=90, thickness=4)
    ball = Circle(radius=5, pos=(500, 0))
    assert ring.contains_escape(ball) is True
    assert ring.contains_escape(ball) is False


def test_hollow_rect_contacts_a_wall():
    rect = HollowRect(width=200, height=200, thickness=4)
    ball = Circle(radius=10, pos=(200, 0))
    assert rect.contact_with(ball) is not None


def test_hollow_rect_ignores_interior_objects():
    rect = HollowRect(width=200, height=200, thickness=4)
    assert rect.contact_with(Circle(radius=10, pos=(0, 0))) is None


def test_ring_stack_builds_layers():
    stack = RingStack(count=4, inner_radius=100, spacing=50)
    assert len(stack.rings) == 4
    assert stack.rings[-1].radius == 250


def test_ring_stack_picks_the_ring_the_body_is_inside():
    stack = RingStack(count=3, inner_radius=100, spacing=50, gap_degrees=30)
    # sitting between the first and second ring
    ball = Circle(radius=5, pos=(120, 0))
    assert stack.active_ring(ball) is stack.rings[1]


def test_ring_stack_ignores_rings_already_passed():
    # a ring the body is outside of must not drag it back toward the centre
    stack = RingStack(count=3, inner_radius=100, spacing=50, gap_degrees=30)
    ball = Circle(radius=5, pos=(120, 0))
    contact = stack.contact_with(ball)
    assert contact is None or contact.depth < 10


def test_ring_stack_does_not_teleport_a_passed_body():
    scene = Scene(RenderConfig(fps=60), physics=PhysicsParams(gravity=0, damping=1.0))
    stack = RingStack(count=3, inner_radius=100, spacing=50, gap_degrees=30)
    scene.add(stack)
    ball = Circle(radius=5, pos=(120, 0), velocity=(10, 0))
    scene.add(ball)

    before = ball.pos
    scene.step(1 / 60)
    assert (ball.pos - before).length < 20


def test_ring_stack_escape_fires_for_inner_rings():
    stack = RingStack(count=3, inner_radius=100, spacing=50, gap_degrees=30)
    # beyond the innermost ring but nowhere near the outermost
    ball = Circle(radius=5, pos=(140, 0))
    assert stack.contains_escape(ball) is True


def test_ring_stack_escape_only_fires_once_per_ring():
    stack = RingStack(count=3, inner_radius=100, spacing=50, gap_degrees=30)
    ball = Circle(radius=5, pos=(140, 0))
    assert stack.contains_escape(ball) is True
    assert stack.contains_escape(ball) is False


def test_ring_stack_pop_removes_the_innermost():
    stack = RingStack(count=3)
    popped = stack.pop()
    assert popped is stack.rings[0] and popped.alive is False


def test_polygon_needs_three_sides():
    with pytest.raises(ValueError, match="at least 3 sides"):
        Polygon(sides=2)


def test_polygon_vertex_count():
    assert len(Polygon(radius=50, sides=6).vertices()) == 6
    assert len(Triangle(radius=50).vertices()) == 3


def test_star_has_two_points_per_spike():
    assert len(Star(radius=50, points=5).vertices()) == 10


def test_shapes_grow():
    for shape in (Circle(radius=10), Triangle(radius=10), Star(radius=10)):
        shape.grow(5)
        assert shape.radius == 15


def test_rect_grows_both_dimensions():
    rect = Rect(width=10, height=10)
    rect.grow(5)
    assert rect.width == 20 and rect.height == 20


def test_collision_radius_follows_scale():
    ball = Circle(radius=10)
    ball.transform.scale = Vec2(2, 2)
    assert ball.collision_radius == 20


def test_text_rejects_bad_alignment():
    with pytest.raises(ValueError, match="align"):
        Text("hi", align="sideways")


def test_text_change_fires_an_event():
    text, seen = Text("a"), []
    text.on("change", seen.append)
    text.set_text("b")
    assert len(seen) == 1 and text.text == "b"


def test_text_ignores_identical_updates():
    text, seen = Text("a"), []
    text.on("change", seen.append)
    text.set_text("a")
    assert seen == []


def test_text_splits_lines():
    assert Text("a\nb\nc").lines == ["a", "b", "c"]


def test_clone_is_independent():
    ball = Circle(radius=10, pos=(5, 5))
    twin = ball.clone()
    twin.transform.position = Vec2(99, 99)
    assert ball.pos == (5, 5) and twin.id != ball.id


def test_effects_attach_and_chain():
    from physim.effects import Glow, Trail

    ball = Circle(radius=10)
    assert ball.add_effect(Trail(), Glow()) is ball
    assert len(ball.effects) == 2


def test_trail_records_positions():
    from physim.effects import Trail

    scene = Scene(physics=PhysicsParams(gravity=0))
    ball = Circle(radius=10, velocity=(100, 0))
    trail = Trail(length=5)
    ball.add_effect(trail)
    scene.add(ball)
    for _ in range(10):
        scene.step(1 / 60)
    assert len(trail.points) == 5
