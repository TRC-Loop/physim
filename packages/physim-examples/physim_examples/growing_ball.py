"""A ball that grows on every bounce until it fills the ring.

python -m physim_examples.growing_ball
"""

from physim import Circle, HollowCircle, RGBCycle, Scene
from physim.actions import Grow, SpeedUp, Stop
from physim.effects import Glow
from physim.events import Bounce


class GrowingBall(Scene):
    """Each bounce makes the ball a little bigger and a little faster."""

    def construct(self) -> None:
        """Build the scene."""
        self.add(HollowCircle(radius=430, stroke="#ffffff", thickness=6))

        ball = Circle(radius=14, fill=RGBCycle(speed=120), velocity=(280, 60))
        ball.add_effect(Glow(strength=0.6))
        ball.on(Bounce, Grow(3.5, max_size=380))
        ball.on(Bounce, SpeedUp(1.02, max_speed=2200))
        # end once the ball has effectively filled the ring
        ball.on(Bounce, Stop(every=140))
        self.add(ball)

        self.run(seconds=20)


def main() -> None:
    """Render this example."""
    from ._runner import run

    run(GrowingBall)


if __name__ == "__main__":
    main()
