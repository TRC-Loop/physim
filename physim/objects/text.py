"""Styled text elements."""

from __future__ import annotations

from ..color import Paint
from ..types import Vec2Like
from .base import SceneObject

#: horizontal alignment options
ALIGNMENTS = ("left", "center", "right")


class Text(SceneObject):
    """A styled run of text.

    Fonts are looked up by name through the system font manager; when a name
    isn't found the platform default is used instead and a warning is issued.
    """

    def __init__(
        self,
        text: str = "",
        pos: Vec2Like = (0.0, 0.0),
        *,
        font: str | None = None,
        size: float = 64.0,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikethrough: bool = False,
        color: Paint = "#ffffff",
        background: Paint | None = None,
        background_opacity: float = 1.0,
        background_padding: float = 12.0,
        background_radius: float = 8.0,
        align: str = "center",
        letter_spacing: float = 0.0,
        line_height: float = 1.2,
        **kwargs,
    ) -> None:
        kwargs.setdefault("fill", color)
        super().__init__(pos, **kwargs)
        self.text = text
        self.font = font
        self.size = size
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.strikethrough = strikethrough
        self.background = background
        self.background_opacity = background_opacity
        self.background_padding = background_padding
        self.background_radius = background_radius
        self.letter_spacing = letter_spacing
        self.line_height = line_height
        if align not in ALIGNMENTS:
            raise ValueError(f"align must be one of {ALIGNMENTS}, got {align!r}")
        self.align = align

    @property
    def color(self) -> Paint | None:
        """The text fill, an alias of :attr:`fill`."""
        return self.fill

    @color.setter
    def color(self, value: Paint) -> None:
        self.fill = value

    @property
    def lines(self) -> list[str]:
        """The text split into rendered lines."""
        return self.text.split("\n")

    def set_text(self, value: str) -> None:
        """Replace the text and fire a change event."""
        if value != self.text:
            old, self.text = self.text, value
            self.emit("change", old=old, new=value)

    def draw(self, canvas, ctx) -> None:
        """Draw the text."""
        ctx.draw_text(canvas, self)
