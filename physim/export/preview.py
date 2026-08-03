"""Live preview window.

Needs the preview extra::

    pip install physim[preview]
"""

from __future__ import annotations

import time

from ..render import Renderer

_HINT = "the live preview needs opencv; install it with: pip install physim[preview]"


def play_live(sound, config) -> None:
    """Play a sound immediately through the sound card, if one is usable.

    Preview audio is best-effort: a missing sounddevice, or no output device,
    leaves the window silent rather than failing the preview.
    """
    try:
        import sounddevice as sd
    except ImportError:
        return
    from ..audio.mixer import _to_buffer

    try:
        buffer = _to_buffer(sound, config.sample_rate)
        if buffer.size:
            sd.play(buffer * config.master_volume, config.sample_rate)
    except Exception:  # noqa: BLE001  (audio output is optional, never fatal)
        return


def preview_scene(scene, *, scale: float = 1.0, audio: bool = True, **overrides) -> None:
    """Play a scene in a window, pacing playback to the configured framerate.

    Press ``q`` or Escape to close, and space to pause. Sounds triggered by
    events play live when the preview extra is installed.
    """
    try:
        import cv2
    except ImportError as exc:
        raise ImportError(_HINT) from exc

    from .render import _apply_overrides

    scene.config = _apply_overrides(scene.config, overrides)
    scene.build()

    renderer = Renderer(scene.config, scene.debug)
    scene.stats.total_frames = scene.total_frames
    window = f"physim · {type(scene).__name__}"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    if scale != 1.0:
        cv2.resizeWindow(window, int(scene.config.width * scale), int(scene.config.height * scale))

    target = scene.config.frame_duration
    paused = False
    heard = 0
    try:
        for _ in scene.frames():
            scene.stats.begin_frame()
            started = time.perf_counter()
            frame = renderer.render(scene)
            scene.stats.render_time = time.perf_counter() - started

            if audio and scene.audio_config.enabled and len(scene._sounds) > heard:
                for _, sound in scene._sounds[heard:]:
                    play_live(sound, scene.audio_config)
                heard = len(scene._sounds)

            cv2.imshow(window, frame[:, :, ::-1])
            scene.stats.end_frame()

            wait = max(1, int((target - scene.stats.frametime) * 1000))
            key = cv2.waitKey(1 if paused else wait) & 0xFF
            if key in (27, ord("q")):
                break
            if key == ord(" "):
                paused = not paused
            while paused:
                key = cv2.waitKey(50) & 0xFF
                if key == ord(" "):
                    paused = False
                elif key in (27, ord("q")):
                    return
    finally:
        cv2.destroyWindow(window)
