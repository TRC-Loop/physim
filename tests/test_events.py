"""Events, handlers and the built-in actions."""

import pytest

from physim import Circle, HollowCircle, PhysicsParams, Scene
from physim.actions import (
    Action,
    After,
    ChangeColor,
    Clone,
    Custom,
    Destroy,
    Grow,
    Sequence,
    SetSpeed,
    Shrink,
    SpeedUp,
    Stop,
)
from physim.color import Color, ColorSequence
from physim.events import Event, EventBus


def fire(source=None, scene=None, **data) -> Event:
    """Build an event for exercising an action directly."""
    return Event(name="bounce", source=source, scene=scene, data=data)


def test_handlers_receive_the_event():
    bus, seen = EventBus(), []
    bus.on("bounce", seen.append)
    bus.emit(fire())
    assert len(seen) == 1


def test_multiple_handlers_run_in_order():
    bus, order = EventBus(), []
    bus.on("bounce", lambda e: order.append(1))
    bus.on("bounce", lambda e: order.append(2))
    bus.emit(fire())
    assert order == [1, 2]


def test_off_removes_a_single_handler():
    bus, seen = EventBus(), []
    handler = bus.on("bounce", seen.append)
    bus.off("bounce", handler)
    bus.emit(fire())
    assert seen == []


def test_off_without_handler_clears_all():
    bus, seen = EventBus(), []
    bus.on("bounce", seen.append)
    bus.off("bounce")
    bus.emit(fire())
    assert seen == []


def test_unknown_event_is_harmless():
    EventBus().emit(fire())


def test_event_payload_access():
    event = fire(impact=42)
    assert event["impact"] == 42
    assert event.get("missing", "fallback") == "fallback"


def test_object_events_bubble_to_the_scene():
    scene, seen = Scene(), []
    ball = Circle(radius=10)
    scene.add(ball)
    scene.on("bounce", seen.append)
    ball.emit("bounce")
    assert len(seen) == 1


def test_speed_up_scales_velocity():
    ball = Circle(radius=10, velocity=(100, 0))
    SpeedUp(2.0).run(fire(source=ball))
    assert ball.speed == pytest.approx(200.0)


def test_speed_up_respects_the_ceiling():
    ball = Circle(radius=10, velocity=(100, 0))
    SpeedUp(10.0, max_speed=150).run(fire(source=ball))
    assert ball.speed == pytest.approx(150.0)


def test_set_speed_keeps_direction():
    ball = Circle(radius=10, velocity=(100, 0))
    SetSpeed(50).run(fire(source=ball))
    assert ball.velocity == (50, 0)


def test_grow_increases_radius():
    ball = Circle(radius=10)
    Grow(5).run(fire(source=ball))
    assert ball.radius == 15


def test_grow_stops_at_max_size():
    ball = Circle(radius=10)
    Grow(100, max_size=20).run(fire(source=ball))
    assert ball.radius == pytest.approx(20)


def test_shrink_respects_the_floor():
    ball = Circle(radius=10)
    Shrink(100, min_size=2).run(fire(source=ball))
    assert ball.radius == pytest.approx(2)


def test_every_rate_limits_an_action():
    ball = Circle(radius=10)
    action = Grow(1, every=3)
    for _ in range(3):
        action.run(fire(source=ball))
    assert ball.radius == 11


def test_chance_zero_never_runs():
    scene = Scene(seed=1)
    ball = Circle(radius=10)
    action = Grow(5, chance=0.0)
    for _ in range(20):
        action.run(fire(source=ball, scene=scene))
    assert ball.radius == 10


def test_destroy_marks_the_source():
    scene = Scene()
    ball = Circle(radius=10)
    scene.add(ball)
    Destroy().run(fire(source=ball, scene=scene))
    assert ball.alive is False


def test_destroy_can_target_another_object():
    scene = Scene()
    ball, ring = Circle(radius=10), HollowCircle(radius=100)
    scene.add(ball, ring)
    Destroy(ring).run(fire(source=ball, scene=scene))
    assert ring.alive is False and ball.alive is True


def test_clone_adds_objects_to_the_scene():
    scene = Scene(seed=7)
    ball = Circle(radius=10, velocity=(100, 0))
    scene.add(ball)
    Clone(2).run(fire(source=ball, scene=scene))
    scene.step(0.01)
    assert len(scene.bodies) == 3


def test_clones_do_not_inherit_handlers():
    scene = Scene(seed=7)
    ball = Circle(radius=10, velocity=(100, 0))
    ball.on("bounce", Clone(1))
    scene.add(ball)
    twin = ball.clone()
    assert twin.events.has("bounce") is False


def test_clone_respects_the_object_ceiling():
    scene = Scene(seed=7)
    ball = Circle(radius=10, velocity=(100, 0))
    scene.add(ball)
    Clone(5, max_objects=1).run(fire(source=ball, scene=scene))
    scene.step(0.01)
    assert len(scene.bodies) == 1


def test_stop_ends_the_scene():
    scene = Scene()
    Stop().run(fire(scene=scene))
    assert scene.stopping is True


def test_change_color_sets_the_fill():
    ball = Circle(radius=10, fill="#000000")
    ChangeColor("#ff0000").run(fire(source=ball))
    assert Color.of(ball.fill) == Color("#ff0000")


def test_change_color_steps_a_sequence():
    ball = Circle(radius=10, fill="#000000")
    action = ChangeColor(ColorSequence(colors=["#ff0000", "#00ff00"]))
    action.run(fire(source=ball))
    assert Color.of(ball.fill) == Color("#00ff00")


def test_custom_wraps_a_callable():
    seen = []
    Custom(lambda e: seen.append(e)).run(fire())
    assert len(seen) == 1


def test_sequence_runs_every_action():
    ball = Circle(radius=10, velocity=(100, 0))
    Sequence(Grow(5), SpeedUp(2.0)).run(fire(source=ball))
    assert ball.radius == 15 and ball.speed == pytest.approx(200.0)


def test_after_delays_until_the_threshold():
    ball = Circle(radius=10)
    action = After(3, Grow(1))
    for _ in range(2):
        action.run(fire(source=ball))
    assert ball.radius == 10
    action.run(fire(source=ball))
    assert ball.radius == 11


def test_action_subclass_must_implement_apply():
    with pytest.raises(NotImplementedError):
        Action().run(fire())


def test_bad_handler_type_is_rejected():
    bus = EventBus()
    bus.on("bounce", "not callable")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        bus.emit(fire())


def test_stop_ends_a_render_early():
    scene = Scene(physics=PhysicsParams(gravity=0))
    scene.run(seconds=10)
    scene.on("frame", lambda e: scene.stop() if scene.frame > 5 else None)
    frames = list(scene.frames())
    assert len(frames) < 300
