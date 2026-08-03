"""Finding renderable scenes inside a Python file."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from types import ModuleType

from ..scene import Scene


def load_module(path: Path) -> ModuleType:
    """Import a Python file as a module without installing it."""
    path = Path(path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"no such file: {path}")

    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not import {path}")

    module = importlib.util.module_from_spec(spec)
    # let the file import its own siblings
    sys.path.insert(0, str(path.parent))
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def find_scenes(module: ModuleType) -> dict[str, type[Scene]]:
    """Return every Scene subclass defined in a module, in declaration order."""
    found = {}
    for name, obj in vars(module).items():
        if (
            inspect.isclass(obj)
            and issubclass(obj, Scene)
            and obj is not Scene
            and obj.__module__ == module.__name__
        ):
            found[name] = obj
    return found


def pick_scene(scenes: dict[str, type[Scene]], name: str | None) -> type[Scene]:
    """Choose a scene by name, or the only one when the file defines just one."""
    if not scenes:
        raise ValueError("no Scene subclasses found in that file")
    if name is None:
        if len(scenes) == 1:
            return next(iter(scenes.values()))
        raise ValueError(f"file defines {len(scenes)} scenes, pick one: {', '.join(scenes)}")
    try:
        return scenes[name]
    except KeyError:
        raise ValueError(f"no scene named {name!r}; found: {', '.join(scenes)}") from None
