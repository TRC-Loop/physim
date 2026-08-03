"""Shared entry point so every example is runnable with ``python -m``."""

from __future__ import annotations

import sys


def run(scene_class, seconds: float | None = None) -> None:
    """Render a scene from the command line.

    Accepts the same handful of flags across every example::

        python -m physim_examples.bouncing_ball --debug --seconds 5 -o out.mp4
    """
    args = sys.argv[1:]
    debug = "--debug" in args or "-d" in args
    preview = "--preview" in args

    def flag(name: str, cast, default=None):
        """Read ``--name value`` from argv."""
        if name not in args:
            return default
        try:
            return cast(args[args.index(name) + 1])
        except (IndexError, ValueError):
            raise SystemExit(f"error: {name} needs a value") from None

    from physim import DebugConfig, RenderConfig

    config = RenderConfig(
        fps=flag("--fps", int, 30),
        format=flag("--format", str, "mp4"),
        output=flag("-o", str) or flag("--output", str),
    )
    if resolution := flag("--resolution", str):
        from physim import Resolution

        config.resolution = Resolution.parse(resolution)

    scene = scene_class(config, debug=DebugConfig(enabled=debug))
    scene.build()
    if (override := flag("--seconds", float, seconds)) is not None:
        scene.run(override)

    if preview:
        scene.preview()
        return
    path = scene.render()
    print(f"wrote {path}")
