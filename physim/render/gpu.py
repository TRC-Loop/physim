"""GPU raster support.

Skia's GPU backend needs a current GL context, and offline rendering has no
window to borrow one from. The optional ``glfw`` dependency creates a hidden
one::

    pip install physim[gpu]

Asking Skia for a context when none exists segfaults the process rather than
returning an error, so availability is probed once in a throwaway subprocess.
A crashing probe simply means "no GPU here" and the render carries on the CPU.
"""

from __future__ import annotations

import subprocess
import sys
import warnings

_PROBE = "\n".join(
    (
        "import glfw, skia",
        "assert glfw.init()",
        "glfw.window_hint(glfw.VISIBLE, glfw.FALSE)",
        "w = glfw.create_window(64, 64, 'probe', None, None)",
        "assert w",
        "glfw.make_context_current(w)",
        "c = skia.GrDirectContext.MakeGL()",
        "raise SystemExit(0 if c is not None else 1)",
    )
)

_available: bool | None = None
_window = None


def gpu_available(timeout: float = 30.0) -> bool:
    """Whether a usable Skia GPU context can be created, cached after the first call."""
    global _available
    if _available is not None:
        return _available
    try:
        import glfw  # noqa: F401
    except ImportError:
        _available = False
        return _available
    try:
        result = subprocess.run(
            [sys.executable, "-c", _PROBE],
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        _available = result.returncode == 0
    except (subprocess.SubprocessError, OSError):
        _available = False
    return _available


def _ensure_context() -> bool:
    """Create the hidden GL context this process renders into."""
    global _window
    if _window is not None:
        return True
    import glfw

    if not glfw.init():
        return False
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
    window = glfw.create_window(64, 64, "physim", None, None)
    if not window:
        return False
    glfw.make_context_current(window)
    _window = window
    return True


def make_gpu_surface(width: int, height: int):
    """Create a GPU-backed surface, or ``None`` when the GPU can't be used.

    Returns a ``(surface, context)`` pair on success.
    """
    if not gpu_available() or not _ensure_context():
        return None
    import skia

    try:
        context = skia.GrDirectContext.MakeGL()
        if context is None:
            return None
        info = skia.ImageInfo.MakeN32Premul(width, height)
        surface = skia.Surface.MakeRenderTarget(context, skia.Budgeted.kNo, info)
        if surface is None:
            return None
    except Exception:  # noqa: BLE001  (any gl failure means fall back)
        return None
    return surface, context


def warn_unavailable() -> None:
    """Warn that the GPU backend was requested but isn't usable here."""
    hint = (
        "install it with: pip install physim[gpu]"
        if not _has_glfw()
        else "no usable gl context on this machine"
    )
    warnings.warn(
        f"gpu backend unavailable ({hint}), rendering on cpu instead; "
        "hardware video encoding is still available via --hardware-encode",
        stacklevel=3,
    )


def _has_glfw() -> bool:
    """Whether the optional glfw dependency is installed."""
    try:
        import glfw  # noqa: F401
    except ImportError:
        return False
    return True
