"""Synthesis, melodies and the offline mixer."""

import numpy as np
import pytest

from physim import Circle, PhysicsParams, RenderConfig, Scene
from physim.actions import PitchByImpact, PlayNote
from physim.audio import Envelope, Melody, Tone, mix, note, note_to_frequency
from physim.config import AudioConfig
from physim.events import Event


def test_a4_is_440_hz():
    assert note_to_frequency("A4") == pytest.approx(440.0)


def test_octave_doubles_the_frequency():
    assert note_to_frequency("A5") == pytest.approx(880.0)
    assert note_to_frequency("A3") == pytest.approx(220.0)


def test_sharps_and_flats_agree():
    assert note_to_frequency("C#4") == pytest.approx(note_to_frequency("Db4"))


def test_numeric_pitch_passes_through():
    assert note_to_frequency(300.0) == 300.0


def test_unknown_note_is_rejected():
    with pytest.raises(ValueError, match="unknown note"):
        note_to_frequency("H4")


def test_tone_length_matches_the_sample_rate():
    samples = Tone(440, duration=0.5).render(1000)
    assert len(samples) == 500


def test_tone_stays_in_range():
    samples = Tone(440, duration=0.1, volume=1.0).render(8000)
    assert np.abs(samples).max() <= 1.0


def test_every_waveform_renders():
    for shape in ("sine", "square", "triangle", "saw", "noise"):
        assert Tone(440, 0.05, waveform=shape).render(8000).size > 0


def test_bad_waveform_is_rejected():
    with pytest.raises(ValueError, match="waveform"):
        Tone(440, waveform="zigzag")


def test_envelope_starts_and_ends_quiet():
    shaped = Envelope().apply(np.ones(8000, dtype=np.float32), 8000)
    assert shaped[0] < 0.1 and shaped[-1] < 0.1


def test_melody_advances_and_loops():
    melody = Melody.from_notes("C4 E4")
    assert melody.advance().frequency == pytest.approx(note_to_frequency("C4"))
    assert melody.advance().frequency == pytest.approx(note_to_frequency("E4"))
    assert melody.advance().frequency == pytest.approx(note_to_frequency("C4"))


def test_melody_can_stop_at_the_end():
    melody = Melody.from_notes("C4", loop=False)
    melody.advance()
    assert melody.advance() is None


def test_melody_reset():
    melody = Melody.from_notes("C4 E4")
    melody.advance()
    melody.reset()
    assert melody.advance().frequency == pytest.approx(note_to_frequency("C4"))


def test_melody_accepts_a_list():
    assert len(Melody.from_notes(["C4", "E4", 440.0])) == 3


def test_melody_action_queues_sound_on_the_scene():
    scene = Scene()
    ball = Circle(radius=10)
    scene.add(ball)
    ball.on("bounce", Melody.from_notes("C4 E4").next_note())
    ball.emit("bounce")
    assert len(scene._sounds) == 1


def test_play_note_action_queues_a_tone():
    scene = Scene()
    PlayNote("C4").run(Event(name="bounce", scene=scene))
    assert isinstance(scene._sounds[0][1], Tone)


def test_pitch_follows_impact():
    scene = Scene()
    action = PitchByImpact(base="C4", span=12, reference_impact=1000)
    action.run(Event(name="bounce", scene=scene, data={"impact": 0}))
    action.run(Event(name="bounce", scene=scene, data={"impact": 1000}))
    soft, hard = scene._sounds[0][1], scene._sounds[1][1]
    assert hard.frequency > soft.frequency


def test_sounds_are_queued_at_scene_time():
    scene = Scene(RenderConfig(fps=10), physics=PhysicsParams(gravity=0))
    scene.time = 2.5
    scene.play_sound(note("C4"))
    assert scene._sounds[0][0] == 2.5


def test_mix_produces_the_right_shape():
    track = mix([(0.0, note("C4", 0.1))], AudioConfig(sample_rate=8000), duration=1.0)
    assert track.shape == (2, 8000)


def test_mix_mono():
    config = AudioConfig(sample_rate=8000, channels=1)
    assert mix([(0.0, note("C4", 0.1))], config, duration=1.0).shape == (1, 8000)


def test_mix_places_sound_at_the_right_offset():
    config = AudioConfig(sample_rate=8000)
    track = mix([(0.5, note("C4", 0.1, volume=1.0))], config, duration=1.0)
    assert np.abs(track[0, :3000]).max() < 0.01
    assert np.abs(track[0, 4000:5000]).max() > 0.01


def test_mix_never_clips():
    config = AudioConfig(sample_rate=8000)
    loud = [(0.0, note("C4", 0.5, volume=1.0)) for _ in range(20)]
    assert np.abs(mix(loud, config, duration=1.0)).max() <= 1.0


def test_empty_mix_is_silent():
    track = mix([], AudioConfig(sample_rate=8000), duration=0.5)
    assert np.abs(track).max() == 0.0


def test_render_muxes_an_audio_stream(tmp_path):
    import av

    scene = Scene(RenderConfig(resolution=(120, 120), fps=10), physics=PhysicsParams(gravity=0))
    ball = Circle(radius=10)
    ball.on("bounce", PlayNote("C4"))
    scene.add(ball)
    scene.run(seconds=0.5)
    scene.each_frame(lambda s, dt: ball.emit("bounce") if s.frame == 1 else None)

    path = scene.render(output=tmp_path / "sound.mp4", quiet=True)
    with av.open(str(path)) as container:
        assert len(container.streams.audio) == 1


def test_long_audio_muxes_without_rebase_error(tmp_path):
    # a single oversized audio frame produced packets av could not timestamp,
    # which only showed up once a track ran for many seconds
    import av

    from physim.export.video import mux_audio

    scene = Scene(RenderConfig(resolution=(96, 96), fps=60), physics=PhysicsParams(gravity=0))
    scene.add(Circle(radius=8))
    scene.run(seconds=0.5)
    path = scene.render(output=tmp_path / "long.mp4", quiet=True)

    samples = np.zeros((2, 48_000 * 30), dtype=np.float32)
    mux_audio(path, samples, AudioConfig())

    with av.open(str(path)) as container:
        assert len(container.streams.audio) == 1
        assert len(container.streams.video) == 1


def test_muxed_audio_keeps_every_video_frame(tmp_path):
    import av

    from physim.export.video import mux_audio

    scene = Scene(RenderConfig(resolution=(96, 96), fps=30), physics=PhysicsParams(gravity=0))
    scene.add(Circle(radius=8, velocity=(40, 0)))
    scene.run(seconds=1.0)
    path = scene.render(output=tmp_path / "keep.mp4", quiet=True)

    mux_audio(path, np.zeros((2, 48_000), dtype=np.float32), AudioConfig())
    with av.open(str(path)) as container:
        assert len(list(container.decode(video=0))) == 30


def test_audio_can_be_disabled(tmp_path):
    import av

    scene = Scene(RenderConfig(resolution=(120, 120), fps=10), physics=PhysicsParams(gravity=0))
    scene.audio_config.enabled = False
    ball = Circle(radius=10)
    scene.add(ball)
    scene.play_sound(note("C4"))
    scene.run(seconds=0.3)

    path = scene.render(output=tmp_path / "silent.mp4", quiet=True)
    with av.open(str(path)) as container:
        assert len(container.streams.audio) == 0
