"""Shapes defined by math expressions.

Needs the expr extra::

    pip install physim[expr]
    python -m physim_examples.expr_shape
"""

from physim import Circle, HollowCircle, Scene
from physim.effects import Spin, Trail
from physim.objects.expr import ParametricShape


class ExprShape(Scene):
    """A rose curve and a lissajous figure traced from parametric expressions."""

    def construct(self) -> None:
        """Build the scene."""
        self.add(HollowCircle(radius=460, stroke="#222233", thickness=4))

        rose = ParametricShape(
            x="260*cos(5*t)*cos(t)",
            y="260*cos(5*t)*sin(t)",
            t_range=(0, 6.283185307179586),
            samples=600,
            fill=None,
            stroke="#ff006e",
            stroke_width=4,
        )
        rose.add_effect(Spin(speed=25))

        lissajous = ParametricShape(
            x="150*sin(3*t)",
            y="150*sin(4*t)",
            t_range=(0, 6.283185307179586),
            samples=400,
            fill=None,
            stroke="#00fff5",
            stroke_width=3,
        )
        lissajous.add_effect(Spin(speed=-40))
        self.add(rose, lissajous)

        ball = Circle(radius=14, fill="#faff00", velocity=(260, 110))
        ball.add_effect(Trail(length=22))
        self.add(ball)

        self.run(seconds=10)


def main() -> None:
    """Render this example."""
    from ._runner import run

    run(ExprShape)


if __name__ == "__main__":
    main()
