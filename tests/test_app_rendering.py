from __future__ import annotations

from asciipal.app import AsciiPalApp, _compose_display
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


def test_weather_panel_renders_below_ground() -> None:
    display = _compose_display(
        char_art="X",
        above_lines=[],
        plant_lines=[],
        progress_line="",
        status_line="",
        achievement_line="",
        inner_w=30,
        weather_panel_lines=["░ ╽ ░ ╽ ░  Rain"],
    )
    text = display.text
    assert "Weather" in text
    lines = text.split("\n")
    # Weather panel must appear after ground borders
    ground_idx = max(i for i, l in enumerate(lines) if l.startswith("╚"))
    weather_idx = next(i for i, l in enumerate(lines) if "Weather" in l)
    assert weather_idx > ground_idx
    # Check weather_panel region tag is used
    weather_row = display.regions[weather_idx]
    assert "weather_panel" in weather_row


def test_no_weather_panel_when_none() -> None:
    display = _compose_display(
        char_art="X",
        above_lines=[],
        plant_lines=[],
        progress_line="",
        status_line="",
        achievement_line="",
        inner_w=30,
        weather_panel_lines=None,
    )
    assert "Weather" not in display.text


def test_sysinfo_panel_renders_with_tag() -> None:
    display = _compose_display(
        char_art="X",
        above_lines=[],
        plant_lines=[],
        progress_line="",
        status_line="",
        achievement_line="",
        inner_w=40,
        sysinfo_line="Disk: 100.0/500.0 GB  |  RAM: 8.0/16.0 GB",
    )
    text = display.text
    assert "System" in text
    assert "Disk:" in text
    lines = text.split("\n")
    sysinfo_idx = next(i for i, l in enumerate(lines) if "System" in l)
    sysinfo_row = display.regions[sysinfo_idx]
    assert "sysinfo" in sysinfo_row

