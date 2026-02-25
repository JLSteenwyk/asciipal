from __future__ import annotations

from asciipal.app import AsciiPalApp
from asciipal.break_manager import BreakStatus
from asciipal.config import Config, DEFAULT_CONFIG


def _config(notifications: str) -> Config:
    cfg = dict(DEFAULT_CONFIG)
    cfg["notifications"] = notifications
    return Config.from_dict(cfg)


def test_render_status_silent_hides_break_messages() -> None:
    app = AsciiPalApp(_config("silent"), headless=True, max_ticks=1)
    state, line = app._render_status(
        "watching", BreakStatus(should_break=True, stage="insistence", seconds_until_break=0.0)
    )
    assert state == "watching"
    assert line == ""


def test_render_status_verbose_shows_countdown() -> None:
    app = AsciiPalApp(_config("verbose"), headless=True, max_ticks=1)
    state, line = app._render_status(
        "watching", BreakStatus(should_break=False, stage="suggestion", seconds_until_break=121.0)
    )
    assert state == "watching"
    assert "Break soon" in line

