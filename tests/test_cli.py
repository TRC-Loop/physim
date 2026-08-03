"""Scene discovery and the command-line interface."""

import pytest

from physim.cli.discover import find_scenes, load_module, pick_scene

SCENE_FILE = '''
"""A test scene file."""

from physim import Circle, HollowCircle, Scene


class First(Scene):
    """The first scene."""

    def construct(self):
        self.add(HollowCircle(radius=100), Circle(radius=10))
        self.run(seconds=0.2)


class Second(Scene):
    """The second scene."""

    def construct(self):
        self.add(Circle(radius=5))
        self.run(seconds=0.2)
'''

SINGLE_SCENE_FILE = """
from physim import Circle, Scene


class Only(Scene):
    def construct(self):
        self.add(Circle(radius=8))
        self.run(seconds=0.2)
"""


@pytest.fixture
def scene_file(tmp_path):
    """A file defining two scenes."""
    path = tmp_path / "scenes.py"
    path.write_text(SCENE_FILE)
    return path


@pytest.fixture
def single_file(tmp_path):
    """A file defining exactly one scene."""
    path = tmp_path / "single.py"
    path.write_text(SINGLE_SCENE_FILE)
    return path


def test_load_module_imports_a_file(scene_file):
    assert load_module(scene_file) is not None


def test_missing_file_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_module(tmp_path / "nope.py")


def test_find_scenes_discovers_subclasses(scene_file):
    assert set(find_scenes(load_module(scene_file))) == {"First", "Second"}


def test_find_scenes_ignores_the_base_class(scene_file):
    assert "Scene" not in find_scenes(load_module(scene_file))


def test_pick_scene_by_name(scene_file):
    scenes = find_scenes(load_module(scene_file))
    assert pick_scene(scenes, "Second").__name__ == "Second"


def test_pick_scene_defaults_when_only_one(single_file):
    scenes = find_scenes(load_module(single_file))
    assert pick_scene(scenes, None).__name__ == "Only"


def test_pick_scene_requires_a_name_when_ambiguous(scene_file):
    scenes = find_scenes(load_module(scene_file))
    with pytest.raises(ValueError, match="pick one"):
        pick_scene(scenes, None)


def test_unknown_scene_name_is_reported(scene_file):
    scenes = find_scenes(load_module(scene_file))
    with pytest.raises(ValueError, match="no scene named"):
        pick_scene(scenes, "Missing")


def test_empty_file_has_no_scenes(tmp_path):
    path = tmp_path / "empty.py"
    path.write_text("x = 1\n")
    with pytest.raises(ValueError, match="no Scene subclasses"):
        pick_scene(find_scenes(load_module(path)), None)


def test_cli_renders_a_scene(scene_file, tmp_path):
    typer_testing = pytest.importorskip("typer.testing")
    from physim.cli.app import app

    result = typer_testing.CliRunner().invoke(
        app,
        [
            "render",
            str(scene_file),
            "First",
            "-o",
            str(tmp_path / "cli.mp4"),
            "--resolution",
            "120x120",
            "--quiet",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "cli.mp4").exists()


def test_cli_lists_scenes(scene_file):
    typer_testing = pytest.importorskip("typer.testing")
    from physim.cli.app import app

    result = typer_testing.CliRunner().invoke(app, ["list", str(scene_file)])
    assert result.exit_code == 0
    assert "First" in result.output and "Second" in result.output


def test_cli_reports_a_missing_file(tmp_path):
    typer_testing = pytest.importorskip("typer.testing")
    from physim.cli.app import app

    result = typer_testing.CliRunner().invoke(app, ["list", str(tmp_path / "nope.py")])
    assert result.exit_code == 1


def test_cli_rejects_a_bad_resolution(scene_file):
    typer_testing = pytest.importorskip("typer.testing")
    from physim.cli.app import app

    result = typer_testing.CliRunner().invoke(
        app, ["render", str(scene_file), "First", "--resolution", "huge"]
    )
    assert result.exit_code == 1


def test_cli_info_runs():
    typer_testing = pytest.importorskip("typer.testing")
    from physim.cli.app import app

    result = typer_testing.CliRunner().invoke(app, ["info"])
    assert result.exit_code == 0
    assert "physim" in result.output
