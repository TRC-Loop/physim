"""Image textures usable as a shape fill.

A texture is loaded once and cached, then tiled or fitted into whatever shape
it fills. Any format Skia can decode works (png, jpg, webp, gif frames).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: how a texture maps onto the shape it fills
FIT_MODES = ("tile", "stretch", "cover", "contain")

_cache: dict[Path, Any] = {}


def load_image(path: str | Path) -> Any:
    """Decode an image file into a Skia image, caching by path."""
    import skia

    key = Path(path).expanduser().resolve()
    cached = _cache.get(key)
    if cached is not None:
        return cached
    if not key.exists():
        raise FileNotFoundError(f"texture not found: {key}")
    image = skia.Image.open(str(key))
    if image is None:
        raise ValueError(f"could not decode texture: {key}")
    _cache[key] = image
    return image


def clear_cache() -> None:
    """Drop every cached texture image."""
    _cache.clear()


@dataclass
class Texture:
    """An image used as a fill.

    ``fit`` controls the mapping: ``"tile"`` repeats the image, ``"stretch"``
    distorts it to the shape's bounds, ``"cover"`` fills while preserving
    aspect (cropping the overflow) and ``"contain"`` fits it entirely inside.
    """

    path: str | Path
    fit: str = "cover"
    opacity: float = 1.0
    scale: float = 1.0
    rotation: float = 0.0
    """Texture rotation in degrees."""

    offset: tuple[float, float] = (0.0, 0.0)
    tint: str | None = None
    """Optional color multiplied over the image."""

    def __post_init__(self) -> None:
        if self.fit not in FIT_MODES:
            raise ValueError(f"fit must be one of {FIT_MODES}, got {self.fit!r}")

    def image(self) -> Any:
        """The decoded Skia image for this texture."""
        return load_image(self.path)

    @property
    def size(self) -> tuple[int, int]:
        """Pixel dimensions of the source image."""
        img = self.image()
        return img.width(), img.height()
