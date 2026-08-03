"""Per-frame render statistics.

An instance lives on every scene as ``scene.stats`` and stays populated
whether or not the debug overlay is drawn, so these values can be read from
code, logged, or asserted on in tests.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class Stats:
    """Timing and object counters for the render in progress.

    All durations are in seconds; the ``*_ms`` properties convert for display.
    """

    frame_index: int = 0
    total_frames: int | None = None
    scene_time: float = 0.0

    frametime: float = 0.0
    physics_time: float = 0.0
    render_time: float = 0.0
    encode_time: float = 0.0

    object_count: int = 0
    collision_count: int = 0
    """Collisions resolved in the current frame."""

    total_collisions: int = 0
    events_fired: int = 0

    started_at: float = field(default_factory=time.perf_counter)
    history: deque[float] = field(default_factory=lambda: deque(maxlen=120))
    """Recent frametimes, used for the rolling average."""

    def begin_frame(self) -> None:
        """Reset the per-frame counters."""
        self.collision_count = 0
        self._frame_start = time.perf_counter()

    def end_frame(self) -> None:
        """Close out the frame and record its duration."""
        self.frametime = time.perf_counter() - getattr(self, "_frame_start", time.perf_counter())
        self.history.append(self.frametime)
        self.frame_index += 1

    @property
    def fps(self) -> float:
        """Instantaneous frames per second from the last frametime."""
        return 1.0 / self.frametime if self.frametime > 0 else 0.0

    @property
    def average_fps(self) -> float:
        """Rolling average frames per second over recent frames."""
        if not self.history:
            return 0.0
        mean = sum(self.history) / len(self.history)
        return 1.0 / mean if mean > 0 else 0.0

    @property
    def frametime_ms(self) -> float:
        """Last frametime in milliseconds."""
        return self.frametime * 1000.0

    @property
    def physics_ms(self) -> float:
        """Physics step duration in milliseconds."""
        return self.physics_time * 1000.0

    @property
    def render_ms(self) -> float:
        """Rasterization duration in milliseconds."""
        return self.render_time * 1000.0

    @property
    def encode_ms(self) -> float:
        """Encode duration in milliseconds."""
        return self.encode_time * 1000.0

    @property
    def elapsed(self) -> float:
        """Wall-clock seconds since the render started."""
        return time.perf_counter() - self.started_at

    @property
    def eta(self) -> float | None:
        """Estimated seconds remaining, or ``None`` when the length is unknown."""
        if not self.total_frames or self.frame_index == 0:
            return None
        remaining = self.total_frames - self.frame_index
        if remaining <= 0:
            return 0.0
        return remaining * (self.elapsed / self.frame_index)

    @property
    def progress(self) -> float | None:
        """Completion from 0 to 1, or ``None`` when the length is unknown."""
        if not self.total_frames:
            return None
        return min(1.0, self.frame_index / self.total_frames)

    def as_dict(self) -> dict[str, float | int | None]:
        """Snapshot every statistic as plain values."""
        return {
            "frame_index": self.frame_index,
            "total_frames": self.total_frames,
            "scene_time": self.scene_time,
            "frametime_ms": self.frametime_ms,
            "fps": self.fps,
            "average_fps": self.average_fps,
            "physics_ms": self.physics_ms,
            "render_ms": self.render_ms,
            "encode_ms": self.encode_ms,
            "object_count": self.object_count,
            "collision_count": self.collision_count,
            "total_collisions": self.total_collisions,
            "events_fired": self.events_fired,
            "elapsed": self.elapsed,
            "eta": self.eta,
        }

    def overlay_lines(self, config) -> list[str]:
        """Build the text rows for the debug overlay from a ``DebugConfig``."""
        lines: list[str] = []
        if self.total_frames:
            lines.append(f"frame      {self.frame_index} / {self.total_frames}")
        else:
            lines.append(f"frame      {self.frame_index}")
        if config.show_frametime:
            lines.append(f"frametime  {self.frametime_ms:.1f} ms")
        if config.show_fps:
            lines.append(f"fps        {self.fps:.0f} (avg {self.average_fps:.0f})")
        if config.show_objects:
            lines.append(f"objects    {self.object_count}")
        if config.show_collisions:
            lines.append(f"collisions {self.collision_count}")
        if config.show_timings:
            lines.append(
                f"phys {self.physics_ms:.1f}ms  render {self.render_ms:.1f}ms"
                f"  enc {self.encode_ms:.1f}ms"
            )
        if config.show_eta and self.eta is not None:
            lines.append(f"eta        {self.eta:.1f}s")
        return lines
