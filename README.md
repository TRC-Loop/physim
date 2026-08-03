<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/physimw.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/physim.svg">
    <img src="assets/physim.svg" alt="physim" width="520">
  </picture>
</p>

<p align="center">
  <a href="https://pypi.org/project/physim/"><img alt="PyPI" src="https://img.shields.io/pypi/v/physim?color=ff006e&label=pypi"></a>
  <a href="https://pypi.org/project/physim/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/physim?color=3a86ff"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-39ff14"></a>
  <a href="https://github.com/TRC-Loop/physim/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/TRC-Loop/physim/ci.yml?branch=main"></a>
  <a href="https://github.com/TRC-Loop/physim"><img alt="Code style" src="https://img.shields.io/badge/style-ruff-000000"></a>
</p>

<p align="center">
  Python library for the bouncing and growing object animations you see on social media.<br>
  Every frame is rendered offline, so the exported video never stutters or drops frames.
</p>

## What it does

- Balls, polygons, stars and rects bouncing inside rings and arenas
- Rings with spinning gaps that objects escape through, plus stacked concentric rings
- Objects that grow, speed up, change color, clone themselves or vanish on any event
- Trails, glow, motion blur and gradient or image backgrounds
- Styled text with fonts, weights, italics, underline, strikethrough, gradients and backgrounds
- Shapes defined by math expressions, parametric and implicit
- Sound: synthesized tones, sample files and melodies that play the next note on every bounce
- MP4 and MKV export at any resolution and framerate, plus a live preview window
- Debug overlay with fps, frametime, object count, collisions and timings, all readable from code
- Third party addons through the `physim.plugins` entry point

## Install

```bash
pip install physim[all]
```

Core stays lean if you would rather opt in:

| Install | Pulls in | Gives you |
| --- | --- | --- |
| `physim` | numpy, skia-python, av, coloraide, alive-progress, yaspin | rendering and MP4/MKV export |
| `physim[cli]` | typer, rich | the `physim` command |
| `physim[preview]` | opencv-python, sounddevice | live preview window with audio |
| `physim[audio]` | mido | melodies from MIDI files |
| `physim[expr]` | sympy | shapes defined by math expressions |
| `physim[presets]` | physim-presets | color palettes and physics presets |
| `physim[examples]` | physim-examples | runnable example scenes |
| `physim[gpu]` | glfw | GPU rasterization via an offscreen GL context |
| `physim[all]` | everything above | |

## Run it

```python
# scene.py
from physim import Circle, HollowCircle, RGBCycle, Scene
from physim.actions import Grow, SpeedUp
from physim.effects import Glow, Trail
from physim.events import Bounce


class Bouncy(Scene):
    """A ball that grows and speeds up on every bounce."""

    def construct(self):
        self.add(HollowCircle(radius=420, stroke="#ffffff"))

        ball = Circle(radius=16, fill=RGBCycle(), velocity=(280, 60))
        ball.add_effect(Trail(length=28), Glow(strength=0.6))
        ball.on(Bounce, Grow(3, max_size=380))
        ball.on(Bounce, SpeedUp(1.02, max_speed=2200))
        self.add(ball)

        self.run(seconds=15)
```

```bash
physim render scene.py Bouncy --debug
```

Or skip the CLI entirely:

```bash
python -c "from scene import Bouncy; Bouncy().render()"
```

## Examples

```bash
pip install physim[examples]

python -m physim_examples                     # list them all
python -m physim_examples.bouncing_ball
python -m physim_examples.escape_ring --debug
python -m physim_examples.ring_stack --seconds 5 -o out.mp4
```

## CLI

```bash
physim render scene.py [Scene]   # render to video
physim list scene.py             # show the scenes in a file
physim preview scene.py          # live window
physim info                      # version, installed features, presets
```

| Flag | Does |
| --- | --- |
| `-o, --output` | output file path |
| `-f, --format` | `mp4` or `mkv` |
| `-r, --resolution` | `square`, `vertical`, `landscape`, `hd`, `fhd`, `4k` or `1080x1920` |
| `--fps` | frames per second |
| `-s, --seconds` | override the scene length |
| `-p, --physics` | physics preset name |
| `--seed` | random seed, for reproducible renders |
| `--motion-blur N` | sub-frame samples per frame |
| `-b, --backend` | `auto`, `cpu` or `gpu` |
| `--hardware-encode` | use a hardware video encoder when available |
| `-d, --debug` | overlay fps, frametime, objects, collisions and timings |
| `--audio-file` | also write the audio to a separate file |
| `--audio-only` | write only the audio track |
| `--no-audio` | skip audio entirely |
| `-q, --quiet` | hide the progress bar |

## Development

```bash
poetry install --all-extras
poetry run pytest
poetry run ruff check .
poetry run ruff format .
```

This repo also holds `packages/physim-presets` and `packages/physim-examples`.

## License

MIT
