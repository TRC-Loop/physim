"""The physim command-line interface.

Installed as the ``physim`` command with the cli extra::

    pip install physim[cli]
"""

from __future__ import annotations

_HINT = "the physim command needs typer and rich; install them with: pip install physim[cli]"


def main() -> None:
    """Entry point for the ``physim`` command, with a clear hint when deps are missing."""
    try:
        from .app import main as run
    except ImportError as exc:
        raise SystemExit(f"error: {_HINT}") from exc
    run()


def __getattr__(name: str):
    """Expose ``app`` lazily so importing this module never requires typer."""
    if name == "app":
        from .app import app

        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["main"]
