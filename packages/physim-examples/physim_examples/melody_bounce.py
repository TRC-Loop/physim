"""Each bounce plays the next note of a melody.

python -m physim_examples.melody_bounce
"""

from physim import Circle, HollowCircle, Scene
from physim.audio import Melody
from physim.effects import Glow, Trail
from physim.events import Bounce


class MelodyBounce(Scene):
    """A ball playing its way through a tune, one note per bounce."""

    def construct(self) -> None:
        """Build the scene."""
        self.add(HollowCircle(radius=420, stroke="#ffffff", thickness=6))

        melody = Melody.from_notes(
            "C4 D4 E4 G4 A4 G4 E4 D4 C4 E4 G4 C5",
            duration=0.22,
            waveform="triangle",
        )
        ball = Circle(radius=24, fill="#00fff5", velocity=(280, 90))
        ball.add_effect(Trail(length=24), Glow(strength=0.5))
        ball.on(Bounce, melody.next_note())
        self.add(ball)

        self.run(seconds=12)


def main() -> None:
    """Render this example."""
    from ._runner import run

    run(MelodyBounce)


if __name__ == "__main__":
    main()
