"""The physim command-line interface.

Needs the cli extra::

    pip install physim[cli]
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ..config import DebugConfig, RenderConfig
from ..types import PRESETS, Resolution
from .discover import find_scenes, load_module, pick_scene

app = typer.Typer(
    name="physim",
    help="Render physics animations to video.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _fail(message: str) -> None:
    """Print an error and exit with a non-zero status."""
    console.print(f"[bold red]error[/] {message}")
    raise typer.Exit(1)


@app.command()
def render(
    file: Path = typer.Argument(..., help="Python file defining one or more scenes."),
    scene: str | None = typer.Argument(None, help="Scene class name."),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path."),
    fmt: str = typer.Option("mp4", "--format", "-f", help="Container: mp4 or mkv."),
    fps: int | None = typer.Option(None, "--fps", help="Frames per second."),
    resolution: str | None = typer.Option(
        None,
        "--resolution",
        "-r",
        help=f"WIDTHxHEIGHT or a preset: {', '.join(sorted(PRESETS))}.",
    ),
    seconds: float | None = typer.Option(None, "--seconds", "-s", help="Override length."),
    physics: str | None = typer.Option(None, "--physics", "-p", help="Physics preset."),
    seed: int | None = typer.Option(None, "--seed", help="Random seed."),
    backend: str = typer.Option("auto", "--backend", "-b", help="Raster backend: auto/cpu/gpu."),
    hardware_encode: bool = typer.Option(
        False, "--hardware-encode", help="Use a hardware video encoder when available."
    ),
    motion_blur: int = typer.Option(0, "--motion-blur", help="Sub-frame samples per frame."),
    debug: bool = typer.Option(False, "--debug", "-d", help="Overlay fps/frametime/objects."),
    audio_only: bool = typer.Option(False, "--audio-only", help="Write only the audio track."),
    audio_file: Path | None = typer.Option(
        None, "--audio-file", help="Also write the audio to a separate file."
    ),
    no_audio: bool = typer.Option(False, "--no-audio", help="Skip audio entirely."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Hide the progress bar."),
) -> None:
    """Render a scene from a Python file to a video."""
    from yaspin import yaspin

    with yaspin(text=f"loading {file}", color="cyan") as spinner:
        try:
            module = load_module(file)
            scenes = find_scenes(module)
            scene_class = pick_scene(scenes, scene)
        except (FileNotFoundError, ImportError, ValueError) as exc:
            spinner.fail("✗")
            _fail(str(exc))
            return
        spinner.ok("✓")

    config = RenderConfig(
        fps=fps or 30,
        format=fmt,
        backend=backend,
        motion_blur=motion_blur,
        hardware_encode=hardware_encode,
        output=output,
    )
    if resolution:
        try:
            config.resolution = Resolution.parse(resolution)
        except ValueError as exc:
            _fail(str(exc))

    kwargs = {"config": config, "debug": DebugConfig(enabled=debug)}
    if physics:
        kwargs["physics"] = physics
    if seed is not None:
        kwargs["seed"] = seed

    try:
        instance = scene_class(**kwargs)
    except (TypeError, ValueError) as exc:
        _fail(f"could not build scene: {exc}")
        return

    instance.audio_config.enabled = not no_audio
    instance.audio_config.audio_only = audio_only
    instance.audio_config.export_separate = audio_file
    instance.build()
    if seconds is not None:
        instance.run(seconds)

    _print_plan(scene_class.__name__, instance, config, hardware_encode, physics, seed)
    try:
        path = instance.render(quiet=quiet)
    except Exception as exc:  # noqa: BLE001  (surface any render failure cleanly)
        _fail(f"render failed: {exc}")
        return

    used = getattr(instance, "backend", "cpu")
    encoder = "hardware" if hardware_encode else "software"
    console.print(f"[bold green]done[/] {path} [dim]({used} raster, {encoder} encode)[/]")


@app.command(name="list")
def list_scenes(
    file: Path = typer.Argument(..., help="Python file to inspect."),
) -> None:
    """List the scenes defined in a Python file."""
    try:
        scenes = find_scenes(load_module(file))
    except (FileNotFoundError, ImportError, ValueError) as exc:
        _fail(str(exc))
        return
    if not scenes:
        console.print("[yellow]no scenes found[/]")
        return

    table = Table(title=str(file))
    table.add_column("scene", style="cyan")
    table.add_column("docstring")
    for name, cls in scenes.items():
        doc = (cls.__doc__ or "").strip().split("\n")[0]
        table.add_row(name, doc)
    console.print(table)


@app.command()
def preview(
    file: Path = typer.Argument(..., help="Python file defining one or more scenes."),
    scene: str | None = typer.Argument(None, help="Scene class name."),
    scale: float = typer.Option(0.6, "--scale", help="Window size relative to the frame."),
    fps: int | None = typer.Option(None, "--fps", help="Frames per second."),
    debug: bool = typer.Option(False, "--debug", "-d", help="Overlay the stats box."),
) -> None:
    """Play a scene in a live preview window."""
    try:
        scene_class = pick_scene(find_scenes(load_module(file)), scene)
    except (FileNotFoundError, ImportError, ValueError) as exc:
        _fail(str(exc))
        return

    instance = scene_class(RenderConfig(fps=fps or 30), debug=DebugConfig(enabled=debug))
    try:
        instance.preview(scale=scale)
    except ImportError as exc:
        _fail(str(exc))


@app.command()
def info() -> None:
    """Show the installed version, optional features and available presets."""
    from .. import __version__
    from ..presets import available as presets_available
    from ..presets import physics_names
    from ..render.gpu import gpu_available

    table = Table(title=f"physim {__version__}")
    table.add_column("feature", style="cyan")
    table.add_column("status")

    def mark(ok: bool, hint: str) -> str:
        return "[green]yes[/]" if ok else f"[yellow]no[/] ({hint})"

    table.add_row("presets", mark(presets_available(), "pip install physim[presets]"))
    table.add_row("expr shapes", mark(_installed("sympy"), "pip install physim[expr]"))
    table.add_row("preview", mark(_installed("cv2"), "pip install physim[preview]"))
    table.add_row("midi", mark(_installed("mido"), "pip install physim[audio]"))
    table.add_row("gpu raster", mark(gpu_available(), "pip install physim[gpu]"))
    table.add_row("examples", mark(_installed("physim_examples"), "pip install physim[examples]"))
    table.add_row("physics presets", ", ".join(physics_names()))
    table.add_row("resolutions", ", ".join(sorted(PRESETS)))
    console.print(table)


def resolve_backend(requested: str) -> str:
    """Work out which raster backend a render will actually use.

    Only probes the GPU when it was asked for, since probing costs a subprocess.
    """
    if requested != "gpu":
        return "cpu"
    from ..render.gpu import gpu_available

    return "gpu" if gpu_available() else "cpu (gpu unavailable)"


def _print_plan(name, scene, config, hardware_encode, physics, seed) -> None:
    """Summarize what is about to be rendered, before any work happens."""
    backend = resolve_backend(config.backend)
    frames = scene.total_frames
    if not frames:
        length = "until stopped"
    elif getattr(scene, "may_stop_early", False):
        length = f"up to {frames / config.fps:.1f}s"
    else:
        length = f"{frames / config.fps:.1f}s"

    rows = [
        ("scene", name),
        ("output", str(config.output_path(name))),
        ("resolution", f"{config.resolution} @ {config.fps}fps · {config.format}"),
        ("length", length + (f" ({frames} frames max)" if frames else "")),
        ("raster", backend),
        ("encoder", f"{config.codec} ({'hardware' if hardware_encode else 'software'})"),
        ("physics", physics or "default"),
        ("objects", str(len(scene.objects))),
        ("seed", "random" if seed is None and scene.seed is None else str(scene.seed)),
    ]
    if config.motion_blur > 1:
        rows.append(("motion blur", f"{config.motion_blur} samples"))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim", justify="right")
    table.add_column(style="cyan")
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)
    console.print()


def _installed(module: str) -> bool:
    """Whether an optional module can be imported."""
    import importlib.util

    return importlib.util.find_spec(module) is not None


def main() -> None:
    """Entry point for the ``physim`` command."""
    app()
