"""Balls escaping a ring through a spinning gap, playing a melody."""

from physim import Circle, Color, HollowCircle, Scene
from physim.actions import Custom
from physim.audio import Melody
from physim.effects import Trail
from physim.events import Bounce, Escape

MAX_BALLS = 200


class Escaping(Scene):
    """Each escape replaces one ball with two, so the swarm grows."""

    def construct(self) -> None:
        self.melody = Melody.from_notes(
            "E5 D#5 E5 D#5 E5 B4 D5 C5 A4", duration=0.25, waveform="triangle"
        )
        self.spawned = 0

        radius = min(self.config.width, self.config.height) * 0.42
        self.add(
            HollowCircle(
                radius=radius,
                stroke="#ffffff",
                thickness=9,
                gap_degrees=30,
                rotation_speed=50,
            )
        )
        self.add(self.new_ball(velocity=(300, 120)))
        self.run_until(lambda s: len(s.bodies) >= MAX_BALLS, max_seconds=120)

    def new_ball(self, velocity=None) -> Circle:
        """Build a ball with its own color and the shared melody."""
        from physim import Vec2

        self.spawned += 1
        ball = Circle(
            radius=18,
            velocity=velocity
            or Vec2.polar(self.random.uniform(0, 360), self.random.uniform(260, 380)),
            fill=Color.oklch(0.75, 0.2, (self.spawned * 47) % 360),
        )
        if self.spawned <= 300:
            ball.add_effect(Trail(length=30, fade=0.55))
        ball.on(Bounce, self.melody.next_note())
        ball.on(Escape, Custom(self.on_escape))
        return ball

    def on_escape(self, event) -> None:
        """Replace the escaped ball with two new ones."""
        event.source.destroy()
        for _ in range(2):
            self.spawn(self.new_ball())


if __name__ == "__main__":
    Escaping(physics="classic").render()
