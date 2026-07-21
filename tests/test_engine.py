"""PlaybackEngine drives a real Monitor over real cast files."""

from __future__ import annotations

from textual_tty import Monitor

from textual_asciinema.engine import PlaybackEngine
from textual_asciinema.parser import CastParser


def _engine(cast_path):
    parser = CastParser(cast_path)
    header = parser.header
    monitor = Monitor(size=(header.width, header.height))
    return PlaybackEngine(parser, monitor), monitor


def _line(monitor, y):
    return monitor.board.blitter.current_buffer.get_line_text(y).rstrip()


async def test_seek_forward_replays_frames(simple_cast):
    engine, monitor = _engine(simple_cast)
    await engine.seek_to(1.5)
    assert _line(monitor, 0) == "Hello World!"
    assert engine.current_time == 1.5


async def test_seek_backward_resets_and_replays(simple_cast):
    engine, monitor = _engine(simple_cast)
    await engine.seek_to(2.5)
    assert _line(monitor, 1) == "second line"

    await engine.seek_to(0.5)
    assert _line(monitor, 0) == "Hello"
    assert _line(monitor, 1) == ""  # the later frames are gone after the reset


async def test_resize_frames_reflow_the_board(resizing_cast):
    engine, monitor = _engine(resizing_cast)
    assert (monitor.board.width, monitor.board.height) == (20, 6)
    await engine.seek_to(1.5)
    assert (monitor.board.width, monitor.board.height) == (30, 8)


async def test_playback_reaches_the_end(simple_cast):
    engine, monitor = _engine(simple_cast)
    engine.set_speed(100.0)  # two seconds of cast in a blink
    await engine.play()
    await engine._playback_task
    assert not engine.is_playing
    assert _line(monitor, 0) == "Hello World!"
    assert _line(monitor, 1) == "second line"


async def test_pause_and_resume(simple_cast):
    engine, _ = _engine(simple_cast)
    await engine.play()
    assert engine.is_playing
    await engine.pause()
    assert not engine.is_playing
    await engine.toggle_play_pause()
    assert engine.is_playing
    await engine.pause()


def test_speed_and_initial_state(simple_cast):
    engine, _ = _engine(simple_cast)
    assert engine.current_time == 0.0
    assert not engine.is_playing
    assert engine.speed == 1.0
    engine.set_speed(2.0)
    assert engine.speed == 2.0


async def test_reset_returns_to_the_top(simple_cast):
    engine, monitor = _engine(simple_cast)
    await engine.seek_to(2.5)
    engine.reset()
    assert engine.current_time == 0.0
    assert _line(monitor, 0) == ""
