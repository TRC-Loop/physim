"""Driving a scene through the renderer and into a file."""

from __future__ import annotations

import time
from contextlib import contextmanager
from pathlib import Path

from ..config import RenderConfig
from ..render import Renderer
from .video import VideoWriter, mux_audio


def _progress(total: int | None, quiet: bool):
    """Return an alive-progress bar, or a no-op context when quiet.

    ``total`` is left unset for runs that can stop early, otherwise finishing
    before the last frame makes the bar report an incomplete run.
    """
    if quiet:
        from contextlib import nullcontext

        return nullcontext(lambda *_: None)
    from alive_progress import alive_bar

    return alive_bar(total, title="rendering", enrich_print=False)


@contextmanager
def _step(message: str, quiet: bool):
    """Show a spinner for a step that would otherwise look like a hang.

    Each step ticks itself off on the way out, so successive steps stack as
    lines instead of overwriting one another.
    """
    if quiet:
        yield
        return
    from yaspin import yaspin

    spinner = yaspin(text=message, color="cyan")
    spinner.start()
    try:
        yield
    except Exception:
        spinner.fail("✗")
        raise
    else:
        spinner.ok("✓")


def _log(message: str, quiet: bool) -> None:
    """Print a progress line unless the render is quiet."""
    if not quiet:
        print(message)


def render_scene(
    scene,
    *,
    output: Path | str | None = None,
    quiet: bool = False,
    **overrides,
) -> Path:
    """Render a scene to a video file and return the path it wrote.

    Keyword overrides are applied to the scene's :class:`RenderConfig` first,
    so ``scene.render(fps=60, format="mkv")`` works without building a config.
    """
    config = _apply_overrides(scene.config, overrides)
    scene.config = config
    scene.build()

    path = Path(output) if output else config.output_path(type(scene).__name__)
    path.parent.mkdir(parents=True, exist_ok=True)

    renderer = Renderer(config, scene.debug)
    scene.stats.total_frames = scene.total_frames

    # a run that can end early would otherwise leave the bar looking failed
    open_ended = getattr(scene, "may_stop_early", False)
    bar_total = None if open_ended else scene.total_frames

    writer = VideoWriter(path, config)
    try:
        with _progress(bar_total, quiet) as bar:
            for _ in scene.frames():
                scene.stats.begin_frame()

                started = time.perf_counter()
                frame = renderer.render_rgba(scene)
                scene.stats.render_time = time.perf_counter() - started

                started = time.perf_counter()
                writer.write(frame)
                scene.stats.encode_time = time.perf_counter() - started

                scene.stats.end_frame()
                bar()
    finally:
        with _step("flushing the encoder", quiet):
            writer.close()

    frames = scene.stats.frame_index
    _log(
        f"  rendered {frames} frames ({frames / config.fps:.1f}s), "
        f"{scene.stats.total_collisions} collisions, {len(scene.objects)} objects left",
        quiet,
    )

    # sounds are queued while frames render, so the track is built once the
    # video file is closed, then muxed in as a second pass
    cfg = scene.audio_config
    if cfg.enabled and scene._sounds:
        with _step(f"building audio track ({len(scene._sounds)} sounds)", quiet):
            audio = _audio_track(scene)
        if audio is not None:
            with _step("muxing audio into the video", quiet):
                mux_audio(path, audio, cfg)
            if cfg.export_separate is not None:
                with _step(f"writing {cfg.export_separate}", quiet):
                    from ..audio import write_audio_file

                    write_audio_file(Path(cfg.export_separate), audio, cfg)
            _log(f"  audio: {audio.shape[1] / cfg.sample_rate:.1f}s, {cfg.codec}", quiet)
    elif cfg.enabled:
        _log("  audio: no sounds were triggered, writing video only", quiet)

    scene.backend = renderer.backend
    """Which raster backend the last render actually used."""

    if scene.debug.enabled and scene.debug.print_summary and not quiet:
        print_summary(scene, path, renderer.backend)
    return path


def _apply_overrides(config: RenderConfig, overrides: dict) -> RenderConfig:
    """Return a config with the given fields replaced."""
    if not overrides:
        return config
    from dataclasses import replace

    clean = {k: v for k, v in overrides.items() if v is not None}
    return replace(config, **clean) if clean else config


def _audio_track(scene):
    """Build the scene's audio track, or ``None`` when there is no sound."""
    if not scene.audio_config.enabled or not scene._sounds:
        return None
    from ..audio import mix

    return mix(scene._sounds, scene.audio_config, scene.time or 1.0)


def print_summary(scene, path: Path, backend: str) -> None:
    """Print a debug summary once a render finishes.

    Uses rich when it's installed, and falls back to plain text otherwise so
    core installs don't need it.
    """
    stats = scene.stats
    rows = [
        ("output", str(path)),
        ("resolution", str(scene.config.resolution)),
        ("fps", str(scene.config.fps)),
        ("backend", backend),
        ("frames", str(stats.frame_index)),
        ("objects", str(stats.object_count)),
        ("collisions", str(stats.total_collisions)),
        ("events", str(stats.events_fired)),
        ("avg fps", f"{stats.average_fps:.1f}"),
        ("avg frametime", f"{stats.frametime_ms:.2f} ms"),
        ("elapsed", f"{stats.elapsed:.2f} s"),
    ]
    try:
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        print(f"\nphysim · {type(scene).__name__}")
        for label, value in rows:
            print(f"  {label:<14} {value}")
        return

    table = Table(title=f"physim · {type(scene).__name__}", title_style="bold")
    table.add_column("stat", style="cyan")
    table.add_column("value", justify="right")
    for label, value in rows:
        table.add_row(label, value)
    Console().print(table)
