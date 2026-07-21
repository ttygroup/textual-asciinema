"""AsciinemaPlayer: the composed widget, mounted in a real app."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual_tty import Monitor

from textual_asciinema.parser import CastParser
from textual_asciinema.player import AsciinemaPlayer


class PlayerApp(App):
    def __init__(self, cast_path) -> None:
        super().__init__()
        self.cast_path = cast_path

    def compose(self) -> ComposeResult:
        yield AsciinemaPlayer(self.cast_path)


async def test_player_composes_a_monitor_without_a_process(simple_cast):
    app = PlayerApp(simple_cast)
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        monitor = app.query_one(Monitor)
        assert monitor.board.process is None
        assert (monitor.board.width, monitor.board.height) == (20, 6)
        assert (monitor.size.width, monitor.size.height) == (20, 6)  # sized to the cast


async def test_seek_shows_mid_cast_state(simple_cast):
    app = PlayerApp(simple_cast)
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        player = app.query_one(AsciinemaPlayer)
        await player.seek(1.5)
        await pilot.pause(0.1)
        monitor = app.query_one(Monitor)
        assert "Hello World!" in monitor.render_line(0).text


async def test_play_renders_the_cast(simple_cast):
    app = PlayerApp(simple_cast)
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        player = app.query_one(AsciinemaPlayer)
        player.set_speed(100.0)
        await player.play()
        await pilot.pause(0.3)
        monitor = app.query_one(Monitor)
        assert "Hello World!" in monitor.render_line(0).text
        assert "second line" in monitor.render_line(1).text


async def test_gzipped_cast_plays(gzipped_cast):
    app = PlayerApp(gzipped_cast)
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        player = app.query_one(AsciinemaPlayer)
        await player.seek(2.0)
        await pilot.pause(0.1)
        assert "Compressed data!" in app.query_one(Monitor).render_line(0).text


def test_init_accepts_string_and_path(simple_cast):
    assert AsciinemaPlayer(str(simple_cast)).cast_path == Path(simple_cast)
    assert AsciinemaPlayer(Path(simple_cast)).cast_path == Path(simple_cast)


def test_parser_reads_header_and_duration(simple_cast):
    parser = CastParser(simple_cast)
    assert (parser.header.width, parser.header.height) == (20, 6)
    assert parser.duration == 2.0
