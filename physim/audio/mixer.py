"""Mixing queued sounds into a single audio track.

Sounds are placed at the exact scene time they were triggered. Because frames
are rendered offline, timing is sample-accurate rather than dependent on how
fast the render ran.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..config import AudioConfig
from .synth import Tone


def load_sample(path: str | Path, sample_rate: int) -> np.ndarray:
    """Decode an audio file into a mono float32 buffer, resampled if needed."""
    import av

    with av.open(str(path)) as container:
        stream = container.streams.audio[0]
        chunks = [frame.to_ndarray().astype(np.float32) for frame in container.decode(stream)]
        source_rate = stream.rate

    if not chunks:
        return np.zeros(0, dtype=np.float32)

    data = np.concatenate([c.reshape(c.shape[0], -1) for c in chunks], axis=1)
    mono = data.mean(axis=0)
    if np.issubdtype(data.dtype, np.integer) or mono.max(initial=0.0) > 1.5:
        mono = mono / 32768.0

    if source_rate != sample_rate:
        target_len = int(len(mono) * sample_rate / source_rate)
        mono = np.interp(
            np.linspace(0, len(mono), target_len, endpoint=False),
            np.arange(len(mono)),
            mono,
        ).astype(np.float32)
    return mono.astype(np.float32)


def _to_buffer(sound, sample_rate: int) -> np.ndarray:
    """Turn any queued sound into a mono float32 buffer."""
    if isinstance(sound, Tone):
        return sound.render(sample_rate)
    if isinstance(sound, np.ndarray):
        return sound.astype(np.float32)
    return load_sample(sound, sample_rate)


def mix(sounds: list[tuple[float, object]], config: AudioConfig, duration: float) -> np.ndarray:
    """Render queued ``(time, sound)`` pairs into a ``(channels, n)`` float32 track."""
    rate = config.sample_rate
    total = max(1, int((duration + 2.0) * rate))
    track = np.zeros(total, dtype=np.float32)

    for start, sound in sounds:
        buffer = _to_buffer(sound, rate)
        if buffer.size == 0:
            continue
        offset = max(0, int(start * rate))
        end = min(total, offset + len(buffer))
        if end <= offset:
            continue
        track[offset:end] += buffer[: end - offset]

    track *= config.master_volume
    peak = float(np.abs(track).max(initial=0.0))
    if peak > 1.0:
        track /= peak

    trimmed = track[: max(1, int(duration * rate))]
    if config.channels == 1:
        return trimmed.reshape(1, -1)
    return np.vstack([trimmed, trimmed])


def write_audio_file(path: Path, samples: np.ndarray, config: AudioConfig) -> Path:
    """Write a finished track to a standalone audio file."""
    import av

    channels = samples.shape[0]
    layout = "stereo" if channels == 2 else "mono"
    with av.open(str(path), mode="w") as container:
        stream = container.add_stream(config.codec, rate=config.sample_rate)
        stream.bit_rate = config.bitrate

        pcm = np.clip(samples, -1.0, 1.0)
        pcm = (pcm * 32767.0).astype(np.int16)
        flat = pcm.reshape(1, -1) if channels == 1 else pcm.T.reshape(1, -1).copy()
        frame = av.AudioFrame.from_ndarray(flat, format="s16", layout=layout)
        frame.sample_rate = config.sample_rate
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)
    return path
