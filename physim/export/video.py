"""Frame-by-frame video encoding with PyAV.

Frames are pushed in-process rather than piped to an ffmpeg binary, and the
whole timeline is rendered offline, so output never drops frames no matter how
many objects the scene holds.
"""

from __future__ import annotations

from pathlib import Path

import av
import numpy as np

from ..config import RenderConfig

#: hardware encoders tried when ``hardware_encode`` is on, in preference order
HARDWARE_CODECS = {
    "h264": ["h264_videotoolbox", "h264_nvenc", "h264_qsv", "h264_vaapi"],
    "hevc": ["hevc_videotoolbox", "hevc_nvenc"],
}

#: containers that accept each codec
CONTAINER_CODECS = {
    "mp4": ("h264", "hevc"),
    "mkv": ("h264", "hevc", "vp9"),
}


def pick_codec(config: RenderConfig) -> str:
    """Choose an encoder name, preferring hardware when it's available."""
    if not config.hardware_encode:
        return config.codec
    for candidate in HARDWARE_CODECS.get(config.codec, []):
        try:
            av.codec.Codec(candidate, "w")
        except Exception:  # noqa: BLE001  (unavailable encoders raise various errors)
            continue
        return candidate
    return config.codec


class VideoWriter:
    """Encodes frames into an MP4 or MKV container."""

    def __init__(self, path: Path, config: RenderConfig) -> None:
        self.path = Path(path)
        self.config = config
        self.codec = pick_codec(config)
        self.frames_written = 0

        self.container = av.open(str(self.path), mode="w")
        self.stream = self.container.add_stream(self.codec, rate=config.fps)
        self.stream.width = config.width
        self.stream.height = config.height
        self.stream.pix_fmt = "yuv420p"
        self.stream.bit_rate = config.bitrate

    def write(self, frame: np.ndarray) -> None:
        """Encode one RGB uint8 frame."""
        video_frame = av.VideoFrame.from_ndarray(np.ascontiguousarray(frame), format="rgb24")
        for packet in self.stream.encode(video_frame):
            self.container.mux(packet)
        self.frames_written += 1

    def add_audio(self, samples: np.ndarray, sample_rate: int, codec: str, bitrate: int) -> None:
        """Mux a finished audio track into the container.

        ``samples`` is float32 shaped ``(channels, n)`` in the range -1 to 1.
        """
        channels = samples.shape[0]
        layout = "stereo" if channels == 2 else "mono"
        stream = self.container.add_stream(codec, rate=sample_rate)
        stream.bit_rate = bitrate

        pcm = np.clip(samples, -1.0, 1.0)
        pcm = (pcm * 32767.0).astype(np.int16)
        frame = av.AudioFrame.from_ndarray(
            pcm.reshape(1, -1) if channels == 1 else pcm.T.reshape(1, -1).copy(),
            format="s16",
            layout=layout,
        )
        frame.sample_rate = sample_rate
        for packet in stream.encode(frame):
            self.container.mux(packet)
        for packet in stream.encode(None):
            self.container.mux(packet)

    def close(self) -> None:
        """Flush the encoder and finalize the file."""
        for packet in self.stream.encode(None):
            self.container.mux(packet)
        self.container.close()

    def __enter__(self) -> VideoWriter:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
