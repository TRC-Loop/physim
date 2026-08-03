"""A small oscillator synth.

Notes are generated with numpy rather than sampled, so melodies need no
soundfonts, no extra dependencies and no audio files.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: semitone offsets within an octave
NOTE_OFFSETS = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}

#: available oscillator shapes
WAVEFORMS = ("sine", "square", "triangle", "saw", "noise")


def note_to_frequency(note: str | float) -> float:
    """Convert a note name like ``"C4"`` or ``"F#5"`` into a frequency in hertz."""
    if isinstance(note, (int, float)):
        return float(note)
    text = note.strip()
    octave_start = len(text)
    for i, ch in enumerate(text):
        if ch.isdigit() or (ch == "-" and i > 0):
            octave_start = i
            break
    name, octave_text = text[:octave_start], text[octave_start:]
    if name not in NOTE_OFFSETS:
        raise ValueError(f"unknown note {note!r}")
    octave = int(octave_text) if octave_text else 4
    semitones = NOTE_OFFSETS[name] + (octave + 1) * 12 - 69
    return 440.0 * (2.0 ** (semitones / 12.0))


def midi_to_frequency(midi_note: int) -> float:
    """Convert a MIDI note number into a frequency in hertz."""
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


@dataclass
class Envelope:
    """A simple attack/decay/sustain/release amplitude shape."""

    attack: float = 0.005
    decay: float = 0.08
    sustain: float = 0.6
    release: float = 0.15

    def apply(self, samples: np.ndarray, sample_rate: int) -> np.ndarray:
        """Shape a mono buffer with this envelope."""
        n = len(samples)
        env = np.ones(n, dtype=np.float32)
        a = min(n, int(self.attack * sample_rate))
        d = min(n - a, int(self.decay * sample_rate))
        r = min(n - a - d, int(self.release * sample_rate))

        if a:
            env[:a] = np.linspace(0.0, 1.0, a, dtype=np.float32)
        if d:
            env[a : a + d] = np.linspace(1.0, self.sustain, d, dtype=np.float32)
        env[a + d : n - r] = self.sustain
        if r:
            env[n - r :] = np.linspace(self.sustain, 0.0, r, dtype=np.float32)
        return samples * env


@dataclass
class Tone:
    """A single synthesized note."""

    frequency: float = 440.0
    duration: float = 0.25
    waveform: str = "sine"
    volume: float = 0.5
    envelope: Envelope = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.waveform not in WAVEFORMS:
            raise ValueError(f"waveform must be one of {WAVEFORMS}, got {self.waveform!r}")
        if self.envelope is None:
            self.envelope = Envelope()

    def render(self, sample_rate: int) -> np.ndarray:
        """Synthesize this tone as a mono float32 buffer."""
        count = max(1, int(self.duration * sample_rate))
        t = np.arange(count, dtype=np.float32) / sample_rate
        phase = 2.0 * np.pi * self.frequency * t

        if self.waveform == "sine":
            wave = np.sin(phase)
        elif self.waveform == "square":
            wave = np.sign(np.sin(phase))
        elif self.waveform == "triangle":
            wave = 2.0 / np.pi * np.arcsin(np.sin(phase))
        elif self.waveform == "saw":
            wave = 2.0 * (t * self.frequency % 1.0) - 1.0
        else:
            wave = np.random.default_rng(0).uniform(-1.0, 1.0, count)

        wave = (wave * self.volume).astype(np.float32)
        return self.envelope.apply(wave, sample_rate)


def note(
    pitch: str | float,
    duration: float = 0.25,
    waveform: str = "sine",
    volume: float = 0.5,
) -> Tone:
    """Build a :class:`Tone` from a note name or frequency."""
    return Tone(note_to_frequency(pitch), duration, waveform, volume)
