"""Text styling and gradients over a moving scene.

python -m physim_examples.styled_text
"""

from physim import Circle, Gradient, HollowRect, Scene, Text
from physim.effects import FadeIn, Trail


class StyledText(Scene):
    """Shows off font styling, gradients and backgrounds."""

    def construct(self) -> None:
        """Build the scene."""
        self.add(HollowRect(width=900, height=900, stroke="#333344", thickness=4))

        title = Text(
            "physim",
            pos=(0, 330),
            size=140,
            bold=True,
            color=Gradient(colors=["#ff006e", "#3a86ff"], kind="linear", end=(0, 140)),
        )
        title.add_effect(FadeIn(duration=0.8))

        subtitle = Text(
            "offline rendered\nnever drops a frame",
            pos=(0, 170),
            size=44,
            italic=True,
            color="#c8c8c8",
            background="#16161f",
            background_opacity=0.85,
        )

        note = Text(
            "underlined  ·  struck through",
            pos=(0, -330),
            size=38,
            underline=True,
            strikethrough=True,
            color="#39ff14",
        )
        self.add(title, subtitle, note)

        ball = Circle(radius=22, fill="#faff00", pos=(0, -80), velocity=(320, 40))
        ball.add_effect(Trail(length=20))
        self.add(ball)

        self.run(seconds=8)


def main() -> None:
    """Render this example."""
    from ._runner import run

    run(StyledText)


if __name__ == "__main__":
    main()
