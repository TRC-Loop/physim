"""Turning physim fill values into Skia paints."""

from __future__ import annotations

import math

import skia

from ..color import Gradient, Texture, resolve_paint
from ..types import Resolution, Vec2

#: how a texture's fit mode maps onto Skia tiling
_TILE_MODES = {
    "tile": skia.TileMode.kRepeat,
    "stretch": skia.TileMode.kClamp,
    "cover": skia.TileMode.kClamp,
    "contain": skia.TileMode.kDecal,
}


def _skia_points(res: Resolution, points: list[Vec2]) -> list:
    """Convert scene points into Skia raster points."""
    return [skia.Point(*res.to_raster(p)) for p in points]


def gradient_shader(gradient: Gradient, res: Resolution, center: Vec2, extent: float):
    """Build a Skia shader for a gradient, positioned around ``center``."""
    colors = [c.to_argb32() for c in gradient.resolved_colors()]
    stops = gradient.resolved_stops()

    if gradient.relative:
        start = center + gradient.start_vec * (extent / 100.0)
        end = center + gradient.end_vec * (extent / 100.0)
        radius = gradient.radius / 100.0 * extent
    else:
        start, end, radius = gradient.start_vec, gradient.end_vec, gradient.radius

    if gradient.rotation:
        start = center + (start - center).rotated(gradient.rotation)
        end = center + (end - center).rotated(gradient.rotation)

    if gradient.kind == "radial":
        return skia.GradientShader.MakeRadial(
            center=skia.Point(*res.to_raster(center)),
            radius=max(1.0, radius),
            colors=colors,
            positions=stops,
        )
    if gradient.kind == "sweep":
        cx, cy = res.to_raster(center)
        return skia.GradientShader.MakeSweep(cx=cx, cy=cy, colors=colors, positions=stops)
    return skia.GradientShader.MakeLinear(
        points=_skia_points(res, [start, end]), colors=colors, positions=stops
    )


def texture_shader(texture: Texture, res: Resolution, center: Vec2, extent: float):
    """Build a Skia shader that fills a shape with an image."""
    image = texture.image()
    mode = _TILE_MODES[texture.fit]

    matrix = skia.Matrix()
    cx, cy = res.to_raster(center)
    if texture.fit in ("cover", "contain", "stretch"):
        span = max(1.0, extent * 2.0)
        if texture.fit == "stretch":
            sx, sy = span / image.width(), span / image.height()
        else:
            pick = max if texture.fit == "cover" else min
            scale = pick(span / image.width(), span / image.height())
            sx = sy = scale
        matrix.setScale(sx * texture.scale, sy * texture.scale)
        matrix.postTranslate(
            cx - image.width() * sx * texture.scale / 2.0,
            cy - image.height() * sy * texture.scale / 2.0,
        )
    else:
        matrix.setScale(texture.scale, texture.scale)
        matrix.postTranslate(cx, cy)

    if texture.rotation:
        matrix.postRotate(-texture.rotation, cx, cy)
    matrix.postTranslate(texture.offset[0], -texture.offset[1])
    return image.makeShader(mode, mode, skia.SamplingOptions(), matrix)


def make_paint(
    value,
    res: Resolution,
    time: float,
    *,
    center: Vec2 = Vec2(),
    extent: float = 100.0,
    opacity: float = 1.0,
    stroke_width: float = 0.0,
    antialias: bool = True,
):
    """Build a Skia paint for any fill value, or ``None`` when there's nothing to draw."""
    resolved = resolve_paint(value, time)
    if resolved is None:
        return None

    paint = skia.Paint(AntiAlias=antialias)
    if stroke_width > 0.0:
        paint.setStyle(skia.Paint.kStroke_Style)
        paint.setStrokeWidth(stroke_width)
        paint.setStrokeCap(skia.Paint.kRound_Cap)

    if isinstance(resolved, Gradient):
        paint.setShader(gradient_shader(resolved, res, center, extent))
        paint.setAlphaf(opacity)
    elif isinstance(resolved, Texture):
        paint.setShader(texture_shader(resolved, res, center, extent))
        paint.setAlphaf(opacity * resolved.opacity)
    else:
        r, g, b, a = resolved.to_rgba8()
        paint.setColor(skia.Color(r, g, b, a))
        paint.setAlphaf((a / 255.0) * opacity)
    return paint


def blur_filter(radius: float):
    """A Gaussian blur image filter, used by the glow effect."""
    sigma = max(0.01, radius / 2.0)
    return skia.ImageFilters.Blur(sigma, sigma)


def arc_path(res: Resolution, center: Vec2, radius: float, start_deg: float, sweep_deg: float):
    """Build a Skia path tracing an arc, used to draw rings with gaps."""
    cx, cy = res.to_raster(center)
    rect = skia.Rect.MakeLTRB(cx - radius, cy - radius, cx + radius, cy + radius)
    path = skia.Path()
    # skia sweeps clockwise in raster space, scene angles run counter-clockwise
    path.addArc(rect, -start_deg, -sweep_deg)
    return path


def polygon_path(res: Resolution, points: list[Vec2], corner_radius: float = 0.0):
    """Build a closed Skia path through a list of scene-space points."""
    path = skia.Path()
    raster = [res.to_raster(p) for p in points]
    if corner_radius <= 0.0:
        path.moveTo(raster[0].x, raster[0].y)
        for p in raster[1:]:
            path.lineTo(p.x, p.y)
        path.close()
        return path

    count = len(raster)
    for i in range(count):
        prev, cur, nxt = raster[i - 1], raster[i], raster[(i + 1) % count]
        into = (prev - cur).normalized()
        out = (nxt - cur).normalized()
        limit = min(corner_radius, (prev - cur).length / 2, (nxt - cur).length / 2)
        a, b = cur + into * limit, cur + out * limit
        if i == 0:
            path.moveTo(a.x, a.y)
        else:
            path.lineTo(a.x, a.y)
        path.quadTo(cur.x, cur.y, b.x, b.y)
    path.close()
    return path


def degrees_between(a: Vec2, b: Vec2) -> float:
    """Signed angle in degrees from ``a`` to ``b``."""
    return math.degrees(math.atan2(a.cross(b), a.dot(b)))
