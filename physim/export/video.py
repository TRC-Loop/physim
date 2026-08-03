"""Frame-by-frame video encoding with PyAV.

Frames are pushed in-process rather than piped to an ffmpeg binary, and the
whole timeline is rendered offline, so output never drops frames no matter how
many objects the scene holds.
"""

from __future__ import annotations

from fractions import Fraction
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
        """Encode one frame, given as RGB or RGBA uint8.

        RGBA is preferred: it is what the renderer holds natively, so it needs
        no copy on the way in.
        """
        if frame.shape[2] == 4:
            if not frame.flags["C_CONTIGUOUS"]:
                frame = np.ascontiguousarray(frame)
            video_frame = av.VideoFrame.from_ndarray(frame, format="rgba")
        else:
            video_frame = av.VideoFrame.from_ndarray(np.ascontiguousarray(frame), format="rgb24")
        for packet in self.stream.encode(video_frame):
            self.container.mux(packet)
        self.frames_written += 1

    def close(self) -> None:
        """Flush the encoder and finalize the file."""
        for packet in self.stream.encode(None):
            self.container.mux(packet)
        self.container.close()

    def __enter__(self) -> VideoWriter:
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def encode_audio_stream(container, stream, samples: np.ndarray, sample_rate: int) -> None:
    """Encode a float32 ``(channels, n)`` track into an open container.

    The track is split into encoder-sized frames with explicit timestamps;
    handing an encoder one huge frame produces packets it cannot timestamp.
    """
    channels = samples.shape[0]
    layout = "stereo" if channels == 2 else "mono"
    pcm = np.clip(samples, -1.0, 1.0).astype(np.float32)

    resampler = av.AudioResampler(format=stream.format.name, layout=layout, rate=sample_rate)
    frame_size = stream.frame_size or 1024
    time_base = Fraction(1, sample_rate)
    pts = 0

    for start in range(0, pcm.shape[1], frame_size):
        chunk = np.ascontiguousarray(pcm[:, start : start + frame_size])
        frame = av.AudioFrame.from_ndarray(chunk, format="fltp", layout=layout)
        frame.sample_rate = sample_rate
        frame.time_base = time_base
        frame.pts = pts
        pts += chunk.shape[1]
        for resampled in resampler.resample(frame):
            for packet in stream.encode(resampled):
                container.mux(packet)

    for resampled in resampler.resample(None):
        for packet in stream.encode(resampled):
            container.mux(packet)
    for packet in stream.encode(None):
        container.mux(packet)


def mux_audio(path: Path, samples: np.ndarray, config) -> Path:
    """Add an audio track to an already written video file.

    Done as a second pass because a container's header is written on the first
    muxed packet, and a stream added after that has no usable time base. The
    video is copied through without re-encoding, so this is cheap.
    """
    temp = path.with_name(f"{path.stem}.muxing{path.suffix}")
    with av.open(str(path)) as source, av.open(str(temp), mode="w") as target:
        video_in = source.streams.video[0]
        video_out = target.add_stream_from_template(video_in)

        audio = target.add_stream(config.codec, rate=config.sample_rate)
        audio.bit_rate = config.bitrate

        for packet in source.demux(video_in):
            if packet.dts is None:
                continue
            packet.stream = video_out
            target.mux(packet)

        encode_audio_stream(target, audio, samples, config.sample_rate)

    temp.replace(path)
    return path
