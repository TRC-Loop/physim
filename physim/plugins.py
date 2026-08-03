"""Extension points for third-party addons.

An addon is an ordinary pip-installable package that registers itself under the
``physim.plugins`` entry point group. physim imports every registered plugin the
first time :func:`load` runs, giving it a chance to add shapes, actions, easing
curves, effects or physics presets.

A minimal addon's ``pyproject.toml``::

    [project]
    name = "physim-sparkles"
    dependencies = ["physim>=0.0.0"]

    [project.entry-points."physim.plugins"]
    sparkles = "physim_sparkles:setup"

And its ``setup`` function::

    from physim.plugins import register_action, register_easing

    def setup(registry):
        register_easing("sparkle", lambda t: t ** 0.5)
        register_action("Sparkle", Sparkle)

Everything an addon can extend is a plain registry, so nothing here needs
physim's internals.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

#: entry point group addons register themselves under
GROUP = "physim.plugins"

#: objects contributed by addons, keyed by kind then name
REGISTRY: dict[str, dict[str, Any]] = {
    "objects": {},
    "actions": {},
    "effects": {},
    "physics": {},
    "shaders": {},
}

_loaded: dict[str, Any] | None = None


def register(kind: str, name: str, value: Any) -> Any:
    """Register an addon contribution under a kind and name."""
    if kind not in REGISTRY:
        raise ValueError(f"unknown plugin kind {kind!r}; expected one of {sorted(REGISTRY)}")
    REGISTRY[kind][name] = value
    return value


def register_object(name: str, cls: Any) -> Any:
    """Register a custom scene object so scenes and the CLI can find it by name."""
    return register("objects", name, cls)


def register_action(name: str, cls: Any) -> Any:
    """Register a custom event action."""
    return register("actions", name, cls)


def register_effect(name: str, cls: Any) -> Any:
    """Register a custom visual effect."""
    return register("effects", name, cls)


def register_physics(name: str, params: Any) -> Any:
    """Register a custom physics preset."""
    return register("physics", name, params)


def register_easing(name: str, fn: Callable[[float], float]) -> Callable:
    """Register a custom easing curve, shared with :mod:`physim.easing`."""
    from .easing import add

    return add(name, fn)


def get(kind: str, name: str) -> Any:
    """Look up a registered contribution, loading addons first."""
    load()
    try:
        return REGISTRY[kind][name]
    except KeyError:
        raise ValueError(f"no {kind} plugin named {name!r}") from None


def names(kind: str) -> list[str]:
    """Sorted names registered for a kind."""
    load()
    return sorted(REGISTRY.get(kind, {}))


def load(reload: bool = False) -> dict[str, Any]:
    """Import every installed addon, returning what each ``setup`` returned.

    A failing addon is skipped with a warning rather than breaking the render.
    """
    global _loaded
    if _loaded is not None and not reload:
        return _loaded

    import warnings
    from importlib.metadata import entry_points

    results: dict[str, Any] = {}
    for entry in entry_points(group=GROUP):
        try:
            setup = entry.load()
            results[entry.name] = setup(REGISTRY) if callable(setup) else setup
        except Exception as exc:  # noqa: BLE001  (one bad addon must not break physim)
            warnings.warn(f"physim plugin {entry.name!r} failed to load: {exc}", stacklevel=2)
    _loaded = results
    return results


def loaded() -> list[str]:
    """Names of every addon that loaded successfully."""
    return sorted(load())
