"""Melodies that advance one note per event.

The pattern behind the videos where every bounce plays the next note of a
tune::

    melody = Melody.from_notes("C4 E4 G4 C5")
    ball.on(Bounce, melody.next_note())
"""

from __future__ import annotations

from pathlib import Path

from ..events import Event
from .synth import Tone, midi_to_frequency, note_to_frequency

_MIDI_HINT = "reading midi files needs mido; install it with: pip install physim[audio]"


class Melody:
    """An ordered list of notes that steps forward each time it is triggered."""

    def __init__(
        self,
        frequencies: list[float],
        *,
        duration: float = 0.25,
        waveform: str = "sine",
        volume: float = 0.5,
        loop: bool = True,
    ) -> None:
        self.frequencies = frequencies
        self.duration = duration
        self.waveform = waveform
        self.volume = volume
        self.loop = loop
        self.index = -1

    @classmethod
    def from_notes(cls, notes: str | list[str | float], **kwargs) -> Melody:
        """Build from note names, either space-separated or as a list.

        >>> Melody.from_notes("C4 E4 G4 C5")
        """
        items = notes.split() if isinstance(notes, str) else notes
        return cls([note_to_frequency(n) for n in items], **kwargs)

    @classmethod
    def from_midi(cls, path: str | Path, track: int | None = None, **kwargs) -> Melody:
        """Build from the note-on events of a MIDI file."""
        try:
            import mido
        except ImportError as exc:
            raise ImportError(_MIDI_HINT) from exc

        midi = mido.MidiFile(str(path))
        tracks = midi.tracks if track is None else [midi.tracks[track]]
        pitches = [
            msg.note for t in tracks for msg in t if msg.type == "note_on" and msg.velocity > 0
        ]
        if not pitches:
            raise ValueError(f"no notes found in {path}")
        return cls([midi_to_frequency(p) for p in pitches], **kwargs)

    def __len__(self) -> int:
        return len(self.frequencies)

    def reset(self) -> None:
        """Start the melody over."""
        self.index = -1

    def advance(self) -> Tone | None:
        """Step to the next note and return it, or ``None`` past the end."""
        self.index += 1
        if self.index >= len(self.frequencies):
            if not self.loop:
                return None
            self.index = 0
        return Tone(
            frequency=self.frequencies[self.index],
            duration=self.duration,
            waveform=self.waveform,
            volume=self.volume,
        )

    def next_note(self):
        """Return an action that plays the next note when an event fires."""
        from ..actions.base import Action

        melody = self

        class PlayNextNote(Action):
            """Plays the melody's next note."""

            def apply(self, event: Event) -> None:
                """Advance the melody and queue the note on the scene."""
                tone = melody.advance()
                if tone is not None and event.scene is not None:
                    event.scene.play_sound(tone)

        return PlayNextNote()
