"""Geometry value types."""

import math

import pytest

from physim.types import Resolution, Size, Vec2


def test_vec2_coerces_tuples():
    assert Vec2.of((3, 4)) == Vec2(3.0, 4.0)
    assert Vec2.of(Vec2(1, 2)) == Vec2(1.0, 2.0)


def test_vec2_arithmetic():
    assert Vec2(1, 2) + (3, 4) == Vec2(4, 6)
    assert Vec2(5, 5) - (1, 2) == Vec2(4, 3)
    assert Vec2(2, 3) * 2 == Vec2(4, 6)
    assert -Vec2(1, -1) == Vec2(-1, 1)


def test_vec2_length_and_normalize():
    assert Vec2(3, 4).length == 5.0
    assert Vec2(3, 4).length_squared == 25.0
    assert Vec2(3, 4).normalized().length == pytest.approx(1.0)
    assert Vec2(0, 0).normalized() == Vec2(0, 0)


def test_vec2_rotation_and_angle():
    rotated = Vec2(1, 0).rotated(90)
    assert rotated.x == pytest.approx(0.0, abs=1e-9)
    assert rotated.y == pytest.approx(1.0)
    assert Vec2(0, 1).angle == pytest.approx(90.0)


def test_vec2_polar_roundtrip():
    v = Vec2.polar(30, 10)
    assert v.length == pytest.approx(10.0)
    assert v.angle == pytest.approx(30.0)


def test_vec2_reflect_off_flat_surface():
    # travelling down, bouncing off a floor whose normal points up
    assert Vec2(1, -1).reflected(Vec2(0, 1)) == Vec2(1, 1)


def test_vec2_clamped():
    assert Vec2(10, 0).clamped(5).length == pytest.approx(5.0)
    assert Vec2(1, 0).clamped(5) == Vec2(1, 0)


def test_vec2_dot_and_cross():
    assert Vec2(1, 0).dot((0, 1)) == 0.0
    assert Vec2(1, 0).cross((0, 1)) == 1.0


def test_size_accepts_scalar():
    assert Size.of(5) == Size(5.0, 5.0)
    assert Size.of((4, 2)).aspect == 2.0


def test_resolution_parsing():
    assert Resolution.parse("square") == Resolution(1080, 1080)
    assert Resolution.parse("1920x1080") == Resolution(1920, 1080)
    assert Resolution.parse((640, 480)) == Resolution(640, 480)


def test_resolution_rejects_nonsense():
    with pytest.raises(ValueError, match="unknown resolution"):
        Resolution.parse("enormous")


def test_scene_to_raster_is_centered_and_y_up():
    res = Resolution(1000, 800)
    assert res.to_raster((0, 0)) == Vec2(500, 400)
    # positive y is up, so it maps to a smaller raster row
    assert res.to_raster((0, 100)) == Vec2(500, 300)


def test_raster_roundtrip():
    res = Resolution(1080, 1920)
    point = Vec2(123, -456)
    assert res.to_scene(res.to_raster(point)) == point


def test_vec2_is_immutable():
    with pytest.raises((AttributeError, TypeError)):
        Vec2(1, 2).x = 5  # type: ignore[misc]


def test_vec2_lerp():
    assert Vec2(0, 0).lerp((10, 20), 0.5) == Vec2(5, 10)


def test_vec2_iterates_as_pair():
    x, y = Vec2(7, 8)
    assert (x, y) == (7.0, 8.0)


def test_vec2_perpendicular_is_orthogonal():
    v = Vec2(3, 4)
    assert v.dot(v.perpendicular()) == pytest.approx(0.0)
    assert v.perpendicular().length == pytest.approx(v.length)


def test_polar_matches_trig():
    v = Vec2.polar(45, 2)
    assert v.x == pytest.approx(2 * math.cos(math.radians(45)))
