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
    # Weather panel must appear after ground (sand row with ·. pattern)
    ground_idx = max(i for i, ln in enumerate(lines) if "·" in ln and "." in ln and "Weather" not in ln)
    weather_idx = next(i for i, ln in enumerate(lines) if "Weather" in ln)
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


def test_sysinfo_panel_renders_with_lines() -> None:
    display = _compose_display(
        char_art="X",
        above_lines=[],
        plant_lines=[],
        progress_line="",
        status_line="",
        achievement_line="",
        inner_w=40,
        sysinfo_lines=["Disk: 100.0/500.0 GB", "RAM: 8.0/16.0 GB"],
    )
    text = display.text
    assert "System" in text
    assert "Disk:" in text
    assert "RAM:" in text
    lines = text.split("\n")
    sysinfo_idx = next(i for i, ln in enumerate(lines) if "System" in ln)
    sysinfo_row = display.regions[sysinfo_idx]
    assert "sysinfo" in sysinfo_row


def test_water_surface_row_has_water_tag() -> None:
    display = _compose_display(
        char_art="X",
        above_lines=[],
        plant_lines=[],
        progress_line="",
        status_line="",
        achievement_line="",
        inner_w=30,
    )
    # Row 0 is now the water surface (no top border)
    assert "water" in display.regions[0]


def test_ground_uses_sand_tag() -> None:
    display = _compose_display(
        char_art="X",
        above_lines=[],
        plant_lines=[],
        progress_line="",
        status_line="",
        achievement_line="",
        inner_w=30,
    )
    text = display.text
    lines = text.split("\n")
    # Find the single sand row by its ·. pattern (no box-drawing corners)
    sand_idx = next(i for i, ln in enumerate(lines) if "·" in ln and "." in ln and ln.strip().replace("·", "").replace(".", "") == "")
    assert all(t == "sand" for t in display.regions[sand_idx])


def test_top_row_is_water_surface() -> None:
    display = _compose_display(
        char_art="X",
        above_lines=[],
        plant_lines=[],
        progress_line="",
        status_line="",
        achievement_line="",
        inner_w=30,
    )
    lines = display.text.split("\n")
    # Row 0 is water surface with `. ·` pattern
    assert "." in lines[0] or "\u00b7" in lines[0]


def test_pomodoro_panel_appears_when_provided() -> None:
    display = _compose_display(
        char_art="X",
        above_lines=[],
        plant_lines=[],
        progress_line="",
        status_line="",
        achievement_line="",
        inner_w=40,
        pomodoro_panel_lines=["\U0001f345 Work: 12:34"],
    )
    assert "Pomodoro" in display.text
    lines = display.text.split("\n")
    pom_idx = next(i for i, ln in enumerate(lines) if "Pomodoro" in ln)
    assert "pomodoro" in display.regions[pom_idx]


def test_pomodoro_panel_absent_when_none() -> None:
    display = _compose_display(
        char_art="X",
        above_lines=[],
        plant_lines=[],
        progress_line="",
        status_line="",
        achievement_line="",
        inner_w=40,
        pomodoro_panel_lines=None,
    )
    assert "Pomodoro" not in display.text


def test_goal_line_renders_when_provided() -> None:
    display = _compose_display(
        char_art="X",
        above_lines=[],
        plant_lines=[],
        progress_line="",
        status_line="",
        achievement_line="",
        inner_w=40,
        goal_line="\u2022 goal: 10m/120m",
    )
    assert "goal:" in display.text
    lines = display.text.split("\n")
    goal_idx = next(i for i, ln in enumerate(lines) if "goal:" in ln)
    assert "goal" in display.regions[goal_idx]


def test_streak_line_renders_when_provided() -> None:
    display = _compose_display(
        char_art="X",
        above_lines=[],
        plant_lines=[],
        progress_line="",
        status_line="",
        achievement_line="",
        inner_w=40,
        streak_line="\u00b7 7 days",
    )
    assert "7 days" in display.text
    lines = display.text.split("\n")
    streak_idx = next(i for i, ln in enumerate(lines) if "7 days" in ln)
    assert "streak" in display.regions[streak_idx]
