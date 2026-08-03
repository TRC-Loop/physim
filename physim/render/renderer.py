"""The Skia-backed frame renderer.

Objects don't touch Skia directly; they call the drawing helpers on this class,
which keeps the graphics backend swappable and the object code readable.
"""

from __future__ import annotations

import numpy as np
import skia

from ..color import Color, Gradient
from ..config import DebugConfig, RenderConfig
from ..types import Resolution, Vec2
from . import fonts
from .gpu import make_gpu_surface, warn_unavailable
from .paint import arc_path, blur_filter, make_paint, polygon_path


class Renderer:
    """Rasterizes a scene into RGB frames."""

    def __init__(self, config: RenderConfig, debug: DebugConfig | None = None) -> None:
        self.config = config
        self.debug = debug or DebugConfig()
        self.res: Resolution = config.resolution
        self.time = 0.0
        """Scene time of the frame being drawn, used to resolve dynamic colors."""

        self.gpu_context = None
        self.surface = self._make_surface()

    def _make_surface(self):
        """Create the raster surface, using the GPU only when explicitly asked.

        ``auto`` stays on the CPU: offline rendering has no window, so there is
        usually no GL context to attach to, and the CPU path is dependable.
        """
        width, height = self.res.width, self.res.height
        if self.config.backend == "gpu":
            made = make_gpu_surface(width, height)
            if made is not None:
                surface, self.gpu_context = made
                return surface
            warn_unavailable()
        return skia.Surface(width, height)

    @property
    def backend(self) -> str:
        """Which backend actually ended up in use."""
        return "gpu" if self.gpu_context is not None else "cpu"

    def render(self, scene) -> np.ndarray:
        """Draw a scene and return the frame as an RGB uint8 array."""
        self.time = scene.time
        canvas = self.surface.getCanvas()
        self._draw_background(canvas)

        samples = max(1, self.config.motion_blur)
        if samples > 1:
            return self._render_motion_blurred(scene, samples)

        self._draw_objects(canvas, scene)
        if self.debug.enabled and self.debug.overlay:
            self.draw_debug_overlay(canvas, scene)
        return self.to_array()

    def _render_motion_blurred(self, scene, samples: int) -> np.ndarray:
        """Average several sub-frame samples to smear fast motion.

        Each sample rewinds moving objects along their own velocity by a
        fraction of the frame, so the blur follows real trajectories without
        disturbing the simulation itself.
        """
        dt = self.config.frame_duration
        bodies = [o for o in scene.objects if getattr(o, "physical", False)]
        original = [b.transform.position for b in bodies]
        accumulator = np.zeros((self.res.height, self.res.width, 3), dtype=np.float32)

        try:
            for i in range(samples):
                shift = (i / samples) * dt
                for body, start in zip(bodies, original, strict=False):
                    body.transform.position = start - body.velocity * shift
                canvas = self.surface.getCanvas()
                self._draw_background(canvas)
                self._draw_objects(canvas, scene)
                accumulator += self.to_array()
        finally:
            for body, start in zip(bodies, original, strict=False):
                body.transform.position = start

        frame = (accumulator / samples).astype(np.uint8)
        if self.debug.enabled and self.debug.overlay:
            canvas = self.surface.getCanvas()
            self._blit(canvas, frame)
            self.draw_debug_overlay(canvas, scene)
            return self.to_array()
        return frame

    def _blit(self, canvas, frame: np.ndarray) -> None:
        """Draw a finished RGB frame back onto the surface."""
        rgba = np.dstack([frame, np.full(frame.shape[:2], 255, dtype=np.uint8)])
        canvas.drawImage(skia.Image.fromarray(np.ascontiguousarray(rgba)), 0, 0)

    def _draw_background(self, canvas) -> None:
        """Fill the frame with the configured background."""
        background = self.config.background_color()
        if isinstance(background, Gradient):
            paint = make_paint(
                background, self.res, self.time, extent=max(self.res.width, self.res.height)
            )
            canvas.drawPaint(paint)
        else:
            r, g, b, a = background.to_rgba8()
            canvas.clear(skia.Color(r, g, b, a))

    def _draw_objects(self, canvas, scene) -> None:
        """Draw every visible object in z order."""
        for obj in sorted(scene.objects, key=lambda o: o.z):
            if obj.visible and obj.alive:
                obj.render(canvas, self)

    def to_array(self) -> np.ndarray:
        """Snapshot the surface as an RGB uint8 array."""
        image = self.surface.makeImageSnapshot()
        return image.toarray(colorType=skia.kRGB_888x_ColorType)[:, :, :3]

    def _paint_for(self, obj, center: Vec2, extent: float, stroke: bool = False):
        """Build the fill or stroke paint for an object."""
        value = obj.stroke if stroke else obj.fill
        width = obj.stroke_width if stroke else 0.0
        if stroke and width <= 0.0:
            return None
        return make_paint(
            value,
            self.res,
            self.time,
            center=center,
            extent=extent,
            opacity=obj.transform.opacity,
            stroke_width=width,
            antialias=self.config.antialias,
        )

    def draw_circle(self, canvas, obj, center: Vec2, radius: float) -> None:
        """Draw a filled and optionally stroked circle."""
        cx, cy = self.res.to_raster(center)
        for stroke in (False, True):
            paint = self._paint_for(obj, center, radius, stroke)
            if paint is not None:
                canvas.drawCircle(cx, cy, radius, paint)

    def draw_polygon(self, canvas, obj, points: list[Vec2], corner_radius: float = 0.0) -> None:
        """Draw a closed polygon through scene-space points."""
        path = polygon_path(self.res, points, corner_radius)
        extent = max((p - obj.pos).length for p in points) if points else 1.0
        for stroke in (False, True):
            paint = self._paint_for(obj, obj.pos, extent, stroke)
            if paint is not None:
                canvas.drawPath(path, paint)

    def draw_rect(
        self,
        canvas,
        obj,
        center: Vec2,
        width: float,
        height: float,
        corner_radius: float = 0.0,
        outline: bool = False,
    ) -> None:
        """Draw a rectangle, filled or as an outline."""
        cx, cy = self.res.to_raster(center)
        rect = skia.Rect.MakeLTRB(cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2)
        extent = max(width, height) / 2.0
        order = (True,) if outline else (False, True)
        for stroke in order:
            paint = self._paint_for(obj, center, extent, stroke)
            if paint is None:
                continue
            if corner_radius > 0.0:
                canvas.drawRoundRect(rect, corner_radius, corner_radius, paint)
            else:
                canvas.drawRect(rect, paint)

    def draw_ring(
        self,
        canvas,
        obj,
        center: Vec2,
        radius: float,
        thickness: float,
        gap_degrees: float = 0.0,
        gap_angle: float = 0.0,
    ) -> None:
        """Draw a ring, skipping the angular gap when there is one."""
        paint = make_paint(
            obj.stroke or obj.fill or "#ffffff",
            self.res,
            self.time,
            center=center,
            extent=radius,
            opacity=obj.transform.opacity,
            stroke_width=thickness,
            antialias=self.config.antialias,
        )
        if paint is None:
            return
        if gap_degrees <= 0.0:
            cx, cy = self.res.to_raster(center)
            canvas.drawCircle(cx, cy, radius, paint)
            return
        sweep = 360.0 - gap_degrees
        canvas.drawPath(arc_path(self.res, center, radius, gap_angle + gap_degrees, sweep), paint)

    def draw_text(self, canvas, obj) -> None:
        """Draw a styled text object, including its background and decorations."""
        skia_font = fonts.font(obj.font, obj.size, obj.bold, obj.italic)
        lines = obj.lines
        line_step = obj.size * obj.line_height
        widths = [skia_font.measureText(line) for line in lines]
        block_height = line_step * len(lines)
        cx, cy = self.res.to_raster(obj.pos)
        top = cy - block_height / 2.0 + obj.size * 0.75

        if obj.background is not None:
            pad = obj.background_padding
            half_w = (max(widths) if widths else 0.0) / 2.0 + pad
            rect = skia.Rect.MakeLTRB(
                cx - half_w,
                cy - block_height / 2.0 - pad,
                cx + half_w,
                cy + block_height / 2.0 + pad,
            )
            bg = make_paint(
                obj.background,
                self.res,
                self.time,
                center=obj.pos,
                extent=half_w,
                opacity=obj.transform.opacity * obj.background_opacity,
                antialias=self.config.antialias,
            )
            if bg is not None:
                canvas.drawRoundRect(rect, obj.background_radius, obj.background_radius, bg)

        paint = self._paint_for(obj, obj.pos, max(widths) if widths else 1.0)
        if paint is None:
            return
        for i, line in enumerate(lines):
            width = widths[i]
            x = cx - width / 2.0 if obj.align == "center" else cx
            if obj.align == "right":
                x = cx - width
            y = top + line_step * i
            canvas.drawString(line, x, y, skia_font, paint)
            if obj.underline:
                canvas.drawRect(
                    skia.Rect.MakeLTRB(x, y + obj.size * 0.12, x + width, y + obj.size * 0.17),
                    paint,
                )
            if obj.strikethrough:
                canvas.drawRect(
                    skia.Rect.MakeLTRB(x, y - obj.size * 0.28, x + width, y - obj.size * 0.23),
                    paint,
                )

    def draw_mask(self, canvas, obj, mask, center: Vec2, bounds: float) -> None:
        """Draw a boolean grid as a filled region, used by implicit shapes."""
        color = make_paint(obj.fill, self.res, self.time, center=center, extent=bounds)
        if color is None:
            return
        rgba = np.zeros((*mask.shape, 4), dtype=np.uint8)
        argb = color.getColor()
        rgba[mask] = [
            (argb >> 16) & 0xFF,
            (argb >> 8) & 0xFF,
            argb & 0xFF,
            int(255 * obj.transform.opacity),
        ]
        # the grid is sampled y-up, the raster is y-down
        image = skia.Image.fromarray(np.ascontiguousarray(rgba[::-1]))
        cx, cy = self.res.to_raster(center)
        dest = skia.Rect.MakeLTRB(cx - bounds, cy - bounds, cx + bounds, cy + bounds)
        canvas.drawImageRect(image, dest, skia.SamplingOptions())

    def draw_glow(self, canvas, obj, center: Vec2, radius: float, strength: float) -> None:
        """Draw a blurred copy of a circle underneath it, for a neon look."""
        paint = self._paint_for(obj, center, radius)
        if paint is None:
            return
        paint.setImageFilter(blur_filter(radius * strength))
        cx, cy = self.res.to_raster(center)
        canvas.drawCircle(cx, cy, radius, paint)

    def draw_trail(self, canvas, obj, points: list[Vec2], radius: float, fade: float) -> None:
        """Draw a fading path behind a moving object."""
        if len(points) < 2:
            return
        count = len(points)
        for i, point in enumerate(points):
            t = (i + 1) / count
            paint = make_paint(
                obj.fill,
                self.res,
                self.time,
                center=point,
                extent=radius,
                opacity=obj.transform.opacity * t * fade,
                antialias=self.config.antialias,
            )
            if paint is None:
                continue
            cx, cy = self.res.to_raster(point)
            canvas.drawCircle(cx, cy, radius * t, paint)

    def draw_debug_overlay(self, canvas, scene) -> None:
        """Draw the stats box in the configured corner."""
        cfg = self.debug
        lines = scene.stats.overlay_lines(cfg)
        if not lines:
            return
        skia_font = fonts.font(None, cfg.font_size, bold=False, italic=False)
        widths = [skia_font.measureText(line) for line in lines]
        pad, step = 12.0, cfg.font_size * 1.35
        box_w, box_h = max(widths) + pad * 2, step * len(lines) + pad * 2

        left = cfg.margin if "left" in cfg.corner else self.res.width - box_w - cfg.margin
        top = cfg.margin if "top" in cfg.corner else self.res.height - box_h - cfg.margin

        bg = Color.of(cfg.background_color).to_rgba8()
        bg_paint = skia.Paint(Color=skia.Color(*bg), AntiAlias=True)
        canvas.drawRoundRect(
            skia.Rect.MakeLTRB(left, top, left + box_w, top + box_h), 8, 8, bg_paint
        )

        fg = Color.of(cfg.text_color).to_rgba8()
        text_paint = skia.Paint(Color=skia.Color(*fg), AntiAlias=True)
        for i, line in enumerate(lines):
            canvas.drawString(
                line, left + pad, top + pad + cfg.font_size + step * i, skia_font, text_paint
            )
