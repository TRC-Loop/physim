"""The physics engine, presets and collision response."""

import pytest

from physim import Circle, HollowCircle, PhysicsParams, Scene
from physim.physics import Engine
from physim.physics.collision import Contact, resolve_pair, resolve_wall
from physim.physics.spatial import SpatialGrid
from physim.types import Vec2


def test_params_reject_bad_values():
    with pytest.raises(ValueError, match="substeps"):
        PhysicsParams(substeps=0)
    with pytest.raises(ValueError, match="friction"):
        PhysicsParams(friction=2.0)


def test_gravity_vector_points_down_by_default():
    assert PhysicsParams(gravity=1000).gravity_vector == Vec2(0.0, -1000.0)


def test_params_with_returns_a_copy():
    base = PhysicsParams(gravity=1000)
    changed = base.with_(gravity=0)
    assert base.gravity == 1000 and changed.gravity == 0


def test_gravity_pulls_a_body_down():
    scene = Scene(physics=PhysicsParams(gravity=1000, damping=1.0))
    ball = Circle(radius=10, pos=(0, 0))
    scene.add(ball)
    scene.step(1.0)
    assert ball.velocity.y == pytest.approx(-1000.0, rel=1e-3)
    assert ball.pos.y < 0


def test_zero_gravity_keeps_speed_constant():
    scene = Scene(physics=PhysicsParams(gravity=0, damping=1.0))
    ball = Circle(radius=10, velocity=(100, 0))
    scene.add(ball)
    scene.step(1.0)
    assert ball.speed == pytest.approx(100.0)


def test_damping_slows_a_body():
    scene = Scene(physics=PhysicsParams(gravity=0, damping=0.5))
    ball = Circle(radius=10, velocity=(100, 0))
    scene.add(ball)
    scene.step(1.0)
    assert ball.speed < 100.0


def test_max_speed_is_enforced():
    scene = Scene(physics=PhysicsParams(gravity=0, damping=1.0, max_speed=50))
    ball = Circle(radius=10, velocity=(500, 0))
    scene.add(ball)
    scene.step(0.1)
    assert ball.speed <= 50.0 + 1e-6


def test_ball_stays_inside_its_ring():
    scene = Scene(physics=PhysicsParams(gravity=1200))
    scene.add(HollowCircle(radius=300, thickness=8))
    ball = Circle(radius=20, velocity=(400, 200))
    scene.add(ball)
    for _ in range(300):
        scene.step(1 / 60)
    assert ball.pos.length <= 300


def test_bounce_event_fires_and_counts():
    scene = Scene(physics=PhysicsParams(gravity=1200))
    scene.add(HollowCircle(radius=200, thickness=8))
    ball = Circle(radius=15, velocity=(0, 0))
    hits = []
    ball.on("bounce", lambda e: hits.append(e))
    scene.add(ball)
    for _ in range(180):
        scene.step(1 / 60)
    assert hits and ball.bounces == len(hits)


def test_bounce_event_reports_impact():
    scene = Scene(physics=PhysicsParams(gravity=1500))
    scene.add(HollowCircle(radius=150, thickness=8))
    ball = Circle(radius=10)
    seen = []
    ball.on("bounce", lambda e: seen.append(e.get("impact")))
    scene.add(ball)
    for _ in range(240):
        scene.step(1 / 60)
    assert seen and all(v > 0 for v in seen)


def test_elastic_bounce_preserves_speed():
    params = PhysicsParams(gravity=0, damping=1.0, restitution=1.0)
    scene = Scene(physics=params)
    scene.add(HollowCircle(radius=200, thickness=4))
    ball = Circle(radius=10, velocity=(300, 0))
    scene.add(ball)
    for _ in range(120):
        scene.step(1 / 60)
    assert ball.speed == pytest.approx(300.0, rel=0.05)


def test_lossy_bounce_removes_energy():
    params = PhysicsParams(gravity=0, damping=1.0, restitution=0.5)
    scene = Scene(physics=params)
    scene.add(HollowCircle(radius=100, thickness=4))
    ball = Circle(radius=10, velocity=(300, 0))
    scene.add(ball)
    for _ in range(120):
        scene.step(1 / 60)
    assert ball.speed < 300.0


def test_resolve_wall_reflects_velocity():
    ball = Circle(radius=10, velocity=(0, -100))
    resolve_wall(ball, Contact(normal=Vec2(0, 1), depth=0.0), restitution=1.0, friction=0.0)
    assert ball.velocity.y == pytest.approx(100.0)


def test_resolve_wall_ignores_separating_bodies():
    ball = Circle(radius=10, velocity=(0, 100))
    impact = resolve_wall(
        ball, Contact(normal=Vec2(0, 1), depth=0.0), restitution=1.0, friction=0.0
    )
    assert impact == 0.0


def test_resolve_pair_separates_overlapping_bodies():
    a = Circle(radius=20, pos=(0, 0), velocity=(100, 0))
    b = Circle(radius=20, pos=(10, 0), velocity=(-100, 0))
    resolve_pair(a, b, restitution=1.0, friction=0.0)
    assert (b.pos - a.pos).length >= 39.0
    assert a.velocity.x < 0 and b.velocity.x > 0


def test_fixed_bodies_do_not_move():
    scene = Scene(physics=PhysicsParams(gravity=1000))
    wall = Circle(radius=10, fixed=True)
    scene.add(wall)
    scene.step(1.0)
    assert wall.pos == Vec2(0, 0)


def test_ball_collisions_are_off_by_default():
    assert PhysicsParams().ball_collisions is False


def test_ball_collisions_when_enabled():
    params = PhysicsParams(gravity=0, damping=1.0, ball_collisions=True)
    scene = Scene(physics=params)
    scene.add(Circle(radius=30, pos=(-20, 0), velocity=(100, 0)))
    scene.add(Circle(radius=30, pos=(20, 0), velocity=(-100, 0)))
    scene.step(1 / 60)
    assert scene.stats.total_collisions > 0


def test_spatial_grid_finds_overlapping_pairs():
    grid = SpatialGrid(cell_size=50)
    bodies = [Circle(radius=10, pos=(0, 0)), Circle(radius=10, pos=(5, 5))]
    grid.build(bodies)
    assert (0, 1) in grid.candidate_pairs()


def test_spatial_grid_skips_distant_pairs():
    grid = SpatialGrid(cell_size=50)
    bodies = [Circle(radius=10, pos=(0, 0)), Circle(radius=10, pos=(5000, 5000))]
    grid.build(bodies)
    assert grid.candidate_pairs() == set()


def test_engine_reports_collisions_per_step():
    engine = Engine(PhysicsParams(gravity=0))
    assert engine.collisions_this_step == 0


def test_attraction_pulls_toward_the_center():
    params = PhysicsParams(gravity=0, damping=1.0, attraction=500_000)
    scene = Scene(physics=params)
    ball = Circle(radius=5, pos=(200, 0))
    scene.add(ball)
    scene.step(0.1)
    assert ball.velocity.x < 0
