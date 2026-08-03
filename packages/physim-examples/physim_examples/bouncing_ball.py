"""The simplest scene: one ball bouncing inside a ring.

python -m physim_examples.bouncing_ball
"""

from physim import Circle, HollowCircle, RGBCycle, Scene
from physim.effects import Glow, Trail


class BouncingBall(Scene):
    """A single color-cycling ball bouncing inside a white ring."""

    def construct(self) -> None:
        """Build the scene."""
        self.add(HollowCircle(radius=420, stroke="#ffffff", thickness=6))
        ball = Circle(radius=26, fill=RGBCycle(speed=90), velocity=(260, 120))
        ball.add_effect(Trail(length=28), Glow(strength=0.5))
        self.add(ball)
        self.run(seconds=10)


def main() -> None:
    """Render this example."""
    from ._runner import run

    run(BouncingBall)


if __name__ == "__main__":
    main()
