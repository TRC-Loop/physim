"""The addon registry and extension points."""

import pytest

from physim import easing, plugins


@pytest.fixture(autouse=True)
def clean_registry():
    """Keep registrations from leaking between tests."""
    saved = {kind: dict(entries) for kind, entries in plugins.REGISTRY.items()}
    yield
    for kind, entries in saved.items():
        plugins.REGISTRY[kind] = entries


def test_register_and_get_an_object():
    class Blob:
        pass

    plugins.register_object("Blob", Blob)
    assert plugins.get("objects", "Blob") is Blob


def test_register_each_kind():
    plugins.register_action("Zap", object)
    plugins.register_effect("Sparkle", object)
    plugins.register_physics("bouncy_custom", object)
    assert "Zap" in plugins.names("actions")
    assert "Sparkle" in plugins.names("effects")
    assert "bouncy_custom" in plugins.names("physics")


def test_unknown_kind_is_rejected():
    with pytest.raises(ValueError, match="unknown plugin kind"):
        plugins.register("nonsense", "x", object)


def test_missing_plugin_is_reported():
    with pytest.raises(ValueError, match="no objects plugin named"):
        plugins.get("objects", "DoesNotExist")


def test_register_easing_reaches_the_easing_registry():
    plugins.register_easing("addon_curve", lambda t: t**0.5)
    try:
        assert easing.get("addon_curve")(0.25) == pytest.approx(0.5)
    finally:
        easing.EASINGS.pop("addon_curve", None)


def test_load_is_cached():
    assert plugins.load() is plugins.load()


def test_loaded_returns_a_list():
    assert isinstance(plugins.loaded(), list)


def test_broken_plugin_warns_but_does_not_raise(monkeypatch):
    class BadEntry:
        name = "broken"

        def load(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(plugins, "_loaded", None)
    monkeypatch.setattr("importlib.metadata.entry_points", lambda **kwargs: [BadEntry()])
    with pytest.warns(UserWarning, match="failed to load"):
        result = plugins.load(reload=True)
    assert result == {}


def test_plugin_setup_receives_the_registry(monkeypatch):
    seen = {}

    class GoodEntry:
        name = "good"

        def load(self):
            def setup(registry):
                seen["registry"] = registry
                return "ready"

            return setup

    monkeypatch.setattr(plugins, "_loaded", None)
    monkeypatch.setattr("importlib.metadata.entry_points", lambda **kwargs: [GoodEntry()])
    result = plugins.load(reload=True)
    assert result == {"good": "ready"}
    assert seen["registry"] is plugins.REGISTRY
