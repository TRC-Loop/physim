"""One ball becomes hundreds, each bounce splitting off a copy.

python -m physim_examples.cloning_balls
"""

from physim import Circle, HollowCircle, PhysicsParams, Scene, Text
from physim.actions import Clone, RandomColor
from physim.events import Bounce


class CloningBalls(Scene):
    """Every few bounces a ball splits in two, filling the ring."""

    def construct(self) -> None:
        """Build the scene."""
        self.engine.params = PhysicsParams(
            gravity=900, restitution=1.0, damping=1.0, ball_collisions=True
        )
        self.add(HollowCircle(radius=440, stroke="#ffffff", thickness=6))

        counter = Text("1", pos=(0, 520), size=64, bold=True, color="#ffffff")
        self.add(counter)

        ball = Circle(radius=16, fill="#ff006e", velocity=(240, 120))
        ball.on(Bounce, Clone(1, spread=90, max_objects=400, every=3))
        ball.on(Bounce, RandomColor(every=3))
        self.add(ball)

        @self.each_frame
        def update_counter(scene, _dt) -> None:
            """Keep the on-screen count in step with the ball count."""
            counter.set_text(str(len(scene.bodies)))

        self.run(seconds=15)


def main() -> None:
    """Render this example."""
    from ._runner import run

    run(CloningBalls)


if __name__ == "__main__":
    main()
