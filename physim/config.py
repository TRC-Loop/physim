"""Public configuration objects for rendering, debugging and export."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .color import Color, ColorLike, Gradient
from .types import Resolution

#: raster backends the renderer can use
BACKENDS = ("auto", "cpu", "gpu")

#: container formats the exporter can write
FORMATS = ("mp4", "mkv")


@dataclass
class RenderConfig:
    """How a scene is rasterized and encoded.

    Defaults target the square social format: 1080x1080 at 30 fps.
    """

    resolution: Resolution = field(default_factory=lambda: Resolution(1080, 1080))
    fps: int = 30
    background: ColorLike | Gradient = "#0b0b12"
    background_image: Path | None = None

    backend: str = "auto"
    """Raster backend: ``"auto"``, ``"cpu"`` or ``"gpu"``. Falls back to CPU."""

    antialias: bool = True

    motion_blur: int = 0
    """Sub-frame samples blended per frame. 0 or 1 disables motion blur."""

    format: str = "mp4"
    codec: str = "h264"
    bitrate: int = 12_000_000
    hardware_encode: bool = False
    """Prefer a platform hardware encoder when one is available."""

    output: Path | None = None
    """Explicit output path. Defaults to ``out/<SceneName>.<format>``."""

    def __post_init__(self) -> None:
        self.resolution = Resolution.parse(self.resolution)
        if self.fps <= 0:
            raise ValueError("fps must be positive")
        if self.backend not in BACKENDS:
            raise ValueError(f"backend must be one of {BACKENDS}, got {self.backend!r}")
        if self.format not in FORMATS:
            raise ValueError(f"format must be one of {FORMATS}, got {self.format!r}")
        if isinstance(self.output, str):
            self.output = Path(self.output)

    @property
    def frame_duration(self) -> float:
        """Seconds of scene time per rendered frame."""
        return 1.0 / self.fps

    @property
    def width(self) -> int:
        """Frame width in pixels."""
        return self.resolution.width

    @property
    def height(self) -> int:
        """Frame height in pixels."""
        return self.resolution.height

    def background_color(self) -> Color | Gradient:
        """Background as a concrete color or gradient."""
        if isinstance(self.background, Gradient):
            return self.background
        return Color.of(self.background)

    def output_path(self, scene_name: str) -> Path:
        """Resolve the output file for a scene, creating parent directories."""
        path = self.output or Path("out") / f"{scene_name}.{self.format}"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


@dataclass
class DebugConfig:
    """What the debug flag collects and draws.

    Every statistic stays available on :class:`physim.stats.Stats` whether or
    not the overlay is drawn, so it can be read programmatically.
    """

    enabled: bool = False
    overlay: bool = True
    """Draw the stats box onto the rendered frames."""

    print_summary: bool = True
    """Print a summary table to the terminal when the render finishes."""

    show_fps: bool = True
    show_frametime: bool = True
    show_objects: bool = True
    show_collisions: bool = True
    show_timings: bool = True
    """Show the physics/render/encode breakdown."""

    show_eta: bool = True
    show_bounds: bool = False
    """Outline each object's collision shape."""

    show_velocity: bool = False
    """Draw a velocity vector on every physics object."""

    corner: str = "top_left"
    """One of ``"top_left"``, ``"top_right"``, ``"bottom_left"``, ``"bottom_right"``."""

    text_color: ColorLike = "#00ff9c"
    background_color: ColorLike = "#000000cc"
    font_size: float = 22.0
    margin: float = 20.0

    def __post_init__(self) -> None:
        corners = ("top_left", "top_right", "bottom_left", "bottom_right")
        if self.corner not in corners:
            raise ValueError(f"corner must be one of {corners}, got {self.corner!r}")


@dataclass
class AudioConfig:
    """How the scene's audio track is synthesized and muxed."""

    enabled: bool = True
    sample_rate: int = 48_000
    channels: int = 2
    codec: str = "aac"
    bitrate: int = 192_000
    master_volume: float = 0.8

    mux: bool = True
    """Write the audio into the video container."""

    export_separate: Path | None = None
    """Also write a standalone audio file to this path."""

    audio_only: bool = False
    """Skip video entirely and write only the audio track."""

    def __post_init__(self) -> None:
        if isinstance(self.export_separate, str):
            self.export_separate = Path(self.export_separate)
