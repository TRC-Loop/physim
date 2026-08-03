"""Colors, gradients and dynamic colors."""

import pytest

from physim.color import Color, ColorSequence, Fade, Gradient, RGBCycle, resolve_paint


def test_hex_to_rgba8():
    assert Color("#ff0055").to_rgba8() == (255, 0, 85, 255)


def test_named_css_color():
    assert Color("red").to_rgba8()[:3] == (255, 0, 0)


def test_rgb_accepts_bytes_and_floats():
    assert Color.rgb(255, 0, 85).to_rgba8() == (255, 0, 85, 255)
    assert Color.rgb(1.0, 0.0, 0.0).to_rgba8()[:3] == (255, 0, 0)


def test_alpha_roundtrip():
    assert Color("#ffffff").with_alpha(0.5).alpha == pytest.approx(0.5)


def test_argb32_packing():
    packed = Color("#ff0055").to_argb32()
    assert (packed >> 24) & 0xFF == 255
    assert (packed >> 16) & 0xFF == 255
    assert packed & 0xFF == 85


def test_oklch_and_lch_construct():
    assert len(Color.oklch(0.7, 0.2, 20).to_rgba8()) == 4
    assert len(Color.lch(70, 40, 20).to_rgba8()) == 4


def test_cmyk_black_and_white():
    assert Color.cmyk(0, 0, 0, 1).to_rgba8()[:3] == (0, 0, 0)
    assert Color.cmyk(0, 0, 0, 0).to_rgba8()[:3] == (255, 255, 255)


def test_interpolate_endpoints():
    a, b = Color("#000000"), Color("#ffffff")
    assert a.interpolate(b, 0.0).to_rgba8()[:3] == (0, 0, 0)
    assert a.interpolate(b, 1.0).to_rgba8()[:3] == (255, 255, 255)


def test_interpolate_midpoint_is_between():
    mid = Color("#000000").interpolate("#ffffff", 0.5).to_rgba8()[0]
    assert 0 < mid < 255


def test_lighten_and_darken():
    base = Color("#808080")
    assert base.lighten(0.2).to_rgba8()[0] > base.to_rgba8()[0]
    assert base.darken(0.2).to_rgba8()[0] < base.to_rgba8()[0]


def test_equality_and_hashing():
    assert Color("#ff0000") == Color("rgb(255 0 0)")
    assert len({Color("#ff0000"), Color("rgb(255, 0, 0)")}) == 1


def test_rgb_cycle_changes_over_time():
    cycle = RGBCycle(speed=90)
    assert cycle.at(0.0) != cycle.at(1.0)


def test_rgb_cycle_wraps_after_full_turn():
    cycle = RGBCycle(speed=360)
    assert cycle.at(0.0) == cycle.at(1.0)


def test_color_sequence_advances_and_loops():
    seq = ColorSequence(colors=["#ff0000", "#00ff00"])
    assert seq.advance() == Color("#00ff00")
    assert seq.advance() == Color("#ff0000")


def test_color_sequence_timed():
    seq = ColorSequence(colors=["#ff0000", "#00ff00"], interval=1.0)
    assert seq.at(0.5) == Color("#ff0000")
    assert seq.at(1.5) == Color("#00ff00")


def test_fade_endpoints():
    fade = Fade(start="#000000", end="#ffffff", duration=1.0, loop=False)
    assert fade.at(0.0).to_rgba8()[:3] == (0, 0, 0)
    assert fade.at(1.0).to_rgba8()[:3] == (255, 255, 255)


def test_gradient_stops_are_even_by_default():
    assert Gradient(colors=["#000", "#888", "#fff"]).resolved_stops() == [0.0, 0.5, 1.0]


def test_gradient_rejects_bad_kind():
    with pytest.raises(ValueError, match="kind must be"):
        Gradient(kind="spiral")


def test_resolve_paint_handles_each_form():
    assert isinstance(resolve_paint("#fff", 0.0), Color)
    assert isinstance(resolve_paint(RGBCycle(), 0.0), Color)
    assert isinstance(resolve_paint(Gradient(), 0.0), Gradient)
    assert resolve_paint(None, 0.0) is None
