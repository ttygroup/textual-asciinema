"""Video player for asciinema playback - handles timing and UI updates only."""

import asyncio
import logging
import time
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from textual_tty import Monitor

from .parser import CastParser, CastFrame
from .video_file import VideoFile

logger = logging.getLogger(__name__)


class PlaybackEngine:
    """Video player that handles timing, UI updates, and user controls."""

    def __init__(self, parser: CastParser, terminal: "Monitor"):
        self.parser = parser
        self.terminal = terminal

        # Video file manager handles file reading only
        self.video_file = VideoFile(parser)

        # Simple playback state - just UI timing
        self.current_time = 0.0
        self.is_playing = False
        self.speed = 1.0
        self.last_update_time = 0.0

        # UI callback
        self.on_time_update: Optional[Callable[[float], None]] = None

        # Playback task
        self._playback_task: Optional[asyncio.Task] = None

    def _apply_frame(self, frame: CastFrame) -> None:
        """Apply one cast frame to the monitor: output feeds, resizes reflow."""
        if frame.stream_type == "o":
            self.terminal.feed(frame.data)
        elif frame.stream_type == "r":
            cols, rows = map(int, frame.data.split("x"))
            self.terminal.board.resize(cols, rows)

    async def play(self) -> None:
        """Start or resume playback."""
        if self.is_playing:
            return

        self.is_playing = True
        self.last_update_time = time.time()

        if self._playback_task is None or self._playback_task.done():
            self._playback_task = asyncio.create_task(self._playback_loop())

    async def pause(self) -> None:
        """Pause playback."""
        self.is_playing = False
        if self._playback_task and not self._playback_task.done():
            self._playback_task.cancel()
            try:
                await self._playback_task
            except asyncio.CancelledError:
                pass

    async def toggle_play_pause(self) -> None:
        """Toggle between play and pause."""
        if self.is_playing:
            await self.pause()
        else:
            await self.play()

    def set_speed(self, speed: float) -> None:
        """Set playback speed multiplier."""
        self.speed = speed

    async def seek_to(self, timestamp: float) -> None:
        """Seek to a timestamp, rebuilding the screen by replaying the cast.

        Backward seeks reset the board and replay from the top; forward seeks
        replay just the skipped frames. The parser is fast enough that replay
        is the honest implementation — the screen always shows true mid-cast
        state instead of going blank until the next output.
        """
        timestamp = max(0.0, min(timestamp, self.parser.duration))

        was_playing = self.is_playing
        await self.pause()

        if timestamp < self.current_time:
            self.terminal.board.reset()
            self.video_file.restart()

        for frame in self.video_file.get_frames_until(timestamp):
            self._apply_frame(frame)

        self.current_time = timestamp

        if self.on_time_update:
            self.on_time_update(self.current_time)

        if was_playing:
            await self.play()

    async def _playback_loop(self) -> None:
        """Simple video player loop - streams frames to the monitor."""
        try:
            frame_time = 0.016  # Target 60fps
            last_render_time = 0.0

            while self.is_playing:
                current_real_time = time.time()

                # Calculate how much cast time has passed
                if self.last_update_time > 0:
                    real_time_delta = current_real_time - self.last_update_time
                    cast_time_delta = real_time_delta * self.speed
                    self.current_time += cast_time_delta

                self.last_update_time = current_real_time

                # Skip frames if we're falling behind (only render at target framerate)
                time_since_last_render = current_real_time - last_render_time
                if time_since_last_render >= frame_time:
                    for frame in self.video_file.get_frames_until(self.current_time):
                        self._apply_frame(frame)

                    last_render_time = current_real_time

                    # Update time display
                    if self.on_time_update:
                        self.on_time_update(self.current_time)

                # At the end: flush the remaining frames (the tick that crosses the
                # duration may have skipped its render slot) and stop.
                if self.current_time >= self.parser.duration:
                    self.current_time = self.parser.duration
                    for frame in self.video_file.get_frames_until(self.current_time):
                        self._apply_frame(frame)
                    if self.on_time_update:
                        self.on_time_update(self.current_time)
                    self.is_playing = False
                    break

                # Small delay to prevent busy waiting
                await asyncio.sleep(0.008)  # 125Hz polling for smoother timing

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Playback error: {e}")
            self.is_playing = False

    def reset(self) -> None:
        """Reset playback to the beginning."""
        self.current_time = 0.0
        self.last_update_time = 0.0

        self.terminal.board.reset()
        self.video_file.restart()

        if self.on_time_update:
            self.on_time_update(self.current_time)

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.video_file:
            self.video_file.cleanup()

    def __del__(self):
        """Cleanup on destruction."""
        self.cleanup()
