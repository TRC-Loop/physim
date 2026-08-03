"""A ball escaping through a spinning gap in the ring.

python -m physim_examples.escape_ring
"""

from physim import Circle, HollowCircle, Scene, Text
from physim.actions import Custom, SpeedUp
from physim.effects import Glow, Trail
from physim.events import Bounce, Escape


class EscapeRing(Scene):
    """The ring's opening rotates until the ball finally finds its way out."""

    def construct(self) -> None:
        """Build the scene."""
        ring = HollowCircle(
            radius=420,
            stroke="#ffffff",
            thickness=8,
            gap_degrees=34,
            gap_angle=90,
            rotation_speed=55,
        )
        self.add(ring)

        label = Text("escaped!", pos=(0, 0), size=90, bold=True, color="#39ff14")
        label.visible = False

        ball = Circle(radius=22, fill="#ff006e", velocity=(300, 140))
        ball.add_effect(Trail(length=32), Glow(strength=0.7))
        ball.on(Bounce, SpeedUp(1.03, max_speed=2600))

        def celebrate(event) -> None:
            """Reveal the label and let the ball fly off for a moment."""
            label.visible = True
            event.scene.on("frame", lambda e: None)

        ball.on(Escape, Custom(celebrate))
        self.add(ball, label)

        self.run_until(Escape, max_seconds=40)


def main() -> None:
    """Render this example."""
    from ._runner import run

    run(EscapeRing)


if __name__ == "__main__":
    main()
