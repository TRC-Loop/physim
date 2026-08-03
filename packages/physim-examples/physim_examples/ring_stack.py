"""A ball working its way out through concentric rings.

python -m physim_examples.ring_stack
"""

from physim import Circle, RGBCycle, RingStack, Scene
from physim.actions import PitchByImpact, PopRing, SpeedUp
from physim.effects import Glow, Trail
from physim.events import Bounce, Escape


class RingStackEscape(Scene):
    """Each escape removes the innermost ring, opening the way outward."""

    def construct(self) -> None:
        """Build the scene."""
        stack = RingStack(
            count=6,
            inner_radius=120,
            spacing=55,
            gap_degrees=38,
            gap_step=55,
            rotation_speed=45,
            stroke="#ffffff",
        )
        self.add(stack)

        ball = Circle(radius=18, fill=RGBCycle(speed=140), velocity=(210, 90))
        ball.add_effect(Trail(length=26), Glow(strength=0.6))
        ball.on(Bounce, SpeedUp(1.015, max_speed=2400))
        ball.on(Bounce, PitchByImpact(base="C3", span=28))
        ball.on(Escape, PopRing(stack))
        self.add(ball)

        self.run(seconds=25)


def main() -> None:
    """Render this example."""
    from ._runner import run

    run(RingStackEscape)


if __name__ == "__main__":
    main()
