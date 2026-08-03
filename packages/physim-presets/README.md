# physim-presets

Color palettes and physics parameter presets for [physim](https://github.com/TRC-Loop/physim).

Dependency-free plain data. Install it through physim's extra:

```bash
pip install physim[presets]
```

Then use the presets through physim, which adapts them into `Color` and
`PhysicsParams` values:

```python
from physim import colors, presets

ball = Circle(radius=20, fill=colors.NEON_PINK)
scene = Scene(physics=presets.get("classic"))
```
