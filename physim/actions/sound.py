"""Actions that play sound."""

from __future__ import annotations

from pathlib import Path

from ..events import Event
from .base import Action


class PlaySound(Action):
    """Queues a sound file or tone at the moment the event fires."""

    def __init__(self, sound: str | Path | object, volume: float = 1.0, **kwargs) -> None:
        super().__init__(**kwargs)
        self.sound = sound
        self.volume = volume

    def apply(self, event: Event) -> None:
        """Queue the sound on the scene's audio track."""
        if event.scene is not None:
            event.scene.play_sound(self.sound)


class PlayNote(Action):
    """Plays a single synthesized note."""

    def __init__(
        self,
        pitch: str | float = "C4",
        duration: float = 0.2,
        waveform: str = "sine",
        volume: float = 0.5,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.pitch = pitch
        self.duration = duration
        self.waveform = waveform
        self.volume = volume

    def apply(self, event: Event) -> None:
        """Synthesize and queue the note."""
        from ..audio import note

        if event.scene is not None:
            event.scene.play_sound(note(self.pitch, self.duration, self.waveform, self.volume))


class PlayMelody(Action):
    """Advances a melody and plays its next note.

    Equivalent to ``melody.next_note()``, kept here so every action is
    discoverable from one place.
    """

    def __init__(self, melody, **kwargs) -> None:
        super().__init__(**kwargs)
        self.melody = melody

    def apply(self, event: Event) -> None:
        """Queue the melody's next note."""
        tone = self.melody.advance()
        if tone is not None and event.scene is not None:
            event.scene.play_sound(tone)


class PitchByImpact(Action):
    """Plays a note whose pitch follows how hard the object hit.

    Harder impacts play higher notes, which reads as the object gaining energy.
    """

    def __init__(
        self,
        base: str | float = "C4",
        span: float = 24.0,
        reference_impact: float = 1200.0,
        duration: float = 0.18,
        waveform: str = "sine",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.base = base
        self.span = span
        """How many semitones the pitch can rise by."""

        self.reference_impact = reference_impact
        self.duration = duration
        self.waveform = waveform

    def apply(self, event: Event) -> None:
        """Map the event's impact onto a pitch and queue it."""
        from ..audio import Tone, note_to_frequency

        if event.scene is None:
            return
        impact = float(event.get("impact", 0.0))
        ratio = min(1.0, impact / self.reference_impact)
        semitones = ratio * self.span
        frequency = note_to_frequency(self.base) * (2.0 ** (semitones / 12.0))
        event.scene.play_sound(
            Tone(frequency=frequency, duration=self.duration, waveform=self.waveform)
        )
