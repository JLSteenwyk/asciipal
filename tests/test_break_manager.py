from __future__ import annotations

from asciipal.activity_tracker import ActivitySnapshot
from asciipal.break_manager import BreakManager
from asciipal.config import Config, DEFAULT_CONFIG


def _config() -> Config:
    return Config.from_dict(dict(DEFAULT_CONFIG))


def _active_snapshot() -> ActivitySnapshot:
    return ActivitySnapshot(
        typing_wpm=40,
        click_rate=1,
        mouse_speed=20,
        seconds_since_input=0.5,
        total_active_seconds=100,
    )


def test_break_escalates_after_interval() -> None:
    cfg = _config()
    manager = BreakManager(cfg)
    manager._active_start = 0
    snap = _active_snapshot()

    due = cfg.break_interval_minutes * 60 + 30
    status = manager.update(snap, now=due)
    assert status.should_break is True
    assert status.stage == "suggestion"

    status = manager.update(snap, now=due + 3 * 60)
    assert status.stage == "insistence"

    status = manager.update(snap, now=due + 6 * 60)
    assert status.stage == "tantrum"


def test_break_starts_when_overdue_and_user_idle() -> None:
    cfg = _config()
    manager = BreakManager(cfg)
    manager._active_start = 0
    idle_snap = ActivitySnapshot(
        typing_wpm=0,
        click_rate=0,
        mouse_speed=0,
        seconds_since_input=cfg.idle_timeout_seconds + 1,
        total_active_seconds=100,
    )

    due = cfg.break_interval_minutes * 60 + 10
    status = manager.update(idle_snap, now=due)
    assert status.stage == "on_break"
    assert status.should_break is False
    assert status.break_seconds_remaining == cfg.break_duration_minutes * 60


def test_pomodoro_uses_pomodoro_timers() -> None:
    cfg_data = dict(DEFAULT_CONFIG)
    cfg_data["pomodoro_mode"] = True
    cfg_data["pomodoro_work_minutes"] = 1
    cfg_data["pomodoro_break_minutes"] = 2
    cfg = Config.from_dict(cfg_data)
    manager = BreakManager(cfg)
    manager._active_start = 0
    idle_snap = ActivitySnapshot(
        typing_wpm=0,
        click_rate=0,
        mouse_speed=0,
        seconds_since_input=cfg.idle_timeout_seconds + 1,
        total_active_seconds=100,
    )
    status = manager.update(idle_snap, now=61)
    assert status.stage == "on_break"
    assert status.break_seconds_remaining == 120


def test_break_completion_increments_stats() -> None:
    cfg = _config()
    manager = BreakManager(cfg)
    manager.start_break(now=0)
    snap = ActivitySnapshot(
        typing_wpm=0,
        click_rate=0,
        mouse_speed=0,
        seconds_since_input=cfg.idle_timeout_seconds + 1,
        total_active_seconds=100,
    )
    status = manager.update(snap, now=cfg.break_duration_minutes * 60 + 1)
    assert status.stage == "none"
    assert manager.breaks_taken == 1
