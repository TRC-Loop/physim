"""Sound: synthesized tones, melodies, samples and the offline mixer.

Audio is built as a complete track and muxed into the exported file, so it
lines up with the physics exactly regardless of render speed.
"""

from .melody import Melody
from .mixer import load_sample, mix, write_audio_file
from .synth import (
    NOTE_OFFSETS,
    WAVEFORMS,
    Envelope,
    Tone,
    midi_to_frequency,
    note,
    note_to_frequency,
)

__all__ = [
    "NOTE_OFFSETS",
    "WAVEFORMS",
    "Envelope",
    "Melody",
    "Tone",
    "load_sample",
    "midi_to_frequency",
    "mix",
    "note",
    "note_to_frequency",
    "write_audio_file",
]
