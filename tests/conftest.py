"""Shared fixtures: real cast files, real monitors, no mocks."""

from __future__ import annotations

import gzip
import json

import pytest


def write_cast(path, width=20, height=6, frames=(), compress=False):
    """Write a minimal asciicast v2 file."""
    header = {"version": 2, "width": width, "height": height, "timestamp": 1234567890}
    opener = gzip.open if compress else open
    with opener(path, "wt") as f:
        f.write(json.dumps(header) + "\n")
        for frame in frames:
            f.write(json.dumps(list(frame)) + "\n")
    return path


@pytest.fixture
def simple_cast(tmp_path):
    """Three output frames over two seconds of cast time."""
    return write_cast(
        tmp_path / "simple.cast",
        frames=[
            (0.0, "o", "Hello "),
            (1.0, "o", "World!"),
            (2.0, "o", "\r\nsecond line"),
        ],
    )


@pytest.fixture
def resizing_cast(tmp_path):
    """A cast whose terminal grows mid-recording."""
    return write_cast(
        tmp_path / "resize.cast",
        frames=[
            (0.0, "o", "small"),
            (1.0, "r", "30x8"),
            (2.0, "o", " big"),
        ],
    )


@pytest.fixture
def gzipped_cast(tmp_path):
    return write_cast(
        tmp_path / "test.cast.gz",
        width=40,
        height=10,
        frames=[(0.0, "o", "Compressed "), (1.5, "o", "data!")],
        compress=True,
    )
